# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import datetime
from decimal import Decimal

from trytond.modules.company.tests import (
    CompanyTestMixin, create_company, set_company)
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.transaction import Transaction


class StockKitTestCase(CompanyTestMixin, ModuleTestCase):
    'Test StockKit module'
    module = 'stock_kit'

    @with_transaction()
    def test_kit_available_quantity(self):
        "Test physical and component-based kit quantities are kept separate"
        pool = Pool()
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        KitLine = pool.get('product.kit.line')
        Uom = pool.get('product.uom')
        Location = pool.get('stock.location')
        Move = pool.get('stock.move')
        ProductsByLocations = pool.get('stock.products_by_locations')

        unit, = Uom.search([('name', '=', 'Unit')])
        supplier, = Location.search([('code', '=', 'SUP')])
        storage, = Location.search([('code', '=', 'STO')])
        customer, = Location.search([('code', '=', 'CUS')])
        company = create_company()

        with set_company(company):
            templates = Template.create([{
                        'name': 'Component 1',
                        'type': 'goods',
                        'default_uom': unit.id,
                        }, {
                        'name': 'Component 2',
                        'type': 'goods',
                        'default_uom': unit.id,
                        }, {
                        'name': 'Kit',
                        'type': 'goods',
                        'consumable': True,
                        'default_uom': unit.id,
                        }])
            component1, component2, kit = Product.create([{
                        'template': templates[0].id,
                        }, {
                        'template': templates[1].id,
                        }, {
                        'template': templates[2].id,
                        'kit': True,
                        'stock_depends_on_kit_components': True,
                        }])
            KitLine.create([{
                        'parent': kit.id,
                        'product': component1.id,
                        'quantity': 10,
                        'unit': unit.id,
                        }, {
                        'parent': kit.id,
                        'product': component2.id,
                        'quantity': 1,
                        'unit': unit.id,
                        }])

            today = datetime.date.today()
            moves = Move.create([{
                        'product': component1.id,
                        'unit': unit.id,
                        'quantity': 300,
                        'from_location': supplier.id,
                        'to_location': storage.id,
                        'planned_date': today,
                        'effective_date': today,
                        'company': company.id,
                        'unit_price': Decimal(0),
                        'currency': company.currency.id,
                        }, {
                        'product': component2.id,
                        'unit': unit.id,
                        'quantity': 1000,
                        'from_location': supplier.id,
                        'to_location': storage.id,
                        'planned_date': today,
                        'effective_date': today,
                        'company': company.id,
                        'unit_price': Decimal(0),
                        'currency': company.currency.id,
                        }, {
                        'product': kit.id,
                        'unit': unit.id,
                        'quantity': 3,
                        'from_location': storage.id,
                        'to_location': customer.id,
                        'planned_date': today,
                        'effective_date': today,
                        'company': company.id,
                        'unit_price': Decimal(0),
                        'currency': company.currency.id,
                        }])
            Move.do(moves)

            kit = Product(kit.id)
            self.assertEqual(kit.kit_available_quantity, 30)

            with Transaction().set_context(
                    company=company.id, locations=[storage.id]):
                kit = Product(kit.id)
                self.assertEqual(kit.quantity, -3)
                self.assertEqual(kit.kit_available_quantity, 30)
                self.assertIsNone(
                    Product(component1.id).kit_available_quantity)
                kit_by_location, = ProductsByLocations.search([
                        ('product', '=', kit.id),
                        ])
                self.assertEqual(kit_by_location.quantity, -3)
                self.assertEqual(kit_by_location.kit_available_quantity, 30)


del ModuleTestCase
