# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from oscar.core.loading import get_model

ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")


def add_coupon_category(apps, schema_editor):
    """Create and assign 'coupon_category' attribute to coupons."""
    coupon = ProductClass.objects.get(name='Coupon')
    ProductAttribute.objects.create(
        product_class=coupon,
        name='Coupon category',
        code='coupon_category',
        type='text',
        required=True
    )


def remove_coupon_category(apps, schema_editor):
    """Remove 'coupon_category attribute'."""
    ProductAttribute.objects.filter(code='coupon_category').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        ('catalogue', '0014_alter_couponvouchers_attribute')
    ]
    operations = [
        migrations.RunPython(add_coupon_category, remove_coupon_category)
    ]
