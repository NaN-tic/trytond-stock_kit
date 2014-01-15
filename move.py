#This file is part stock_kit module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import In, Eval
from trytond.transaction import Transaction

__all__ = ['Move']
__metaclass__ = PoolMeta
STATES = {
    'readonly': In(Eval('state'), ['cancel', 'assigned', 'done']),
}
DEPENDS = ['state']


class Move:
    __name__ = 'stock.move'
    sequence = fields.Integer('Sequence')
    kit_depth = fields.Integer('Depth', required=True,
            help='Depth of the line if it is part of a kit.')
    kit_parent_line = fields.Many2One('stock.move', 'Parent Kit Line',
            help='The kit that contains this product.')
    kit_child_lines = fields.One2Many('stock.move', 'kit_parent_line',
            'Lines in the kit', help='Subcomponents of the kit.')

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        cls._order.insert(0, ('id', 'ASC'))

    @staticmethod
    def default_kit_depth():
        return 0

    def get_kit_line(self, line, kit_line, depth):
        '''
        Given a line browse object and a kit dictionary returns the
        dictionary of fields to be stored in a create statement.
        '''
        res = {}
        uom_obj = Pool().get('product.uom')
        quantity = uom_obj.compute_qty(kit_line.unit,
                        kit_line.quantity, line.uom) * line.quantity

        res['sequence'] = line.id + depth
        res['product'] = kit_line.product.id
        res['quantity'] = quantity
        res['from_location'] = line.from_location.id
        res['to_location'] = line.to_location.id
        res['unit_price'] = line.unit_price
        res['kit_depth'] = depth
        res['kit_parent_line'] = line.id
        res['planned_date'] = False
        res['company'] = line.company.id
        res['uom'] = line.uom.id
        res['shipment_out'] = (line.shipment_out and line.shipment_out.id
            or False)
        res['shipment_in'] = (line.shipment_in and line.shipment_in.id
            or False)
        res['shipment_out_return'] = (line.shipment_out_return
            and line.shipment_out_return.id or False)
        res['shipment_in_return'] = (line.shipment_in_return
            and line.shipment_in_return.id or False)
        res['shipment_internal'] = (line.shipment_internal
            and line.shipment_internal or False)
        return res

    def explode_kit(self, moves, depth=1):
        '''
        Walks through the Kit tree in depth-first order and returns
        a sorted list with all the components of the product.
        '''
        line = self.browse(moves)
        result = []
        ''' Check if kit need to be Exploded '''
        explode = Transaction().context.get('explode_kit', True)
        if not explode:
            return result
        ''' Check if kit has been already expanded '''
        if line.kit_child_lines:
            return result
        ''' Check if line belongs to any shipment '''
        if not (line.shipment_in or line.shipment_out
                or line.shipment_out_return or line.shipment_in_return
                or line.shipment_internal):
            return result
        ''' Explode kit '''
        for kit_line in line.product.kit_lines:
            values = self.get_kit_line(line, kit_line, depth)
            new_id = self.create(values)
            self.explode_kit(new_id, depth + 1)
        return result

    def create(self, values):
        #print Transaction().context
        move = super(Move, self).create(values)
        self.explode_kit(move)
        return move

    def kit_tree_ids(self, line):
        res = []
        for kit_line in line.kit_child_lines:
            res.append(kit_line.id)
            res += self.kit_tree_ids(kit_line)
        return res

    def write(self, ids, values):
        ''' Regenerate kit if quantity, product or unit has changed '''
        if not('product' in values or 'quantity' in values
                or 'unit' in values):
            return super(Move, self).write(ids, values)
        if isinstance(ids, (int, long)):
            ids = [ids]
        ids = ids[:]
        kits_to_reset = []
        moves_to_delete = []
        for line in self.browse(ids):
            if not line.product.kit:
                continue
            if (('product' in values and line.product.id != values['product'])
                    or
                    ('quantity' in values
                        and line.quantity != values['quantity'])
                    or
                    ('unit' in values and line.unit != values['unit'])):
                kits_to_reset.append(line.id)
                moves_to_delete += self.kit_tree_ids(line)
        if moves_to_delete:
            self.delete(moves_to_delete)
        if kits_to_reset:
            for kit in kits_to_reset:
                self.explode_kit(kit)
        return super(Move, self).write(ids, values)

    def delete(self, ids):
        ''' Check if stock move to delete belongs to kit.'''
        ids = ids[:]
        for line in self.browse(ids):
            if line.kit_parent_line:
                continue
            if line.kit_child_lines:
                ''' Removing kit, adding all childs products to delete'''
                ids += self.kit_tree_ids(line)
        return super(Move, self).delete(ids)
