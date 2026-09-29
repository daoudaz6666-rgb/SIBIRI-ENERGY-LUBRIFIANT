from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_lubricant = fields.Boolean(string='Vente lubrifiants')
    pickup_requested = fields.Boolean(
        string='Retrait demandé', copy=False, readonly=True)
    pickup_date = fields.Date(string='Date de retrait prévue', copy=False)
    carrier_receipt_ref = fields.Char(
        string='N° du reçu transporteur', copy=False)
    carrier_receipt_ids = fields.Many2many(
        'ir.attachment', 'lubricant_sale_carrier_receipt_rel',
        'order_id', 'attachment_id',
        string='Reçu transporteur (scan)', copy=False)
    vat_certificate_ids = fields.One2many(
        'lubricant.vat.certificate', 'sale_id', string='Certificats de TVA')
    lubricant_closed = fields.Boolean(
        string='Circuit lubrifiants clôturé', copy=False, readonly=True)
    lubricant_stage = fields.Selection([
        ('quotation', '1-2. Cotation / proforma'),
        ('order', '3. Bon de commande'),
        ('pickup', '4. Retrait demandé'),
        ('invoiced', '5. Facturée'),
        ('delivered', '6. Livrée'),
        ('closed', '7. Clôturée'),
    ], string='Étape du circuit', compute='_compute_lubricant_stage')

    @api.depends('state', 'pickup_requested', 'invoice_status',
                 'carrier_receipt_ids', 'carrier_receipt_ref',
                 'vat_certificate_ids', 'lubricant_closed')
    def _compute_lubricant_stage(self):
        for order in self:
            if order.lubricant_closed:
                stage = 'closed'
            elif order.carrier_receipt_ids or order.carrier_receipt_ref:
                stage = 'delivered'
            elif order.invoice_status == 'invoiced':
                stage = 'invoiced'
            elif order.pickup_requested:
                stage = 'pickup'
            elif order.state == 'sale':
                stage = 'order'
            else:
                stage = 'quotation'
            order.lubricant_stage = stage

    def action_request_pickup(self):
        for order in self:
            if order.state != 'sale':
                raise UserError(_(
                    "La commande %s doit être confirmée avant la demande de retrait.",
                    order.name))
            if not order.pickup_date:
                raise UserError(_("Renseignez la date de retrait prévue."))
            order.pickup_requested = True
        return True

    def action_lubricant_close(self):
        for order in self:
            if not order.is_lubricant:
                continue
            if order.state != 'sale':
                raise UserError(_(
                    "La commande %s doit être confirmée avant la clôture.", order.name))
            if not order.pickup_requested:
                raise UserError(_("L'expression de besoin de retrait est manquante."))
            if order.invoice_status != 'invoiced':
                raise UserError(_("La facture définitive doit être établie."))
            if not (order.carrier_receipt_ids or order.carrier_receipt_ref):
                raise UserError(_("Le reçu transporteur est manquant."))
            if not order.vat_certificate_ids:
                raise UserError(_(
                    "Un certificat de TVA est requis avant la clôture de %s.", order.name))
            order.lubricant_closed = True
        return True
