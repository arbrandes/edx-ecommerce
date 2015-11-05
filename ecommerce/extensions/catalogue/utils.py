from __future__ import unicode_literals

from hashlib import md5

from oscar.core.loading import get_model

Catalog = get_model('catalogue', 'Catalog')
StockRecord = get_model('partner', 'StockRecord')


def generate_sku(product, partner, **kwargs):
    """
    Generates a SKU for the given partner and and product combination.

    Example: 76E4E71
    """
    # Note: This currently supports coupons and seats.
    # A new product type can be added via a new else if block.
    if product.product_class and product.product_class.name == 'Coupon':
        _hash = ' '.join((
            unicode(product.id),
            unicode(kwargs.get('catalog', '')),
            str(partner.id)
        ))
    else:
        # Seats
        _hash = ' '.join((
            getattr(product.attr, 'certificate_type', ''),
            product.attr.course_key,
            unicode(product.attr.id_verification_required),
            getattr(product.attr, 'credit_provider', ''),
            str(partner.id)
        ))

    _hash = md5(_hash.lower())
    _hash = _hash.hexdigest()[-7:]

    return _hash.upper()


def get_or_create_catalog(name, partner, stock_record_ids):
    """
    Returns the catalog which has the same name, partner and stock records.
    If there isn't one with that data, creates and returns a new one.
    """
    catalogs = Catalog.objects.all()
    stock_records = [StockRecord.objects.get(id=id) for id in stock_record_ids]  # pylint: disable=redefined-builtin

    for catalog in catalogs:
        if catalog.name == name and catalog.partner == partner:
            if set(catalog.stock_records.all()) == set(stock_records):
                return catalog

    catalog = Catalog.objects.create(name=name, partner=partner)
    for stock_record in stock_records:
        catalog.stock_records.add(stock_record)
    return catalog


def generate_upc(partner, title, catalog):
    """
    Generates a unique UPC value for a coupon from the
    catalog and partner. Used to differentiate products.
    """
    _hash = ' '.join((
        unicode(title),
        unicode(catalog.name),
        str(partner.id)
    ))
    _hash = md5(_hash.lower())
    _hash = _hash.hexdigest()[-10:]

    return _hash.upper()
