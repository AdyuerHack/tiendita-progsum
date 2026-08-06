class PaymentService:
    """
    Orquesta el flujo de agrupación de deuda y reporte de pagos.
    """

    @staticmethod
    def get_owner(env, owner_id):
        """Retorna el partner dueño de manera segura."""
        owner = env['res.partner'].sudo().browse(owner_id)
        if owner.exists() and owner.is_snack_user:
            return owner
        return None

    @staticmethod
    def get_debt_summary(env, consumer_id):
        """
        Devuelve la deuda agrupada por dueño para un consumidor específico.
        """
        sudo_env = env(su=True)
        consumptions = sudo_env['office.snack.consumption'].search([
            ('consumer_id', '=', consumer_id),
            ('state', '=', 'unpaid')
        ])

        debt_by_owner = {}
        for c in consumptions:
            owner = c.owner_id
            if owner not in debt_by_owner:
                debt_by_owner[owner] = {
                    'owner_id': owner.id,
                    'owner_name': owner.name,
                    'payment_bank': owner.payment_bank,
                    'payment_account': owner.payment_account,
                    'total_amount': 0.0,
                    'currency_id': c.currency_id.id,
                    'consumption_ids': []
                }
            debt_by_owner[owner]['total_amount'] += c.total_price
            debt_by_owner[owner]['consumption_ids'].append(c.id)

        return list(debt_by_owner.values())

    @staticmethod
    def report_payment(env, consumer_id, owner_id, evidence_b64):
        """
        Crea el pago y vincula los consumos.
        """
        sudo_env = env(su=True)
        
        # 1. Buscar consumos unpaid del consumidor hacia ese dueño
        consumptions = sudo_env['office.snack.consumption'].search([
            ('consumer_id', '=', consumer_id),
            ('owner_id', '=', owner_id),
            ('state', '=', 'unpaid')
        ])

        if not consumptions:
            raise ValueError("No hay deuda pendiente con este dueño.")

        total_amount = sum(c.total_price for c in consumptions)

        # 2. Crear el pago con la evidencia
        payment = sudo_env['office.snack.payment'].with_context(allow_state_change=True).create({
            'consumer_id': consumer_id,
            'owner_id': owner_id,
            'amount': total_amount,
            'evidence': evidence_b64,
            'currency_id': consumptions[0].currency_id.id,
            'state': 'pending'
        })

        # 3. Vincular y actualizar estado de consumos
        consumptions.write({
            'payment_id': payment.id,
            'state': 'pending_payment'
        })

        return payment.id
