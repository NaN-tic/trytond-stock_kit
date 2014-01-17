#This file is part stock_kit module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import In, Eval
from trytond.transaction import Transaction

__all__ = ['Move', 'CreateShipmentOutReturn']
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

    @classmethod
    def explode_kit(cls, moves):
        '''
        Walks through the Kit tree in depth-first order and returns
        a sorted list with all the components of the product.
        '''
        pool = Pool()
        StockMove = pool.get('stock.move')
        ProductUom = pool.get('product.uom')
        explode = Transaction().context.get('explode_kit', True)
        result = []
        if explode:
            for move in moves:
                depth = move.kit_depth + 1
                if (move.shipment and move.product and move.product.kit_lines
                        and move.product.explode_kit_in_shipments):
                    for kit_move in move.product.kit_lines:
                        quantity = ProductUom.compute_qty(kit_move.unit,
                            kit_move.quantity, move.uom) * move.quantity
                        stock_move = StockMove()
                        stock_move.sequence = move.id + depth
                        stock_move.product = kit_move.product.id
                        stock_move.quantity = quantity
                        stock_move.from_location = move.from_location.id
                        stock_move.to_location = move.to_location.id
                        stock_move.unit_price = move.unit_price
                        stock_move.kit_depth = depth
                        stock_move.kit_parent_line = move.id
                        stock_move.planned_date = None
                        stock_move.company = move.company.id
                        stock_move.uom = move.uom.id
                        stock_move.shipment = '%s,%s' % (
                            move.shipment.__name__, move.shipment.id)
                        stock_move.save()
                        result.append(stock_move)
        return result

    @classmethod
    def create(cls, values):
        moves = super(Move, cls).create(values)
        moves.extend(cls.explode_kit(moves))
        return moves

    def get_kit_moves(self):
        res = []
        for kit_move in self.kit_child_lines:
            res.append(kit_move)
            res += kit_move.get_kit_moves()
        return res

    @classmethod
    def write(cls, moves, values):
        ''' Regenerate kit if quantity, product or unit has changed '''
        if not('product' in values or 'quantity' in values
                or 'unit' in values):
            return super(Move, cls).write(moves, values)
        moves = moves[:]
        kits_to_reset = []
        moves_to_delete = []
        for move in moves:
            if not move.product.kit:
                continue
            if (('product' in values and move.product.id != values['product'])
                    or
                    ('quantity' in values
                        and move.quantity != values['quantity'])
                    or
                    ('unit' in values and move.unit != values['unit'])):
                kits_to_reset.append(move.id)
                moves_to_delete += move.get_kit_moves()
        if moves_to_delete:
            cls.delete(moves_to_delete)
        if kits_to_reset:
            for kit in kits_to_reset:
                cls.explode_kit(kit)
        return super(Move, cls).write(moves, values)

    @classmethod
    def delete(cls, moves):
        ''' Check if stock move to delete belongs to kit.'''
        moves = moves[:]
        for move in moves:
            if move.kit_parent_line:
                continue
            if move.kit_child_lines:
                ''' Removing kit, adding all childs products to delete'''
                moves += move.get_kit_moves()
        return super(Move, cls).delete(moves)


class CreateShipmentOutReturn:
    __name__ = 'stock.shipment.out.return.create'

    def do_start(self, action):
        with Transaction().set_context({'explode_kit': False}):
            return super(CreateShipmentOutReturn, self).do_start(action)
