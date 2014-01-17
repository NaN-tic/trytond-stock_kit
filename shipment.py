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

    @classmethod
    def create_inventory_moves(cls, shipments):
        """ ensure no explode kits again on inventory moves """
        context = Transaction().context.copy()
        context['explode_kit'] = False
        with Transaction().set_context(context):
            return super(ShipmentIn, cls).create_inventory_moves(shipments)


class ShipmentOut:
    __name__ = 'stock.shipment.out'

    @classmethod
    @ModelView.button
    @Workflow.transition('waiting')
    def wait(cls, shipments):
        context = Transaction().context.copy()
        context['explode_kit'] = False
        with Transaction().set_context(context):
            return super(ShipmentOut, cls).wait(shipments)
