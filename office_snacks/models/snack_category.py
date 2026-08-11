from odoo import models, fields

class SnackCategory(models.Model):
    _name = 'office.snack.category'
    _description = 'Categoría de Snacks'
    _order = 'sequence, id'

    name = fields.Char(string="Nombre", required=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    active = fields.Boolean(string="Activa", default=True)
