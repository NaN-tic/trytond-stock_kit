#!/usr/bin/env python
# This file is part stock_kit module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends


class StockKitTestCase(unittest.TestCase):
    'Test Stock Kit module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('stock_kit')

    def test0005views(self):
        'Test views'
        test_view('stock_kit')

    def test0006depends(self):
        'Test depends'
        test_depends()


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        StockKitTestCase))
    return suite
