import base64
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from ..services.payment import PaymentService

class TestPaymentFlow(TransactionCase):

    def setUp(self):
        super().setUp()
        self.owner = self.env['res.partner'].create({
            'name': 'Dueño Test Pagos',
            'is_snack_user': True
        })
        self.consumer = self.env['res.partner'].create({
            'name': 'Consumidor Test Pagos',
            'is_snack_user': True
        })
        self.product = self.env['office.snack.product'].create({
            'name': 'Papas',
            'price': 1500,
            'owner_id': self.owner.id,
            'stock': 10,
            'active': True
        })
        
        # Creamos dos consumos manualmente simulando compras previas
        self.consumption1 = self.env['office.snack.consumption'].create({
            'consumer_id': self.consumer.id,
            'product_id': self.product.id,
            'unit_price': self.product.price,
            'quantity': 1,
            'state': 'unpaid'
        })
        self.consumption2 = self.env['office.snack.consumption'].create({
            'consumer_id': self.consumer.id,
            'product_id': self.product.id,
            'unit_price': self.product.price,
            'quantity': 2,
            'state': 'unpaid'
        })

    def test_payment_grouping_and_approve(self):
        """Flujo feliz: Reportar pago y aprobar."""
        evidence_b64 = base64.b64encode(b"fake_image_data")
        
        # Reportar Pago (esto debe agrupar los 3000 de las 2 papas + 1500 de 1 papa = 4500)
        payment_id = PaymentService.report_payment(self.env, self.consumer.id, self.owner.id, evidence_b64)
        payment = self.env['office.snack.payment'].browse(payment_id)
        
        self.assertEqual(payment.state, 'pending')
        self.assertEqual(payment.amount, 4500)
        self.assertEqual(len(payment.consumption_ids), 2)
        
        # Validamos que los consumos pasaron a pending_payment
        self.assertEqual(self.consumption1.state, 'pending_payment')
        
        # Aprobar pago
        payment.action_approve()
        
        self.assertEqual(payment.state, 'approved')
        self.assertEqual(self.consumption1.state, 'paid')
        self.assertEqual(self.consumption2.state, 'paid')

    def test_payment_reject(self):
        """Flujo de rechazo: Consumos vuelven a unpaid."""
        evidence_b64 = base64.b64encode(b"fake_image_data")
        payment_id = PaymentService.report_payment(self.env, self.consumer.id, self.owner.id, evidence_b64)
        payment = self.env['office.snack.payment'].browse(payment_id)
        
        # Rechazar pago
        payment.action_reject()
        
        self.assertEqual(payment.state, 'rejected')
        # Los consumos deben haberse liberado y regresado a unpaid
        self.assertEqual(self.consumption1.state, 'unpaid')
        self.assertFalse(self.consumption1.payment_id)

    def test_payment_state_protection(self):
        """Garantizar que el estado del pago no puede modificarse arbitrariamente."""
        evidence_b64 = base64.b64encode(b"fake_image_data")
        payment_id = PaymentService.report_payment(self.env, self.consumer.id, self.owner.id, evidence_b64)
        payment = self.env['office.snack.payment'].browse(payment_id)
        
        # Aprobar desde un contexto inválido (directo por write)
        with self.assertRaisesRegex(UserError, "No puede cambiar el estado de un pago directamente"):
            payment.write({'state': 'approved'})
            
        # Pero a través de la acción sí es válido
        payment.action_approve()
        
        # Intentar rechazar un pago ya aprobado (ya no está 'pending')
        with self.assertRaisesRegex(UserError, "Solo se pueden rechazar pagos pendientes"):
            payment.action_reject()
