import base64
import logging

from odoo.tools.misc import file_open

_logger = logging.getLogger(__name__)

NOM = "DZsolar"
TEL = "+226 55 21 98 81"
EMAIL = "contact@dzsolar.bf"
RUE = "Avenue Kwame Nkrumah"
AMBRE = "#F5A623"
NOIR = "#111111"
RULE_NAME = "Commande web -> Opportunité gagnée"

# (code modèle, nom, catégorie, prix de vente FCFA, coût FCFA, stock)
PRODUITS = [
    ('GK-580M', 'Panneau solaire monocristallin 580W - GK-580M', 'Panneaux solaires', 110000, 82000, 200),
    ('IVEM4024-II', 'Onduleur off-grid 4 kW 24V - IVEM4024-II', 'Onduleurs', 450000, 340000, 25),
    ('IVEM5048', 'Onduleur off-grid 5 kW 48V - IVEM5048', 'Onduleurs', 520000, 395000, 25),
    ('IVEM6048-II', 'Onduleur off-grid 6 kW 48V - IVEM6048-II', 'Onduleurs', 620000, 470000, 20),
    ('IVEM12048-II', 'Onduleur off-grid 12 kW 48V - IVEM12048-II', 'Onduleurs', 1250000, 950000, 10),
    ('IVGM5-8KW', 'Onduleur hybride 5 à 8 kW - IVGM5-8KW', 'Onduleurs', 1100000, 840000, 10),
    ('IVGM12-16K', 'Onduleur hybride 12 à 16 kW - IVGM12-16K', 'Onduleurs', 2200000, 1700000, 6),
    ('FLA24300', 'Batterie lithium 24V 300Ah - FLA24300', 'Batteries lithium', 750000, 570000, 15),
    ('LPBF48200-H', 'Batterie lithium 48V 200Ah - LPBF48200-H', 'Batteries lithium', 1650000, 1260000, 12),
    ('FLA48300', 'Batterie lithium 48V 300Ah - FLA48300', 'Batteries lithium', 2400000, 1850000, 8),
    ('LPBF48300-II', 'Batterie lithium 48V 300Ah - LPBF48300-II', 'Batteries lithium', 2350000, 1800000, 8),
    ('LPBF48350', 'Batterie lithium 48V 350Ah - LPBF48350', 'Batteries lithium', 2700000, 2080000, 6),
    ('FLA48500TG2', 'Batterie lithium 48V 500Ah - FLA48500TG2', 'Batteries lithium', 3600000, 2780000, 4),
    ('LAMPADAIRE-AIO', 'Lampadaire solaire tout-en-un', 'Éclairage solaire', 85000, 60000, 60),
]

RULE_CODE = """
for order in records:
    if not order.opportunity_id:
        lead = env['crm.lead'].sudo().create({
            'name': 'Commande web %s' % order.name,
            'type': 'opportunity',
            'partner_id': order.partner_id.id,
            'expected_revenue': order.amount_untaxed,
            'team_id': order.team_id.id,
            'user_id': order.user_id.id or env.ref('base.user_admin').id,
        })
        lead.action_set_won()
        order.sudo().write({'opportunity_id': lead.id})
"""


