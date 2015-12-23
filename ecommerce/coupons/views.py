import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from oscar.core.loading import get_class, get_model
from rest_framework import status
from rest_framework.response import Response

from edx_rest_api_client.client import EdxRestApiClient
from edx_rest_api_client.exceptions import SlumberHttpBaseException

from ecommerce.core.views import StaffOnlyMixin
from ecommerce.extensions.api import data as data_api
from ecommerce.extensions.api.constants import APIConstants as AC
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.fulfillment.status import ORDER
from ecommerce.settings import get_lms_url


Applicator = get_class('offer.utils', 'Applicator')
Basket = get_model('basket', 'Basket')
logger = logging.getLogger(__name__)
Selector = get_class('partner.strategy', 'Selector')
StockRecord = get_model('partner', 'StockRecord')
Voucher = get_model('voucher', 'Voucher')


def get_voucher(code):
    """
    Returns a voucher and prodcut for a given code.

    Arguments:
        code (str): The code of a coupon voucher

    Returns:
        voucher (Voucher): The Voucher for the passed code
        product (Product): The Product associated with the Voucher
    """
    voucher = None
    product = None
    # Check to see if a voucher exists for the code.
    try:
        voucher = Voucher.objects.get(code=code)
    except Voucher.DoesNotExist:
        logger.exception('Voucher does not exist for code [%s]', code)
        return voucher, product

    if voucher:
        # Just get the first product.
        products = voucher.offers.all()[0].condition.range.all_products()
        if products:
            product = products[0]
    return voucher, product


class CouponAppView(StaffOnlyMixin, TemplateView):
    template_name = 'coupons/coupon_app.html'


class CouponOfferView(TemplateView):
    template_name = 'coupons/coupon_redemption.html'

    def get(self, request):
        """
        View to lookup the course for a given code.

        Arguments:
            code (str): The code of a coupon voucher

        Returns:
            406 Code not valid: no code parameter was sent, there isn't a voucher
                    with that specific code or the voucher is no longer active.
                Voucher is not available to the logged in user.
            500 Could not get course information

        """
        code = request.GET.get('code', None)

        if code is not None:
            voucher, product = get_voucher(code=code)
            if voucher is None or voucher.is_active() is False:
                Response({'message': 'Code not valid'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            Response({'message': 'Code not valid'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        avail, msg = voucher.is_available_to_user(request.user)
        if not avail:
            return Response({'message': msg}, status=status.HTTP_406_NOT_ACCEPTABLE)

        api = EdxRestApiClient(get_lms_url('api/courses/v1/'))
        try:
            course = api.courses(product.course_id).get()
        except SlumberHttpBaseException as e:
            logger.error('Could not get course information')
            return Response({'message': e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        course['image_url'] = get_lms_url(course['media']['course_image']['uri'])
        stock_records = voucher.offers.first().condition.range.catalog.stock_records.all()
        data = {
            'course': course,
            'code': code,
            'price': stock_records[0].price_excl_tax
        }
        return render(request, self.template_name, data)


class CouponRedeemView(EdxOrderPlacementMixin, TemplateView):

    @method_decorator(login_required)
    def get(self, request):
        """
        Looks up the passed code and adds the matching product to a basket,
        then applies the voucher and if the basket total is FREE places the order and
        enrolls the user in the course.

        Arguments:
            code (str): The code of a coupon voucher

        Returns:
            404 the voucher with the supplied code does not exist
            406 Code expired: voucher is no longer active
                Product not available for purchase
            500 order didn't complete
        """
        code = request.GET.get('code', None)
        if code is not None:
            voucher, product = get_voucher(code=code)
            if voucher is None:
                return Response({'message': 'Code does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if not voucher.is_active():
            return Response({'message': 'Code expired'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        purchase_info = request.strategy.fetch_for_product(product)
        if not purchase_info.availability.is_available_to_buy:
            return Response(
                {'message': 'Product [{}] not available for purchase.'.format(product)},
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        basket = self._prepare_basket(request.site, request.user, product, voucher)

        if basket.total_excl_tax == AC.FREE:
            basket.freeze()
            order_metadata = data_api.get_order_metadata(basket)

            logger.info(
                u"Preparing to place order [%s] for the contents of basket [%d]",
                order_metadata[AC.KEYS.ORDER_NUMBER],
                basket.id,
            )

            # Place an order. If order placement succeeds, the order is committed
            # to the database so that it can be fulfilled asynchronously.
            order = self.handle_order_placement(
                order_number=order_metadata[AC.KEYS.ORDER_NUMBER],
                user=basket.owner,
                basket=basket,
                shipping_address=None,
                shipping_method=order_metadata[AC.KEYS.SHIPPING_METHOD],
                shipping_charge=order_metadata[AC.KEYS.SHIPPING_CHARGE],
                billing_address=None,
                order_total=order_metadata[AC.KEYS.ORDER_TOTAL],
            )
        else:
            return Response(
                {'message': 'Basket total not $0, current value = ${}'.format(basket.total_excl_tax)},
                status.HTTP_406_NOT_ACCEPTABLE
            )

        if order.status is ORDER.COMPLETE:
            return HttpResponseRedirect(get_lms_url(''))
        else:
            logger.error('Order was not completed [%s]', order.id)
            return Response(
                {'message': 'Error when trying to redeem code'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _prepare_basket(self, site, user, product, voucher):
        """
        Prepare the basket, add the product, and apply a voucher.

        Existing baskets are merged and flushed. The specified product will
        be added to the remaining open basket, and the basket will be frozen.
        The Voucher is applied to the basket and checked for discounts.

        Arguments:
            site (Site): The site from which the request came.
            user (User): User who made the request.
            product (Product): Product to be added to the basket.
            voucher (Voucher): Voucher to apply to the basket.

        Returns:
            basket (Basket): Contains the product to be redeemed and the Voucher applied
        """
        basket = Basket.get_basket(user, site)
        basket.thaw()
        # remove all existing vouchers from the basket
        for vouchers in basket.vouchers.all():
            logger.info('removing voucher [%s]', vouchers.code)
            basket.vouchers.remove(vouchers)
        basket.reset_offer_applications()
        basket.flush()
        basket.add_product(product, 1)
        basket.vouchers.add(voucher)
        Applicator().apply(basket, user, self.request)
        discounts = basket.offer_applications
        # Look for discounts from this new voucher
        for discount in discounts:
            if discount['voucher'] and discount['voucher'] == voucher:
                logger.info('Applied Voucher [%s] to basket', voucher.code)
                break
            else:
                logger.info('Voucher [%s] not valid', voucher.code)
                basket.vouchers.remove(voucher)

        return basket
