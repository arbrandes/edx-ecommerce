from oscar.test import factories
from ecommerce.invoice.models import Invoice
from ecommerce.tests.testcases import TestCase


class InvoiceTests(TestCase):
    """Test to ensure Invoice objects are created correctly"""
    def setUp(self):
        super(InvoiceTests, self).setUp()
        self.basket = factories.create_basket(empty=True)
        self.basket.owner = factories.UserFactory()
        self.basket.order = factories.OrderFactory()
        self.basket.save()
        self.invoice = Invoice.objects.create(basket=self.basket, state='Paid')

    def test_string(self):
        """Test to check to Invoice string matches what is expected"""
        self.assertEqual(str(self.invoice), 'Invoice {id} for order number {order}'.format(
            id=self.invoice.id, order=self.basket.order.number))

    def test_order(self):
        """Test to check invoice order"""
        self.assertEqual(self.basket.order, self.invoice.basket.order)

    def test_client(self):
        """Test to check invoice client"""
        self.assertEqual(self.basket.order.user, self.invoice.client)

    def test_total(self):
        """Test to check invoice total"""
        self.assertEqual(self.basket.order.total_incl_tax, self.invoice.total)
