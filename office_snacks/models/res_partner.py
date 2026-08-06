from odoo import models, fields, api
from werkzeug.security import generate_password_hash, check_password_hash

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_snack_user = fields.Boolean(string="Es Comprador de Snacks", default=False)
    is_snack_vendor = fields.Boolean(string="Es Vendedor/Dueño de Snacks", default=False)
    
    # Campo UI para setear el PIN sin guardar en texto plano
    snack_pin = fields.Char(string="Nuevo PIN de Snacks", store=False, inverse='_inverse_snack_pin')
    
    # Hash almacenado en DB, no se lee en UI.
    snack_pin_hash = fields.Char(string="PIN Hash de Snacks", copy=False)
    
    # Información de pago para el Dueño
    payment_bank = fields.Char(string="Banco / Billetera (Snacks)", help="Ej. Bancolombia, Nequi, Transfiya")
    payment_account = fields.Char(string="Cuenta / Llave (Snacks)", help="Número de celular o de cuenta")
    qr_payment_image = fields.Binary(string="Código QR para Pago", help="Sube la imagen del QR para que te paguen")

    def _inverse_snack_pin(self):
        for record in self:
            if record.snack_pin:
                record._set_snack_pin(record.snack_pin)

    def _set_snack_pin(self, plain_text):
        """Genera y guarda el hash del PIN"""
        self.ensure_one()
        if plain_text:
            self.snack_pin_hash = generate_password_hash(plain_text)

    def _check_snack_pin(self, plain_text):
        """Verifica el PIN contra el hash almacenado"""
        self.ensure_one()
        if not self.snack_pin_hash or not plain_text:
            return False
        return check_password_hash(self.snack_pin_hash, plain_text)
