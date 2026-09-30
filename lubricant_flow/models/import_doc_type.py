from odoo import fields, models

from .constants import PHASES


class LubricantImportDocType(models.Model):
    _name = 'lubricant.import.doc.type'
    _description = "Type de pièce du dossier d'importation"
    _order = 'sequence, id'

    name = fields.Char(string='Pièce', required=True)
    phase = fields.Selection(PHASES, string='Phase', required=True)
    mandatory = fields.Boolean(string='Obligatoire', default=True)
    issuer = fields.Char(string='Émetteur')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    note = fields.Text(string='Remarques')
