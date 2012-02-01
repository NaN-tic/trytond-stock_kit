#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields, OPERATORS
from trytond.backend import TableHandler
from trytond.pyson import In, Eval, Not, Equal, If, Get, Bool
from trytond.transaction import Transaction
from trytond.pool import Pool
import copy

DEPENDS = ['stock_depends_on_kit_components']

class InventoryLine(ModelSQL, ModelView):
    _name = 'stock.inventory.line'


    def __init__(self):
        super(InventoryLine,self).__init__()
        self.product = copy.copy(self.product)
        self.product.depends = copy.copy(self.product.depends) + DEPENDS
        self.product.domain = copy.copy(self.product.domain) + [ [
            'OR', 
                ('kit','=',False),
                ('stock_depends_on_kit_components','=',False)                
            ]
                                                                 ]
        
        self._reset_columns()

InventoryLine()

