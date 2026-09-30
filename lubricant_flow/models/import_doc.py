from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .constants import PHASES


class LubricantImportDoc(models.Model):
    _name = 'lubricant.import.doc'
    _description = "Pièce du dossier d'importation"
    _order = 'sequence, id'

    file_id = fields.Many2one(
        'lubricant.import.file', string='Dossier',
        required=True, ondelete='cascade')
    type_id = fields.Many2one(
        'lubricant.import.doc.type', string='Pièce',
        required=True, ondelete='restrict')
    phase = fields.Selection(
        PHASES, string='Phase', related='type_id.phase',
        store=True, readonly=True)
    sequence = fields.Integer(
        related='type_id.sequence', store=True, readonly=True)
    mandatory = fields.Boolean(string='Obligatoire', default=True)
    original = fields.Selection(
        [('original', 'Original'), ('copy', 'Copie')],
        string='Original / copie', default='original')
    number = fields.Char(string='Numéro / référence')
    date = fields.Date(string='Date')
    received = fields.Boolean(string='Reçue')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'lubricant_import_doc_attachment_rel',
        'doc_id', 'attachment_id', string='Scan / pièces jointes')
    note = fields.Text(string='Remarques')

    @api.onchange('type_id')
    def _onchange_type_id(self):
        for rec in self:
            rec.mandatory = rec.type_id.mandatory

    @api.constrains('received', 'number', 'attachment_ids')
    def _check_received(self):
        for rec in self:
            if rec.received and not (rec.number or rec.attachment_ids):
                raise ValidationError(_(
                    "Pour marquer la pièce « %s » comme reçue, renseignez son numéro ou joignez le scan.",
                    rec.type_id.name))


class LubricantImportContainer(models.Model):
    _name = 'lubricant.import.container'
    _description = "Conteneur du dossier d'importation"

    file_id = fields.Many2one(
        'lubricant.import.file', string='Dossier',
        required=True, ondelete='cascade')
    name = fields.Char(string='N° de conteneur', required=True)
    size = fields.Selection(
        [('20', '20 pieds'), ('40', '40 pieds')],
        string='Taille', default='20', required=True)
    weight = fields.Float(string='Poids (kg)')
    note = fields.Char(string='Remarque')
