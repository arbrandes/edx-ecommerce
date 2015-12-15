import logging

from django.views.generic import TemplateView, View
from ecommerce.core.views import StaffOnlyMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import render
from django.utils.decorators import method_decorator

from edx_rest_api_client.client import EdxRestApiClient
from edx_rest_api_client.exceptions import SlumberHttpBaseException

from oscar.core.loading import get_class, get_model

from ecommerce.extensions.api import data as data_api
from ecommerce.extensions.api.constants import APIConstants as AC
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.partner.shortcuts import get_partner_for_site
from ecommerce.settings import get_lms_url


Applicator = get_class('offer.utils', 'Applicator')
Basket = get_model('basket', 'Basket')
logger = logging.getLogger(__name__)
Selector = get_class('partner.strategy', 'Selector')
StockRecord = get_model('partner', 'StockRecord')
Voucher = get_model('voucher', 'Voucher')


class VoucherMixin(object):
    def get_voucher(self, code):
        """
        Returns a voucher and prodcut for a given code
        Arguments:
            code: The coupon code for a voucher

        Returns:
            voucher: The Voucher for the passed code
            product: The Product associated with the Voucher
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


class CouponOfferView(View, VoucherMixin):
    template_name = 'coupons/coupon_redemption.html'

    def get(self, request):
        """
        View to lookup the course for a given code.

        Arguments:
            code: The code associated with a course

        Returns:

        """
        partner = get_partner_for_site(request)
        if not partner:
            return HttpResponseServerError('No Partner is associated with this site.')

        code = request.GET.get('code', None)
        api = EdxRestApiClient(get_lms_url('api/courses/v1/'))

        if code is not None:
            voucher, product = self.get_voucher(code=code)
            if voucher is None or voucher.is_active() is False:
                return HttpResponseBadRequest('Code not valid')
        else:
            return HttpResponseBadRequest('Code not valid')

        try:
            course = api.courses(product.course_id).get()
        except SlumberHttpBaseException as e:
            # TODO: handle error
            return HttpResponseBadRequest('Error [%s]', e)

        course['image_url'] = get_lms_url(course['media']['course_image']['uri'])
        data = {
            'course': course,
            'code': code,
        }
        return render(request, self.template_name, data)


class CouponRedeemView(View, VoucherMixin, EdxOrderPlacementMixin):

    @method_decorator(login_required)
    def get(self, request):
        """
        Looks up the passed code and adds the matching product to a basket,
        then applies the voucher and if the basket total is FREE places the order and
        enrolls the user in the course.

        Arguments:
            code:
        Returns:
        """
        code = request.GET.get('code', None)
        if code is not None:
            voucher, product = self.get_voucher(code=code)
            if voucher is None:
                return HttpResponseBadRequest('Code does not exist')

        if voucher.is_active() is False:
            return HttpResponseBadRequest('Code no longer valid')

        purchase_info = request.strategy.fetch_for_product(product)
        if not purchase_info.availability.is_available_to_buy:
            return HttpResponseBadRequest('Product [{}] does not exist.'.format(product))

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
            return HttpResponseBadRequest('Basket total not $0, current value = ${}'.format(basket.total_excl_tax))

        if order.status is 'Complete':
            return HttpResponseRedirect(get_lms_url(''))
        else:
            logger.error('Order was not completed [%s]', order.id)
            return HttpResponseBadRequest('Error when trying to redeem code')

    def _prepare_basket(self, site, user, product, voucher):
        """
        Prepare the basket, add the product, and apply a voucher.

        Existing baskets are merged and flushed. The specified product will be added to the remaining open basket,
        and the basket will be frozen.
        The Voucher is applied to the basket and checked for discounts.

        Arguments:
            product: Product to be added to the basket.
            voucher: Voucher to apply to the basket.

        Returns:
            basket: Contains the product to be redeemed and the Voucher applied
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
