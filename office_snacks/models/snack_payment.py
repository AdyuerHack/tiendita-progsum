from odoo import models, fields, api
from odoo.exceptions import UserError

class SnackPayment(models.Model):
    _name = 'office.snack.payment'
    _description = 'Pago de Snacks'

    consumer_id = fields.Many2one('res.partner', string="Consumidor", required=True)
    owner_id = fields.Many2one('res.partner', string="Dueño (Recibe)", required=True)
    
    currency_id = fields.Many2one('res.currency', string="Moneda", default=lambda self: self.env.company.currency_id.id, required=True)
    amount = fields.Monetary(string="Monto Pagado", required=True)
    
    evidence = fields.Binary(string="Evidencia de Pago", required=True)
    
    state = fields.Selection([
        ('pending', 'Pendiente de Aprobación'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string="Estado", default='pending', required=True)

    consumption_ids = fields.One2many('office.snack.consumption', 'payment_id', string="Consumos")

    def action_approve(self):
        for record in self:
            if record.state != 'pending':
                raise UserError("Solo se pueden aprobar pagos pendientes.")
            record.with_context(allow_state_change=True).write({'state': 'approved'})
            record.consumption_ids.write({'state': 'paid'})

    def action_reject(self):
        for record in self:
            if record.state != 'pending':
                raise UserError("Solo se pueden rechazar pagos pendientes.")
            record.with_context(allow_state_change=True).write({'state': 'rejected'})
            # Liberamos consumos
            record.consumption_ids.write({
                'state': 'unpaid',
                'payment_id': False
            })

    def write(self, vals):
        # Impedir modificar el estado directamente sin usar actions
        if 'state' in vals and not self.env.context.get('allow_state_change'):
            raise UserError("No puede cambiar el estado de un pago directamente. Use los botones de acción.")
        return super().write(vals)
