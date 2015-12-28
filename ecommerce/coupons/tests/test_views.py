import httpretty
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from oscar.core.loading import get_model
from oscar.test.factories import ConditionalOfferFactory, VoucherFactory

from ecommerce.coupons.views import get_voucher
from ecommerce.tests.testcases import TestCase


class CouponAppViewTests(TestCase):
    path = reverse('coupons:app', args=[''])

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
        test_voucher = VoucherFactory(code='COUPONTEST')
        offer = ConditionalOfferFactory()
        test_voucher.offers.add(offer)
        test_voucher.save()

        voucher, product = get_voucher(code='COUPONTEST')
        self.assertIsNotNone(voucher)
        self.assertIsNotNone(product)
