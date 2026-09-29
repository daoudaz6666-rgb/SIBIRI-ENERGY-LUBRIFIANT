from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LubricantVatCertificate(models.Model):
    _name = 'lubricant.vat.certificate'
    _description = 'Certificat de TVA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Numéro du certificat', required=True, copy=False, tracking=True)
    date = fields.Date(
        string='Date', default=fields.Date.context_today,
        required=True, tracking=True)
    purchase_id = fields.Many2one(
        'purchase.order', string='Commande achat',
        ondelete='restrict', tracking=True)
    sale_id = fields.Many2one(
        'sale.order', string='Commande vente',
        ondelete='restrict', tracking=True)
    move_id = fields.Many2one(
        'account.move', string='Facture', ondelete='restrict')
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Fichiers (scan du certificat)')
    company_id = fields.Many2one(
        'res.company', string='Société',
        default=lambda self: self.env.company, required=True)
    note = fields.Text(string='Remarques')

    @api.constrains('purchase_id', 'sale_id', 'move_id')
    def _check_origin(self):
        for rec in self:
            if not (rec.purchase_id or rec.sale_id or rec.move_id):
                raise ValidationError(_(
                    "Le certificat doit être rattaché à un achat, une vente ou une facture."))

    @api.constrains('name', 'company_id')
    def _check_unique_name(self):
        for rec in self:
            duplicate = self.search_count([
                ('id', '!=', rec.id),
                ('name', '=', rec.name),
                ('company_id', '=', rec.company_id.id),
            ])
            if duplicate:
                raise ValidationError(_(
                    "Le certificat %s existe déjà.", rec.name))
