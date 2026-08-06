{
    'name': 'Office Snacks',
    'version': '19.0.1.0.1',
    'summary': 'Gestión de venta de snacks en la oficina basado en confianza',
    'description': 'Módulo para compras One-Tap y gestión de consumos y pagos de snacks.',
    'category': 'Sales',
    'author': 'Adyue',
    'depends': ['base', 'website'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/snack_menus.xml',
        'views/snack_product_views.xml',
        'views/snack_consumption_views.xml',
        'views/snack_payment_views.xml',
        'views/res_partner_views.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'office_snacks/static/src/js/snack_portal.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
