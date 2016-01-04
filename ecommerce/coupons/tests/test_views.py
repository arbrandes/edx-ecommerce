import datetime
import httpretty
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_class, get_model
from oscar.test.factories import OrderFactory, ConditionalOfferFactory, BasketFactory, VoucherFactory, RangeFactory, BenefitFactory, ProductFactory

from ecommerce.coupons.views import get_voucher
from ecommerce.tests.testcases import TestCase

Applicator = get_class('offer.utils', 'Applicator')
Voucher = get_model('voucher', 'Voucher')
VoucherApplication = get_model('voucher', 'VoucherApplication')


class CouponAppViewTests(TestCase):
    path = reverse('coupons:app', args=[''])
    offer_url = reverse('coupons:offer')

    def setUp(self):
        super(CouponAppViewTests, self).setUp()

    def prepare_voucher(self, start_datetime=None):
        test_product = ProductFactory(title='Test product')
        test_product.attr.course = 'edX/DemoX/Demo_Course'
        test_product.save()

        if start_datetime is None:
            start_datetime = now() - datetime.timedelta(days=1)
        test_voucher = VoucherFactory(code='COUPONTEST', start_datetime=start_datetime, usage=Voucher.SINGLE_USE)

        range = RangeFactory(products=[test_product, ])
        benefit = BenefitFactory(range=range)
        offer = ConditionalOfferFactory(benefit=benefit)
        test_voucher.offers.add(offer)
        return test_voucher, test_product

    def test_login_required(self):
        """ Users are required to login before accessing the view. """
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL, response.url)

    def test_staff_user_required(self):
        """ Verify the view is only accessible to staff users. """
        user = self.create_user(is_staff=False)
        self.client.login(username=user.username, password=self.password)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 404)

        user = self.create_user(is_staff=True)
        self.client.login(username=user.username, password=self.password)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

    def test_get_voucher(self):
        """ Verify that get_voucher() returns product and voucher. """
        self.prepare_voucher()
        voucher, product = get_voucher(code='COUPONTEST')
        self.assertIsNotNone(voucher)
        self.assertEqual(voucher.code, 'COUPONTEST')
        self.assertIsNotNone(product)
        self.assertEqual(product.title, 'Test product')

    def test_no_code(self):
        self.prepare_voucher()
        response = self.client.get(self.offer_url)
        # TODO: execute the translation and evaluate
        self.assertEqual(response.context['error'], _('Code not valid.'))

    def test_invalid_code(self):
        self.prepare_voucher()
        url = self.offer_url + '?code={}'.format('INVALIDCODE')
        response = self.client.get(url)
        # TODO: execute the translation and evaluate
        self.assertEqual(response.context['error'], _('Code not valid.'))

    def test_voucher_is_not_active(self):
        future = now() + datetime.timedelta(days=10)
        self.prepare_voucher(start_datetime=future)
        url = self.offer_url + '?code={}'.format('COUPONTEST')
        response = self.client.get(url)
        # TODO: execute the translation and evaluate
        self.assertEqual(response.context['error'], _('Code not valid.'))

    def test_voucher_not_available(self):
        voucher, product = self.prepare_voucher()
        basket = BasketFactory()
        basket.add_product(product, 1)
        basket.vouchers.add(voucher)

        Applicator().apply(basket)
        order = OrderFactory()
        user = self.create_user()
        VoucherApplication.objects.create(voucher=voucher, user=user, order=order)

        url = self.offer_url + '?code={}'.format('COUPONTEST')
        response = self.client.get(url)
        # TODO: execute the translation and evaluate
        self.assertEqual(response.context['error'], _('Code not valid.'))

    def test_course_information_error(self):
        pass

    def test_proper_code(self):
        pass
