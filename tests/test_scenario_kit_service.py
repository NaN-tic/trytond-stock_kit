import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.company.tests.tools import create_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestKitService(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        activate_modules('stock_kit')
        create_company()
        Template = Model.get('product.template')
        Product = Model.get('product.product')
        Uom = Model.get('product.uom')
        unit, = Uom.find([('name', '=', 'Unit')])
        template = Template(name='Service Kit', type='service',
            default_uom=unit, list_price=Decimal(10))
        kit, = template.products
        kit.kit = True
        kit.stock_depends_on_kit_components = True
        template.save()
        kit, = template.products
        self.assertEqual(kit.type, 'service')
        self.assertFalse(kit.consumable)
        template.name = 'Updated Service Kit'
        template.save()
        kit.reload()
        self.assertEqual(kit.type, 'service')

        # Updating stock_kit must not rewrite existing product types.
        Module = Model.get('ir.module')
        module, = Module.find([('name', '=', 'stock_kit')])
        module.click('upgrade')
        Wizard('ir.module.activate_upgrade').execute('upgrade')
        kit = Product(kit.id)
        self.assertEqual(kit.type, 'service')
        self.assertFalse(kit.consumable)
