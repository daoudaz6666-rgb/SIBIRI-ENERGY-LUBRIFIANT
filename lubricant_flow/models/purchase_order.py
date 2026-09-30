from odoo import fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    import_file_ids = fields.One2many(
        'lubricant.import.file', 'purchase_id', string="Dossiers d'importation")

    def action_create_import_file(self):
        self.ensure_one()
        if self.state not in ('purchase', 'done'):
            raise UserError(_(
                "Confirmez la commande avant de créer le dossier d'importation."))
        active = self.import_file_ids.filtered(lambda f: f.phase != 'cancel')
        if active:
            raise UserError(_(
                "Cette commande a déjà un dossier d'importation : %s", active[0].name))
        import_file = self.env['lubricant.import.file'].create({
            'partner_id': self.partner_id.id,
            'purchase_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lubricant.import.file',
            'res_id': import_file.id,
            'view_mode': 'form',
        }
