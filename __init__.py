#This file is part stock_kit module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import Pool
from .product import *
from .shipment import *
from .move import *
from .inventory import *


def register():
    Pool.register(
        Product,
        ShipmentIn,
        ShipmentOut,
        Move,
        InventoryLine,
        module='stock_kit', type_='model')
    Pool.register(
        CreateShipmentOutReturn,
        module='stock_kit', type_='wizard')
