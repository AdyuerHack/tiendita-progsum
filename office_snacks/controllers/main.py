import base64
from odoo import http
from odoo.http import request
from ..services.auth import AuthService
from ..services.purchase import PurchaseService
from ..services.payment import PaymentService

class OfficeSnacksController(http.Controller):

    def _get_consumer(self):
        """Helper para obtener el consumidor logueado de la sesión sin tocar BD directamente."""
        partner_id = request.session.get('snack_partner_id')
        if not partner_id:
            return None
        return AuthService.get_partner(request.env, partner_id)

    @http.route('/snacks/login', type='http', auth='public', website=True)
    def snacks_login_page(self, **kw):
        """Página para seleccionar usuario e ingresar PIN."""
        if self._get_consumer():
            return request.redirect('/snacks')
        
        # Delegar a AuthService
        partners = AuthService.get_snack_users(request.env)
        error = kw.get('error')
        
        return request.render('office_snacks.login_template', {
            'partners': partners,
            'error': error
        })

    @http.route('/snacks/login/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def snacks_login_submit(self, **post):
        """Procesa el formulario de login."""
        partner_id = int(post.get('partner_id', 0))
        pin = post.get('pin')
        
        if AuthService.login(request.env, partner_id, pin):
            request.session['snack_partner_id'] = partner_id
            return request.redirect('/snacks')
        
        return request.redirect('/snacks/login?error=1')

    @http.route('/snacks/logout', type='http', auth='public', website=True)
    def snacks_logout(self, **kw):
        """Cierra la sesión de snacks."""
        request.session.pop('snack_partner_id', None)
        return request.redirect('/snacks/login')

    @http.route('/snacks', type='http', auth='public', website=True)
    def snacks_catalog(self, **kw):
        """Catálogo principal de productos (One-Tap)."""
        consumer = self._get_consumer()
        if not consumer:
            return request.redirect('/snacks/login')
        
        # Delegamos lectura segura
        products = PurchaseService.get_available_products(request.env)
        
        return request.render('office_snacks.catalog_template', {
            'consumer': consumer,
            'products': products
        })

    @http.route('/snacks/buy', type='json', auth='public', methods=['POST'], csrf=True)
    def snacks_buy(self, product_id, **kw):
        """Endpoint Ajax para la compra One-Tap."""
        consumer = self._get_consumer()
        if not consumer:
            return {'error': 'unauthorized', 'redirect': '/snacks/login'}
        
        try:
            PurchaseService.buy_product(request.env, consumer.id, int(product_id), quantity=1)
            return {'success': True, 'message': '¡Snack comprado exitosamente!'}
        except Exception as e:
            return {'error': "No se pudo procesar la compra."}

    @http.route('/snacks/debt', type='http', auth='public', website=True)
    def snacks_debt(self, **kw):
        """Pantalla de deudas agrupadas."""
        consumer = self._get_consumer()
        if not consumer:
            return request.redirect('/snacks/login')
        
        # Delegamos lectura segura
        debt_summary = PaymentService.get_debt_summary(request.env, consumer.id)
        success = kw.get('success')
        
        return request.render('office_snacks.debt_template', {
            'consumer': consumer,
            'debt_summary': debt_summary,
            'success': success
        })

    @http.route('/snacks/pay/<int:owner_id>', type='http', auth='public', website=True)
    def snacks_pay_page(self, owner_id, **kw):
        """Pantalla para ver detalles de pago (Banco, Llave, QR) y subir comprobante."""
        consumer = self._get_consumer()
        if not consumer:
            return request.redirect('/snacks/login')
        
        debt_summary = PaymentService.get_debt_summary(request.env, consumer.id)
        owner_debt = next((d for d in debt_summary if d['owner_id'] == owner_id), None)
        
        if not owner_debt:
            return request.redirect('/snacks/debt')
            
        owner = PaymentService.get_owner(request.env, owner_id)
        if not owner:
            return request.redirect('/snacks/debt')
            
        error = kw.get('error')

        return request.render('office_snacks.pay_template', {
            'consumer': consumer,
            'owner_debt': owner_debt,
            'owner': owner,
            'error': error
        })

    @http.route('/snacks/pay/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def snacks_pay_submit(self, **post):
        """Recibe el archivo (evidencia) y procesa el reporte de pago."""
        consumer = self._get_consumer()
        if not consumer:
            return request.redirect('/snacks/login')
            
        owner_id = int(post.get('owner_id', 0))
        evidence_file = post.get('evidence')
        
        if not owner_id or not evidence_file:
            return request.redirect(f'/snacks/pay/{owner_id}?error=missing_data')
            
        try:
            evidence_b64 = base64.b64encode(evidence_file.read())
            # Delegar la creación del pago al PaymentService
            PaymentService.report_payment(request.env, consumer.id, owner_id, evidence_b64)
            return request.redirect('/snacks/debt?success=1')
        except Exception as e:
            return request.redirect(f'/snacks/pay/{owner_id}?error=upload_error')
