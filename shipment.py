#This file is part stock_kit module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import ModelView, Workflow
from trytond.transaction import Transaction
from trytond.pool import PoolMeta

__all__ = ['ShipmentIn', 'ShipmentOut']
__metaclass__ = PoolMeta


class ShipmentIn:
    __name__ = 'stock.shipment.in'

    def create_inventory_moves(self, shipments):
        """ ensure no explode kits again on inventory moves """
        context = Transaction().context.copy()
        context['explode_kit'] = False
        with Transaction().set_context(context):
            return super(ShipmentIn, self).create_inventory_moves(shipments)


class ShipmentOut:
    __name__ = 'stock.shipment.out'

    @ModelView.button
    @Workflow.transition('waiting')
    def wait(self, ids):
        context = Transaction().context.copy()
        context['explode_kit'] = False
        with Transaction().set_context(context):
            return super(ShipmentOut, self).wait(ids)
