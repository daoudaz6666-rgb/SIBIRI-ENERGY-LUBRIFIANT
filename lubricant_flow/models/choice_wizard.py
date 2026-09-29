from odoo import models


class LubricantChoiceWizard(models.TransientModel):
    _name = 'lubricant.choice.wizard'
    _description = "Choix du circuit lubrifiants (achat ou vente)"

    def action_open_purchase(self):
        return self.env['ir.actions.actions']._for_xml_id(
            'lubricant_flow.lubricant_need_request_action')

    def action_open_sale(self):
        # Provisoire : sera remplacé par le circuit vente (étape 3)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ventes de lubrifiants',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'target': 'current',
        }
