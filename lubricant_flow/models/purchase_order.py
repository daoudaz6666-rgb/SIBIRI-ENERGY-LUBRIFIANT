from odoo import fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_lubricant = fields.Boolean(string='Achat lubrifiants')
    need_request_id = fields.Many2one(
        'lubricant.need.request', string='Fiche de besoin', copy=False)
    vat_certificate_ids = fields.One2many(
        'lubricant.vat.certificate', 'purchase_id', string='Certificats de TVA')
    lubricant_closed = fields.Boolean(
        string='Circuit lubrifiants clôturé', copy=False, readonly=True)

    def action_lubricant_close(self):
        for order in self:
            if not order.is_lubricant:
                continue
            if order.state != 'purchase':
                raise UserError(_(
                    "La commande %s doit être confirmée avant la clôture.", order.name))
            if not order.vat_certificate_ids:
                raise UserError(_(
                    "Un certificat de TVA est requis avant la clôture de %s.", order.name))
            order.lubricant_closed = True
        return True
