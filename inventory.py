#This file is part stock_kit module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import PoolMeta
import copy

__all__ = ['InventoryLine']
__metaclass__ = PoolMeta
DEPENDS = ['stock_depends_on_kit_components']


class InventoryLine:
    __name__ = 'stock.inventory.line'

    @classmethod
    def __setup__(cls):
        super(InventoryLine, cls).__setup__()
        cls.product = copy.copy(cls.product)
        cls.product.depends = copy.copy(cls.product.depends) + DEPENDS
        cls.product.domain = copy.copy(cls.product.domain) + [[
                'OR',
                ('kit', '=', False),
                ('stock_depends_on_kit_components', '=', False),
                ]]
        #~ cls._reset_columns() #TODO
