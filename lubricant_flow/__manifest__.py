{
    'name': 'Lubricant Flow',
    'version': '20.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': "Circuits d'achat et de vente de lubrifiants",
    'depends': ['purchase', 'sale_management', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/need_request_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
