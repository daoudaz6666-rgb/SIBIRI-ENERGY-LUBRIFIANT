from odoo import api, fields, models, _
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
    lubricant_stage = fields.Selection([
        ('rfq', 'Demande de prix'),
        ('ordered', 'Commandé'),
        ('received', 'Reçu'),
        ('invoiced', 'Facturé'),
        ('certified', 'Certificat TVA reçu'),
        ('closed', 'Clôturé'),
        ('cancel', 'Annulé'),
    ], string='Étape du circuit', compute='_compute_lubricant_stage', store=True)

    @api.depends('state', 'invoice_status', 'picking_ids.state',
                 'vat_certificate_ids', 'lubricant_closed')
    def _compute_lubricant_stage(self):
        for order in self:
            pickings = order.picking_ids.filtered(lambda p: p.state != 'cancel')
            if order.state == 'cancel':
                stage = 'cancel'
            elif order.lubricant_closed:
                stage = 'closed'
            elif order.vat_certificate_ids:
                stage = 'certified'
            elif order.invoice_status == 'invoiced':
                stage = 'invoiced'
            elif pickings and all(p.state == 'done' for p in pickings):
                stage = 'received'
            elif order.state in ('purchase', 'done'):
                stage = 'ordered'
            else:
                stage = 'rfq'
            order.lubricant_stage = stage

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
