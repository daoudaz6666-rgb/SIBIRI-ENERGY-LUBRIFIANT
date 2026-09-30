PHASES = [
    ('commande', '1. Commande'),
    ('autorisations', '2. Autorisations'),
    ('paiement', '3. Paiement'),
    ('assurance', '4. Assurance'),
    ('expedition', '5. Origine et expédition'),
    ('transit', '6. Transit'),
    ('douane', '7. Dédouanement'),
    ('frais', '8. Frais locaux'),
    ('transmission', '9. Transmission'),
]
FILE_PHASES = PHASES + [('closed', 'Clôturé'), ('cancel', 'Annulé')]
PHASE_KEYS = [key for key, label in PHASES]
PHASE_LABELS = dict(PHASES)
