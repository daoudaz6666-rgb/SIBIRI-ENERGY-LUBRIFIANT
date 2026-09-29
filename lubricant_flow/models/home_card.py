from odoo import fields, models


class LubricantHomeCard(models.Model):
    _name = 'lubricant.home.card'
    _description = "Carte de la page d'accueil Lubrifiants"
    _order = 'sequence, id'

    name = fields.Char(string='Titre', required=True)
    description = fields.Char(string='Description')
    icon = fields.Char(string='Icône (Font Awesome)', default='fa-cube')
    circuit = fields.Selection([
        ('purchase', 'Achat'),
        ('sale', 'Vente'),
    ], string='Circuit', required=True)
    sequence = fields.Integer(default=10)

    def action_open(self):
        self.ensure_one()
        xml_id = ('lubricant_flow.lubricant_need_request_action'
                  if self.circuit == 'purchase'
                  else 'lubricant_flow.lubricant_sale_order_action')
        return self.env['ir.actions.actions']._for_xml_id(xml_id)
