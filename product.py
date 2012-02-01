#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Bool
import math

STATES = {
    'readonly': Bool(~Eval('kit')),
}

DEPENDS = ['kit']

class Product(ModelSQL, ModelView):
    _name = "product.product"

    explode_kit_in_shipments = fields.Boolean('Explode in Shipments', 
            states=STATES, depends=DEPENDS)
    stock_depends_on_kit_components = fields.Boolean('Stock Depends on '
            'Components', states=STATES, depends=DEPENDS,
            help='Indicates weather the stock of the current kit should'
                  ' depend on its components or not.' )

    def default_explode_kit_in_shipments(self):
        return True

    def default_stock_depends_on_kit_components(self):
        return False
        
    def get_quantity(self, ids, name):        
        res = super(Product, self).get_quantity(ids, name )                
        #Calculate stock for kits that stock depens on subproducts
        for product in self.browse(ids):
            
            if not product.stock_depends_on_kit_components or \
                not product.kit_lines:
                continue
            res[product.id] = 0.0
            subproducts_ids = [x.product.id for x in product.kit_lines]
            subproducts_stock = super(Product, self).get_quantity(
                subproducts_ids, name)
            pack_stock = False
                
            for subproduct in product.kit_lines:
                sub_qty = subproduct.quantity
                sub_stock = subproducts_stock.get(subproduct.product.id, 0)
                if not pack_stock:
                    pack_stock = math.floor(sub_stock / sub_qty)
                else:
                    pack_stock = min(pack_stock,
                                     math.floor(sub_stock / sub_qty))
            res[product.id] = pack_stock
                
        return res

Product()
