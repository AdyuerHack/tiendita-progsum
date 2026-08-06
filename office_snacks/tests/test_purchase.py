from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from ..services.purchase import PurchaseService

class TestPurchase(TransactionCase):

    def setUp(self):
        super().setUp()
        self.owner = self.env['res.partner'].create({
            'name': 'Dueño Test',
            'is_snack_user': True,
            'is_snack_vendor': True,
        })
        self.consumer = self.env['res.partner'].create({
            'name': 'Consumidor Test',
            'is_snack_user': True
        })
        self.product = self.env['office.snack.product'].create({
            'name': 'Chocolatina',
            'price': 2000,
            'owner_id': self.owner.id,
            'stock': 1,
            'active': True
        })

    def test_purchase_success(self):
        """Test simple: Comprar con stock suficiente."""
        success = PurchaseService.buy_product(self.env, self.consumer.id, self.product.id, quantity=1)
        self.assertTrue(success)
        
        # El stock debe haber bajado a 0
        self.product.invalidate_recordset(['stock'])
        self.assertEqual(self.product.stock, 0)
        
        # Se debe haber creado un consumo unpaid
        consumption = self.env['office.snack.consumption'].search([('consumer_id', '=', self.consumer.id)])
        self.assertEqual(len(consumption), 1)
        self.assertEqual(consumption.state, 'unpaid')
        self.assertEqual(consumption.total_price, 2000)

    def test_purchase_no_stock(self):
        """Test atómico/restricción: Intentar comprar sin stock debe fallar."""
        # Compramos la única unidad disponible
        PurchaseService.buy_product(self.env, self.consumer.id, self.product.id, quantity=1)
        
        # Intentamos comprar otra vez (simulando concurrencia o un segundo click, con stock a 0)
        with self.assertRaisesRegex(UserError, "No hay stock suficiente"):
            PurchaseService.buy_product(self.env, self.consumer.id, self.product.id, quantity=1)

    def test_pin_hashing(self):
        """Test de que el PIN se hashea correctamente y no se guarda en texto plano."""
        self.owner.snack_pin = '1234'
        self.assertTrue(self.owner.snack_pin_hash)
        self.assertNotEqual(self.owner.snack_pin_hash, '1234')
        self.assertTrue(self.owner._check_snack_pin('1234'))
        self.assertFalse(self.owner._check_snack_pin('0000'))

    def test_frozen_price(self):
        """Test de que el precio unitario del consumo se congela al comprar."""
        PurchaseService.buy_product(self.env, self.consumer.id, self.product.id, quantity=1)
        consumption = self.env['office.snack.consumption'].search([('consumer_id', '=', self.consumer.id)])
        
        # Guardó el precio original
        self.assertEqual(consumption.unit_price, 2000)
        self.assertEqual(consumption.total_price, 2000)
        
        # El dueño le sube el precio
        self.product.price = 3000
        
        # Invalidate y asegurar que la deuda vieja no cambió
        consumption.invalidate_recordset(['unit_price', 'total_price'])
        self.assertEqual(consumption.unit_price, 2000)
        self.assertEqual(consumption.total_price, 2000)
