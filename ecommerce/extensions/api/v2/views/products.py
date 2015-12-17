"""HTTP endpoints for interacting with products."""
from oscar.core.loading import get_model
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_extensions.mixins import NestedViewSetMixin

from ecommerce.extensions.api import serializers
from ecommerce.extensions.api.v2.views import NonDestroyableModelViewSet


Product = get_model('catalogue', 'Product')


class ProductViewSet(NestedViewSetMixin, NonDestroyableModelViewSet):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer
    # URL with filter example:
    # /api/v2/products/?product_class__name=Coupon
    # Note, it's case-sensitive
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('product_class__name',)
    permission_classes = (IsAuthenticated, IsAdminUser,)
