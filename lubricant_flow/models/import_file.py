from odoo import Command, api, fields, models, _
from odoo.exceptions import UserError

from .constants import FILE_PHASES, PHASE_KEYS, PHASE_LABELS


class LubricantImportFile(models.Model):
    _name = 'lubricant.import.file'
    _description = "Dossier d'importation (lubrifiants)"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Référence', default='Nouveau', copy=False,
        readonly=True, tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string='Fournisseur', required=True, tracking=True)
    purchase_id = fields.Many2one(
        'purchase.order', string="Commande d'achat", copy=False,
        ondelete='restrict', tracking=True)
    currency_id = fields.Many2one(
        related='purchase_id.currency_id', string='Devise')
    amount_total = fields.Monetary(
        related='purchase_id.amount_total', currency_field='currency_id',
        string='Montant')
    incoterm = fields.Char(string='Incoterm', default='FOB Anvers')
    phase = fields.Selection(
        FILE_PHASES, string='Phase', default='commande',
        required=True, copy=False, tracking=True)
    bl_number = fields.Char(string='N° de connaissement', tracking=True)
    ship_date = fields.Date(string="Date d'expédition")
    note = fields.Text(string='Remarques')
    container_ids = fields.One2many(
        'lubricant.import.container', 'file_id', string='Conteneurs')
    doc_ids = fields.One2many(
        'lubricant.import.doc', 'file_id', string='Pièces', copy=False)

    doc_required_count = fields.Integer(
        string='Pièces obligatoires', compute='_compute_progress')
    doc_received_count = fields.Integer(
        string='Pièces reçues', compute='_compute_progress')
    progress = fields.Float(
        string='Avancement (%)', compute='_compute_progress')
    missing_text = fields.Char(
        string='Pièces manquantes (phase courante)',
        compute='_compute_progress')

    # ------------------------------------------------------------------
    @api.depends('phase', 'doc_ids.mandatory', 'doc_ids.received', 'doc_ids.phase')
    def _compute_progress(self):
        for rec in self:
            required = rec.doc_ids.filtered('mandatory')
            received = required.filtered('received')
            rec.doc_required_count = len(required)
            rec.doc_received_count = len(received)
            rec.progress = (len(received) * 100.0 / len(required)) if required else 0.0
            current = required.filtered(
                lambda d: d.phase == rec.phase and not d.received)
            rec.missing_text = (
                _("Pièces manquantes pour cette phase : ")
                + ", ".join(current.mapped('type_id.name'))
            ) if current else False

    @api.onchange('purchase_id')
    def _onchange_purchase_id(self):
        for rec in self:
            if rec.purchase_id:
                rec.partner_id = rec.purchase_id.partner_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'lubricant.import.file') or 'Nouveau'
        files = super().create(vals_list)
        files.filtered(lambda f: not f.doc_ids)._generate_docs()
        return files

    def _generate_docs(self):
        types = self.env['lubricant.import.doc.type'].search([])
        for rec in self:
            present = rec.doc_ids.mapped('type_id')
            rec.write({'doc_ids': [
                Command.create({'type_id': t.id, 'mandatory': t.mandatory})
                for t in types if t not in present
            ]})

    # ------------------------------------------------------------------
    def _check_phase_docs(self):
        self.ensure_one()
        missing = self.doc_ids.filtered(
            lambda d: d.phase == self.phase and d.mandatory and not d.received)
        if missing:
            raise UserError(
                _("Pièces obligatoires manquantes pour cette phase :")
                + "\n- " + "\n- ".join(missing.mapped('type_id.name')))

    def action_sync_docs(self):
        self._generate_docs()
        return True

    def action_next_phase(self):
        for rec in self:
            if rec.phase not in PHASE_KEYS:
                raise UserError(_("Ce dossier est clôturé ou annulé."))
            if rec.phase == PHASE_KEYS[-1]:
                raise UserError(_("Dernière phase : utilisez le bouton Clôturer."))
            if rec.phase == 'commande':
                if not rec.purchase_id:
                    raise UserError(_("Rattachez le dossier à une commande d'achat."))
                if rec.purchase_id.state not in ('purchase', 'done'):
                    raise UserError(_("La commande d'achat doit être confirmée."))
            if rec.phase == 'expedition':
                if not rec.bl_number:
                    raise UserError(_("Renseignez le numéro de connaissement."))
                if not rec.container_ids:
                    raise UserError(_("Saisissez au moins un conteneur."))
            rec._check_phase_docs()
            rec.phase = PHASE_KEYS[PHASE_KEYS.index(rec.phase) + 1]
        return True

    def action_previous_phase(self):
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise UserError(_(
                "Seul un responsable des achats peut revenir à la phase précédente."))
        for rec in self:
            if rec.phase not in PHASE_KEYS or rec.phase == PHASE_KEYS[0]:
                raise UserError(_("Impossible de revenir en arrière depuis cette phase."))
            rec.phase = PHASE_KEYS[PHASE_KEYS.index(rec.phase) - 1]
        return True

    def action_close(self):
        for rec in self:
            if rec.phase != 'transmission':
                raise UserError(_(
                    "Le dossier doit être en phase 9 (transmission) pour être clôturé."))
            missing = rec.doc_ids.filtered(lambda d: d.mandatory and not d.received)
            if missing:
                lines = ["%s (%s)" % (d.type_id.name, PHASE_LABELS.get(d.phase, ''))
                         for d in missing]
                raise UserError(
                    _("Clôture impossible, pièces obligatoires manquantes :")
                    + "\n- " + "\n- ".join(lines))
            rec.phase = 'closed'
        return True

    def action_cancel(self):
        for rec in self:
            if rec.phase == 'closed':
                raise UserError(_("Un dossier clôturé ne peut pas être annulé."))
        self.write({'phase': 'cancel'})
        return True

    def action_reset(self):
        self.filtered(lambda r: r.phase == 'cancel').write({'phase': 'commande'})
        return True
