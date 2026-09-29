from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_lubricant = fields.Boolean(string='Achat lubrifiants')
    need_request_id = fields.Many2one(
        'lubricant.need.request', string='Fiche de besoin', copy=False)