def _img(name):
    with file_open('dzsolar_demo/static/img/' + name, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def _step(env, label, func):
    """Exécute une étape ; en cas d'erreur, la journalise sans bloquer l'installation."""
    try:
        with env.cr.savepoint():
            func()
        _logger.info("DZsolar : %s OK", label)
    except Exception:
        _logger.exception("DZsolar : échec de l'étape %s", label)


def post_init_hook(env):
    admin = env.ref('base.user_admin')
    xof = env.ref('base.XOF')
    xof.active = True

    # 1) Société DZsolar neuve en FCFA, plan SYSCOHADA Burkina, sans données de démonstration
    company = env['res.company'].search([('name', '=', NOM)], limit=1)
    if not company:
        company = env['res.company'].create({'name': NOM, 'currency_id': xof.id, 'country_id': env.ref('base.bf').id})
    if not company.chart_template:
        env['account.chart.template'].with_company(company).try_loading('bf', company=company, install_demo=False)
    logo = _img('logo.png')
    company.write({'street': RUE, 'city': 'Ouagadougou', 'phone': TEL, 'email': EMAIL, 'logo': logo,
                   'sale_invoice_policy': 'order', 'sale_automatic_invoice': True})
    # L'administrateur ne voit plus que DZsolar (plus de « My Company » ni « BF Company »)
    admin.write({'company_ids': [(6, 0, company.ids)], 'company_id': company.id})
    env = env(context=dict(env.context, allowed_company_ids=[company.id]))

    # 2) Entrepôt
    wh = env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
    if not wh:
        wh = env['stock.warehouse'].create({'name': 'Entrepôt Ouagadougou', 'code': 'OUA',
                                            'company_id': company.id, 'partner_id': company.partner_id.id})

    # 3) Équipe commerciale
    team = env['crm.team'].search([('name', '=', 'Ventes Web'), ('company_id', '=', company.id)], limit=1)
    if not team:
        team = env['crm.team'].create({'name': 'Ventes Web', 'company_id': company.id,
                                       'user_id': admin.id, 'use_opportunities': True})

    # 4) Site web, listes de prix
    website = env['website'].search([], limit=1)
    old = env['product.pricelist'].with_context(active_test=False).search([('name', '!=', 'Tarif public FCFA')])
    old.filtered(lambda p: p.website_id == website or (not p.company_id and p.website_id)).write({'active': False})
    old.filtered(lambda p: not p.company_id and not p.website_id).write({'company_id': env.ref('base.main_company').id})
    website.write({'name': NOM, 'company_id': company.id, 'salesteam_id': team.id,
                   'salesperson_id': admin.id, 'logo': logo, 'configurator_done': True})
    if not env['product.pricelist'].search([('name', '=', 'Tarif public FCFA')]):
        env['product.pricelist'].create({'name': 'Tarif public FCFA', 'currency_id': xof.id, 'company_id': company.id,
                                         'website_id': website.id, 'sequence': 1, 'selectable': True})

    # 5) Paiements : virement + paiement en ligne de démonstration
    def payments():
        Provider = env['payment.provider']
        tr = Provider.search([('code', '=', 'custom'), ('custom_mode', '=', 'wire_transfer'),
                              ('company_id', '=', company.id)], limit=1)
        if not tr:
            tr = env.ref('payment.payment_provider_transfer').copy({'company_id': company.id})
        tr.write({'is_live': True, 'is_published': True})
        demo = Provider.search([('code', '=', 'demo'), ('company_id', '=', company.id)], limit=1)
        if not demo:
            demo = env.ref('payment.payment_provider_demo').copy({'company_id': company.id})
        demo.write({'name': 'Paiement en ligne', 'is_published': True,
                    'allow_express_checkout': False, 'allow_tokenization': False})
        with file_open('payment/static/img/card.png', 'rb') as f:
            card = base64.b64encode(f.read()).decode()
        method = env.ref('payment_demo.payment_method_demo')
        for lang in ('en_US', 'fr_FR'):
            method.with_context(lang=lang).write({'name': 'Carte bancaire / Mobile Money'})
        method.image = card
    _step(env, "paiements", payments)

    # 6) Règle CRM : commande web -> opportunité gagnée
    def rule():
        if env['base.automation'].search([('name', '=', RULE_NAME)]):
            return
        model = env.ref('sale.model_sale_order')
        env['base.automation'].create({
            'name': RULE_NAME, 'model_id': model.id, 'trigger': 'on_create_or_write',
            'trigger_field_ids': [(6, 0, [env.ref('sale.field_sale_order__state').id])],
            'filter_domain': "[('state', 'in', ('sent', 'sale')), ('website_id', '!=', False)]",
            'action_server_ids': [(0, 0, {'name': RULE_NAME, 'model_id': model.id, 'state': 'code', 'code': RULE_CODE})],
        })
    _step(env, "règle CRM", rule)

    # 7) Catalogue Felicity Solar
    def produits():
        tax = company.account_sale_tax_id
        Categ = env['product.public.category']
        codes = []
        for code, name, cat, prix, cout, qte in PRODUITS:
            codes.append(code)
            c = Categ.search([('name', '=', cat)], limit=1) or Categ.create({'name': cat})
            t = env['product.template'].search([('default_code', '=', code)], limit=1)
            vals = {'name': name, 'list_price': prix, 'standard_price': cout,
                    'public_categ_ids': [(6, 0, c.ids)], 'image_1920': _img(code + '.jpg'),
                    'description_sale': 'Felicity Solar - ' + name}
            if not t:
                vals.update({'default_code': code, 'company_id': company.id, 'type': 'consu',
                             'is_storable': True, 'sale_ok': True, 'taxes_id': [(6, 0, tax.ids)]})
                t = env['product.template'].create(vals)
                env['stock.quant'].with_context(inventory_mode=True).create({
                    'product_id': t.product_variant_id.id, 'location_id': wh.lot_stock_id.id,
                    'inventory_quantity': qte}).action_apply_inventory()
            else:
                t.write(vals)
            t.is_published = True
        env['product.template'].sudo().search([('is_published', '=', True),
                                               ('default_code', 'not in', codes)]).write({'is_published': False})
    _step(env, "catalogue", produits)

    # 8) Archiver les opportunités fictives des autres sociétés
    def nettoyage():
        env['crm.lead'].sudo().search([('company_id', '!=', company.id)]).write({'active': False})
    _step(env, "nettoyage CRM", nettoyage)

    # 9) Page d'accueil
    _step(env, "page d'accueil", lambda: _homepage(env, company, website))


def _fcfa(v):
    return '{:,.0f}'.format(v).replace(',', '&#160;') + '&#160;FCFA'


def _homepage(env, company, website):
    env = env(context=dict(env.context, website_id=website.id))
    cartes = ''
    for code in ['GK-580M', 'IVEM6048-II', 'IVGM5-8KW', 'LPBF48200-H', 'FLA48300', 'LAMPADAIRE-AIO']:
        t = env['product.template'].search([('default_code', '=', code)], limit=1)
        if not t:
            continue
        cartes += f'''
          <div class="col-6 col-lg-4 mb-4">
            <a href="{t.website_url}" class="text-decoration-none">
              <div class="card h-100 border-0 shadow-sm">
                <img src="/web/image/product.template/{t.id}/image_512" class="card-img-top p-3" style="height:220px;object-fit:contain;" alt="{t.name}"/>
                <div class="card-body text-center">
                  <h6 class="card-title" style="color:{NOIR};">{t.name}</h6>
                  <p class="fw-bold mb-0" style="color:{AMBRE};">{_fcfa(t.list_price)} HT</p>
                </div>
              </div>
            </a>
          </div>'''
    blocs = ''
    for nom, desc in [('Panneaux solaires', 'Modules monocristallins haut rendement'),
                      ('Onduleurs', 'Off-grid et hybrides de 4 à 16 kW'),
                      ('Batteries lithium', 'Stockage LiFePO4 longue durée'),
                      ('Éclairage solaire', 'Lampadaires autonomes tout-en-un')]:
        blocs += f'''
          <div class="col-6 col-lg-3 mb-4">
            <a href="/shop" class="text-decoration-none">
              <div class="h-100 p-4 rounded-3" style="background:#1c1c1c;border:1px solid #333;">
                <h5 style="color:{AMBRE};">{nom}</h5>
                <p class="mb-0" style="color:#cccccc;">{desc}</p>
              </div>
            </a>
          </div>'''
    arch = f'''<t name="Home" t-name="website.homepage">
  <t t-call="website.layout" pageName.f="homepage">
    <div id="wrap" class="oe_structure">
      <section style="background:{NOIR};color:#ffffff;" class="pt-5 pb-5">
        <div class="container py-5">
          <div class="row align-items-center">
            <div class="col-lg-7">
              <p class="text-uppercase fw-bold mb-2" style="color:{AMBRE};letter-spacing:2px;">Distributeur Felicity Solar à Ouagadougou</p>
              <h1 class="display-4 fw-bold mb-4" style="color:#ffffff;">L'énergie du soleil, <span style="color:{AMBRE};">sans coupure</span>.</h1>
              <p class="lead mb-4" style="color:#dddddd;">Panneaux, onduleurs et batteries lithium pour la maison, le commerce et l'industrie. Livraison rapide à Ouaga et installation par nos techniciens.</p>
              <a href="/shop" class="btn btn-lg me-2 mb-2" style="background:{AMBRE};color:{NOIR};font-weight:bold;">Acheter en ligne</a>
              <a href="/shop" class="btn btn-lg btn-outline-light mb-2">Voir le catalogue</a>
              <p class="mt-3 mb-0" style="color:#bbbbbb;">&#128274; Paiement sécurisé sur le site : carte bancaire ou Mobile Money</p>
            </div>
            <div class="col-lg-5 text-center mt-4 mt-lg-0">
              <img src="/web/image/website/{website.id}/logo" alt="DZsolar" style="max-width:100%;background:#ffffff;border-radius:16px;padding:24px;"/>
            </div>
          </div>
        </div>
      </section>
      <section style="background:{NOIR};" class="pb-5">
        <div class="container">
          <h2 class="mb-4" style="color:#ffffff;">Nos gammes</h2>
          <div class="row">{blocs}
          </div>
        </div>
      </section>
      <section class="py-5" style="background:#f7f7f7;">
        <div class="container">
          <h2 class="mb-1" style="color:{NOIR};">Produits vedettes</h2>
          <p class="mb-4 text-muted">Matériel Felicity Solar disponible en stock à Ouagadougou</p>
          <div class="row">{cartes}
          </div>
          <div class="text-center"><a href="/shop" class="btn btn-dark btn-lg">Tout le catalogue</a></div>
        </div>
      </section>
      <section class="py-5">
        <div class="container">
          <h2 class="mb-4 text-center" style="color:{NOIR};">Pourquoi choisir DZsolar ?</h2>
          <div class="row text-center">
            <div class="col-6 col-lg-3 mb-4"><h1 style="color:{AMBRE};">&#9728;</h1><h5>Matériel certifié</h5><p class="text-muted">Distributeur de la marque Felicity Solar</p></div>
            <div class="col-6 col-lg-3 mb-4"><h1 style="color:{AMBRE};">&#128179;</h1><h5>Paiement en ligne</h5><p class="text-muted">Carte bancaire ou Mobile Money, directement sur le site</p></div>
            <div class="col-6 col-lg-3 mb-4"><h1 style="color:{AMBRE};">&#128666;</h1><h5>Livraison rapide</h5><p class="text-muted">Partout à Ouagadougou</p></div>
            <div class="col-6 col-lg-3 mb-4"><h1 style="color:{AMBRE};">&#128295;</h1><h5>Installation et SAV</h5><p class="text-muted">Techniciens qualifiés et suivi après-vente</p></div>
          </div>
        </div>
      </section>
      <section class="py-5" style="background:{AMBRE};">
        <div class="container">
          <div class="row align-items-center">
            <div class="col-lg-8" style="color:{NOIR};">
              <h3 class="fw-bold">Commandez et payez en ligne, nous livrons à Ouaga</h3>
              <p class="mb-1">&#128222; {TEL}</p>
              <p class="mb-1">&#128339; Ouvert du lundi au vendredi, de 8h à 19h</p>
              <p class="mb-0">&#128205; {RUE}, Ouagadougou, Burkina Faso</p>
            </div>
            <div class="col-lg-4 text-lg-end mt-3 mt-lg-0">
              <a href="/shop" class="btn btn-lg" style="background:{NOIR};color:#ffffff;">Commander maintenant</a>
            </div>
          </div>
        </div>
      </section>
    </div>
  </t>
</t>'''
    page = env['website.page'].search([('url', '=', '/'), ('website_id', 'in', [website.id, False])],
                                      order='website_id', limit=1)
    view = page.view_id if page else env.ref('website.homepage')
    view.with_context(website_id=website.id).write({'arch': arch})
