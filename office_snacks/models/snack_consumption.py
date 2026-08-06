from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SnackConsumption(models.Model):
    _name = 'office.snack.consumption'
    _description = 'Consumo de Snack'

    consumer_id = fields.Many2one('res.partner', string="Consumidor", required=True, ondelete='restrict')
    product_id = fields.Many2one('office.snack.product', string="Producto", required=True, ondelete='restrict')
    owner_id = fields.Many2one('res.partner', related="product_id.owner_id", store=True, string="Dueño")
    
    quantity = fields.Integer(string="Cantidad", default=1, required=True)
    
    unit_price = fields.Monetary(string="Precio Unitario", required=True)
    currency_id = fields.Many2one(related='product_id.currency_id', store=True)
    total_price = fields.Monetary(string="Precio Total", compute='_compute_total_price', store=True)
    
    state = fields.Selection([
        ('unpaid', 'No Pagado'),
        ('pending_payment', 'Pago Pendiente'),
        ('paid', 'Pagado')
    ], string="Estado", default='unpaid', required=True)

    payment_id = fields.Many2one('office.snack.payment', string="Pago Asociado", ondelete='set null')

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.quantity * record.unit_price

    @api.constrains('state', 'payment_id')
    def _check_payment_link(self):
        for record in self:
            if record.state in ('pending_payment', 'paid') and not record.payment_id:
                raise ValidationError("Un consumo pendiente o pagado debe estar asociado a un pago.")
