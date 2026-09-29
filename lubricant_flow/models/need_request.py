from odoo import Command, api, fields, models, _
from odoo.exceptions import UserError


class LubricantNeedRequest(models.Model):
    _name = 'lubricant.need.request'
    _description = "Fiche d'expression de besoin (lubrifiants)"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Référence', default='Nouveau', copy=False,
        readonly=True, tracking=True)
    date = fields.Date(
        string='Date', default=fields.Date.context_today,
        required=True, tracking=True)
    requester_id = fields.Many2one(
        'res.users', string='Demandeur',
        default=lambda self: self.env.user, required=True, tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string='Dépôt / fournisseur', tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Société',
        default=lambda self: self.env.company, required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('approved', 'Approuvée'),
        ('ordered', 'Commandée'),
        ('cancel', 'Annulée'),
    ], string='Statut', default='draft', copy=False, tracking=True)
    line_ids = fields.One2many(
        'lubricant.need.request.line', 'request_id', string='Produits')
    note = fields.Text(string='Remarques')
    purchase_id = fields.Many2one(
        'purchase.order', string="Demande de prix / commande",
        readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'lubricant.need.request') or 'Nouveau'
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_("Ajoutez au moins un produit avant de soumettre."))
            rec.state = 'submitted'

    def action_approve(self):
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise UserError(_("Seul un responsable des achats peut approuver."))
        self.filtered(lambda r: r.state == 'submitted').write({'state': 'approved'})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'ordered':
                raise UserError(_("Une fiche déjà commandée ne peut pas être annulée."))
        self.write({'state': 'cancel'})

    def action_reset_draft(self):
        self.filtered(lambda r: r.state == 'cancel').write({'state': 'draft'})

    def action_create_rfq(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("La fiche doit être approuvée."))
        if not self.partner_id:
            raise UserError(_("Renseignez le dépôt / fournisseur."))
        order = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'origin': self.name,
            'is_lubricant': True,
            'need_request_id': self.id,
            'order_line': [
                Command.create({
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                })
                for line in self.line_ids
            ],
        })
        self.write({'purchase_id': order.id, 'state': 'ordered'})
        return self.action_view_purchase()

    def action_view_purchase(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.purchase_id.id,
            'view_mode': 'form',
        }


class LubricantNeedRequestLine(models.Model):
    _name = 'lubricant.need.request.line'
    _description = "Ligne de fiche de besoin (lubrifiants)"

    request_id = fields.Many2one(
        'lubricant.need.request', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Produit', required=True,
        domain=[('purchase_ok', '=', True)])
    quantity = fields.Float(string='Quantité', default=1.0, required=True)
    uom_id = fields.Many2one(
        'uom.uom', string='Unité',
        related='product_id.uom_id', readonly=True)
    note = fields.Char(string='Remarque')
