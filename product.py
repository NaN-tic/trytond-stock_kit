# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import math

from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Bool


__all__ = ['Template', 'Product']

STATES = {
    'invisible': Bool(~Eval('kit')),
    }
DEPENDS = ['kit']


class Template:
    __metaclass__ = PoolMeta
    __name__ = 'product.template'

    @classmethod
    def validate(cls, templates):
        super(Template, cls).validate(templates)
        for template in templates:
            template.check_type_and_products_stock_depends()

    def check_type_and_products_stock_depends(self):
        if not (self.consumable or self.type == 'service'):
            for product in self.products:
                product.check_stock_depends_and_product_type()


class Product:
    __metaclass__ = PoolMeta
    __name__ = 'product.product'
    stock_depends_on_kit_components = fields.Boolean('Stock Depends on '
            'Components', states=STATES, depends=DEPENDS,
            help='Indicates weather the stock of the current kit should'
                  ' depend on its components or not.')

    @classmethod
    def __setup__(cls):
        super(Product, cls).__setup__()
        cls._error_messages.update({
                'invalid_stock_depends_and_type': ('The product "%s" is '
                    'configured as a Kit with "Stock Depends on Components", '
                    'but its template is not a Service or Consumable.'),
                })

    @staticmethod
    def default_stock_depends_on_kit_components():
        return False

    @classmethod
    def get_quantity(cls, products, name):
        quantities = super(Product, cls).get_quantity(products, name)

        def get_quantity_kit(product, quantities):
            pack_stock = False
            for subproduct in product.kit_lines:
                sub_qty = subproduct.quantity
                if subproduct.product.id not in quantities:
                    quantities[subproduct.product.id] = cls.get_quantity(
                        [subproduct.product], name)[subproduct.product.id]
                sub_stock = quantities.get(subproduct.product.id, 0)
                if not pack_stock:
                    pack_stock = math.floor(sub_stock / sub_qty)
                else:
                    pack_stock = min(pack_stock,
                                     math.floor(sub_stock / sub_qty))
            return pack_stock if pack_stock else 0.0

        products = products[:]
        while products:
            product = products.pop(0)
            if (product.kit_lines and
                    any([kl.product in products for kl in product.kit_lines])):
                products.append(product)
                continue
            if product.stock_depends_on_kit_components and product.kit_lines:
                quantities[product.id] = get_quantity_kit(product, quantities)
        return quantities

    @classmethod
    def validate(cls, products):
        super(Product, cls).validate(products)
        for product in products:
            product.check_stock_depends_and_product_type()

    def check_stock_depends_and_product_type(self):
        if (self.stock_depends_on_kit_components and
                not (self.consumable or self.type == 'service')):
            self.raise_user_error('invalid_stock_depends_and_type',
                (self.rec_name,))
