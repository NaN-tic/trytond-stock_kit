# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import math

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Bool
from trytond.i18n import gettext
from trytond.model.exceptions import ValidationError
from trytond.transaction import Transaction

__all__ = ['Template', 'Product']

STATES = {
    'invisible': Bool(~Eval('kit')),
    }


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    @classmethod
    def validate(cls, templates):
        Product = Pool().get('product.product')
        Product.ensure_kit_consumable([
                p for t in templates for p in t.products])
        super(Template, cls).validate(templates)
        for template in templates:
            template.check_type_and_products_stock_depends()

    def check_type_and_products_stock_depends(self):
        if not (self.consumable or self.type == 'service'):
            for product in self.products:
                product.check_stock_depends_and_product_type()


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'
    stock_depends_on_kit_components = fields.Boolean('Stock Depends on '
            'Components', states=STATES,
            help='Indicates weather the stock of the current kit should'
                  ' depend on its components or not.')

    @classmethod
    def __register__(cls, module_name):
        super().__register__(module_name)
        template = Pool().get('product.template').__table__()
        product = cls.__table__()
        cursor = Transaction().connection.cursor()
        cursor.execute(*template.update(
                [template.type, template.consumable], ['goods', True],
                where=template.id.in_(product.select(product.template,
                        where=product.kit
                        & product.stock_depends_on_kit_components))
                & ((template.type != 'goods') | ~template.consumable)))

    @staticmethod
    def default_stock_depends_on_kit_components():
        return False

    @classmethod
    def get_quantity(cls, products, name):
        quantities = super(Product, cls).get_quantity(products, name)

        def get_quantity_kit(product, quantities):
            pack_stock = None
            for subproduct in product.kit_lines:
                if subproduct.product.type != 'goods':
                    continue
                sub_qty = subproduct.quantity
                if subproduct.product.id not in quantities:
                    quantities[subproduct.product.id] = cls.get_quantity(
                        [subproduct.product], name)[subproduct.product.id]
                sub_stock = quantities.get(subproduct.product.id, 0)
                if pack_stock is None:
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
        cls.ensure_kit_consumable(products)
        super(Product, cls).validate(products)
        for product in products:
            product.check_stock_depends_and_product_type()

    @classmethod
    def ensure_kit_consumable(cls, products):
        Template = Pool().get('product.template')
        templates = {p.template for p in products
            if p.kit and p.stock_depends_on_kit_components
            and (p.type != 'goods' or not p.consumable)}
        if templates:
            Template.write(list(templates), {
                    'type': 'goods', 'consumable': True})

    @fields.depends('kit', 'stock_depends_on_kit_components', 'template',
        '_parent_template.type', '_parent_template.consumable')
    def on_change_stock_depends_on_kit_components(self):
        if self.kit and self.stock_depends_on_kit_components and self.template:
            self.template.type = 'goods'
            self.template.consumable = True

    def check_stock_depends_and_product_type(self):
        if (self.stock_depends_on_kit_components and
                not (self.consumable or self.type == 'service')):
            raise ValidationError(gettext(
                'stock_kit.invalid_stock_depends_and_type',
                product=self.rec_name))
