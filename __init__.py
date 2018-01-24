# This file is part stock_kit module for Tryton.  The COPYRIGHT file at the top
# level of this repository contains the full copyright notices and license
# terms.
from trytond.pool import Pool
from . import product
from . import inventory


def register():
    Pool.register(
        product.Template,
        product.Product,
        inventory.InventoryLine,
        module='stock_kit', type_='model')
