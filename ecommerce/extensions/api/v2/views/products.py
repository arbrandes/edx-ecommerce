"""HTTP endpoints for interacting with products."""
from oscar.core.loading import get_model
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_extensions.mixins import NestedViewSetMixin

from ecommerce.extensions.api import serializers
from ecommerce.extensions.api.v2.views import NonDestroyableModelViewSet


Product = get_model('catalogue', 'Product')


class ProductViewSet(NestedViewSetMixin, NonDestroyableModelViewSet):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer
    permission_classes = (IsAuthenticated, IsAdminUser,)

    def get_queryset(self):
        queryset = Product.objects.all()
        product_class_filter = self.request.query_params.get('product_class', None)
        if product_class_filter:
            queryset = Product.objects.filter(product_class__slug=product_class_filter.lower())
        return queryset
