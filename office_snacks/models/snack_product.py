from odoo import models, fields, api
from odoo.exceptions import UserError

class SnackProduct(models.Model):
    _name = 'office.snack.product'
    _description = 'Producto de Snacks'

    name = fields.Char(string="Nombre", required=True)
    price = fields.Monetary(string="Precio", required=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", 
                                  default=lambda self: self.env.company.currency_id.id, required=True)
    owner_id = fields.Many2one('res.partner', string="Dueño", required=True, 
                               domain="[('is_snack_user', '=', True)]",
                               default=lambda self: self.env.user.partner_id.id)
    stock = fields.Integer(string="Stock", default=0, required=True)
    image = fields.Binary(string="Imagen")
    active = fields.Boolean(string="Activo", default=True)

    _sql_constraints = [
        ('check_stock_positive', 'CHECK(stock >= 0)', 'El stock no puede ser negativo.')
    ]

    def decrement_stock(self, quantity=1):
        """ 
        Baja el stock atómicamente. Se llama desde el Service. 
        """
        self.ensure_one()
        self.env.cr.execute('''
            UPDATE office_snack_product 
            SET stock = stock - %s 
            WHERE id = %s AND stock >= %s AND active = true
        ''', (quantity, self.id, quantity))
        
        if self.env.cr.rowcount == 0:
            raise UserError(f"No hay stock suficiente para el producto {self.name} o está inactivo.")
        
        self.invalidate_recordset(['stock'])
