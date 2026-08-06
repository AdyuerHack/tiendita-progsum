class AuthService:
    """
    Gestiona la identidad de los usuarios del sistema de Snacks.
    Responsabilidad: Validar PINs, obtener el partner logueado, sin tocar odoo.http.request.
    """

    @staticmethod
    def get_partner(env, partner_id):
        """Retorna el partner si existe y es usuario snack."""
        if not partner_id:
            return None
        partner = env['res.partner'].sudo().browse(partner_id)
        if partner.exists() and partner.is_snack_user:
            return partner
        return None

    @staticmethod
    def get_snack_users(env):
        """Retorna los usuarios habilitados para snacks."""
        return env['res.partner'].sudo().search([('is_snack_user', '=', True)])

    @staticmethod
    def login(env, partner_id, pin):
        """Verifica las credenciales de un partner."""
        partner = env['res.partner'].sudo().browse(partner_id)
        if not partner.exists() or not partner.is_snack_user:
            return False
        return partner._check_snack_pin(pin)
