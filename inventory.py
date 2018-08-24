# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['InventoryLine']


class InventoryLine(metaclass=PoolMeta):
    __name__ = 'stock.inventory.line'

    @classmethod
    def __setup__(cls):
        super(InventoryLine, cls).__setup__()
        cls.product.domain.append(['OR',
                ('kit', '=', False),
                ('stock_depends_on_kit_components', '=', False),
                ])
