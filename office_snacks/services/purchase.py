class PurchaseService:
    """
    Orquesta el flujo de compras 'One-Tap'.
    Responsabilidad: Bajar stock de forma atómica y registrar el consumo para el usuario.
    """

    @staticmethod
    def buy_product(env, consumer_id, product_id, quantity=1):
        """
        Ejecuta una compra. Delega el control de concurrencia al modelo de producto.
        """
        # Elevamos privilegios de forma documentada porque el consumidor no tiene acceso a BD directamente.
        sudo_env = env.sudo()
        
        # 1. Validar producto
        product = sudo_env['office.snack.product'].browse(product_id)
        if not product.exists() or not product.active:
            raise ValueError("El producto no existe o no está activo.")

        # 2. Validar consumidor (ya fue autenticado por el Controller, solo garantizamos que exista)
        consumer = sudo_env['res.partner'].browse(consumer_id)
        if not consumer.exists() or not consumer.is_snack_user:
            raise ValueError("Consumidor no válido.")

        # 3. Disminuir stock atómicamente (El modelo lanza UserError si falla)
        product.decrement_stock(quantity)

        # 4. Registrar el consumo con el precio actual congelado
        sudo_env['office.snack.consumption'].create({
            'consumer_id': consumer.id,
            'product_id': product.id,
            'unit_price': product.price,
            'currency_id': product.currency_id.id,
            'quantity': quantity,
            'state': 'unpaid'
        })

        return True

    @staticmethod
    def get_available_products(env):
        """Retorna los productos que el consumidor puede ver."""
        return env['office.snack.product'].sudo().search([
            ('active', '=', True), 
            ('stock', '>', 0)
        ])
