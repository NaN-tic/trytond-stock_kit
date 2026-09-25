# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import math

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval
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
    kit_available_quantity = fields.Function(fields.Float(
            'Available Kit Quantity', digits='default_uom',
            states={
                'invisible': ~(Bool(Eval('kit'))
                    & Bool(Eval('stock_depends_on_kit_components'))),
                },
            help='The number of kits that can be assembled from the current '
                'stock of their components.'),
        'get_kit_available_quantity')

    @staticmethod
    def default_stock_depends_on_kit_components():
        return False

    @classmethod
    def get_kit_available_quantity(cls, products, name):
        if not Transaction().context.get('locations'):
            Location = Pool().get('stock.location')
            warehouses = Location.search([('type', '=', 'warehouse')])
            result = {product.id: None for product in products}
            for warehouse in warehouses:
                with Transaction().set_context(locations=[warehouse.id]):
                    quantities = cls.get_kit_available_quantity(products, name)
                for product in products:
                    quantity = quantities[product.id]
                    if quantity is not None:
                        result[product.id] = (
                            (result[product.id] or 0.0) + quantity)
            return result

        component_products = {}

        def add_components(product):
            for line in product.kit_lines:
                component = line.product
                if component.type != 'goods':
                    continue
                if component.id in component_products:
                    continue
                component_products[component.id] = component
                if (component.stock_depends_on_kit_components
                        and component.kit_lines):
                    add_components(component)

        for product in products:
            if (product.stock_depends_on_kit_components
                    and product.kit_lines):
                add_components(product)

        quantities = super(Product, cls).get_quantity(
            list(component_products.values()), 'quantity')
        kit_quantities = {}

        def get_quantity_kit(product):
            if product.id in kit_quantities:
                return kit_quantities[product.id]
            pack_stock = None
            for subproduct in product.kit_lines:
                if subproduct.product.type != 'goods':
                    continue
                sub_qty = subproduct.quantity
                if (subproduct.product.stock_depends_on_kit_components
                        and subproduct.product.kit_lines):
                    sub_stock = get_quantity_kit(subproduct.product)
                else:
                    sub_stock = quantities.get(subproduct.product.id, 0)
                if pack_stock is None:
                    pack_stock = math.floor(sub_stock / sub_qty)
                else:
                    pack_stock = min(pack_stock,
                                     math.floor(sub_stock / sub_qty))
            kit_quantities[product.id] = pack_stock if pack_stock else 0.0
            return kit_quantities[product.id]

        result = {product.id: None for product in products}
        for product in products:
            if (product.stock_depends_on_kit_components
                    and product.kit_lines):
                result[product.id] = get_quantity_kit(product)
        return result

    @classmethod
    def validate(cls, products):
        super(Product, cls).validate(products)
        for product in products:
            product.check_stock_depends_and_product_type()

    def check_stock_depends_and_product_type(self):
        if (self.stock_depends_on_kit_components and
                not (self.consumable or self.type == 'service')):
            raise ValidationError(gettext(
                'stock_kit.invalid_stock_depends_and_type',
                product=self.rec_name))
