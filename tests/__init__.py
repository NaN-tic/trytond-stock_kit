# This file is part stock_kit module for Tryton.  The COPYRIGHT file at the top
# level of this repository contains the full copyright notices and license
# terms.
try:
    from trytond.modules.stock_kit.tests.test_stock_kit import suite
except ImportError:
    from .test_stock_kit import suite

__all__ = ['suite']
