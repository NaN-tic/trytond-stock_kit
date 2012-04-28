#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.


from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.transaction import Transaction


class ShipmentIn(Workflow, ModelSQL, ModelView):
    "Supplier Shipment"
    _name = 'stock.shipment.in'

    def create_inventory_moves(self, shipments):
        """ ensure no explode kits again on inventory moves """
        context = Transaction().context.copy()
        context['explode_kit'] = False
        with Transaction().set_context(context):
            return super(ShipmentIn, self).create_inventory_moves(shipments)

ShipmentIn()


class ShipmentOut(Workflow, ModelSQL, ModelView):

    _name = 'stock.shipment.out'

    @ModelView.button
    @Workflow.transition('waiting')
    def wait(self, ids):
        context = Transaction().context.copy()
        context['explode_kit'] = False
        with Transaction().set_context(context):
            return super(ShipmentOut, self).wait(ids)

ShipmentOut()
