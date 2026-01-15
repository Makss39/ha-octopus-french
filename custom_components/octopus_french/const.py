
"""Constants for the OEFR Energy integration."""

DOMAIN = "octopus_french"

CONF_ACCOUNT_NUMBER = "account_number"

# Ledger types
LEDGER_TYPE_ELECTRICITY = "FRA_ELECTRICITY_LEDGER"
LEDGER_TYPE_GAS = "FRA_GAS_LEDGER"
LEDGER_TYPE_POT = "POT_LEDGER"

# interval settings
UPDATE_INTERVAL = 1

# Configuration - Intervalles de mise à jour
DEFAULT_SCAN_INTERVAL = 60

# Token management
TOKEN_REFRESH_MARGIN = 300
TOKEN_AUTO_REFRESH_INTERVAL = 50 * 60

# Services
SERVICE_FORCE_UPDATE = "force_update"


# ---------------------------------------------------------------------------
# 🆕 AJOUT : Paramètre de fréquence des relevés
# ---------------------------------------------------------------------------

# Clé de configuration
CONF_READING_FREQUENCY = "reading_frequency"

# Valeurs possibles (conformes GraphQL Kraken)
FREQ_HOURLY = "HOUR_INTERVAL"     # relevés Linky heure par heure
FREQ_DAILY = "DAY_INTERVAL"       # consommation journalière
FREQ_WEEKLY = "WEEK_INTERVAL"     # (si supporté par ton contrat)
FREQ_MONTHLY = "MONTH_INTERVAL"   # (si supporté)

# Valeur par défaut (plus logique : horaire)
DEFAULT_READING_FREQUENCY = FREQ_HOURLY

# Liste des fréquences acceptées
SUPPORTED_READING_FREQUENCIES = [
    FREQ_HOURLY,
    FREQ_DAILY,
    # FREQ_WEEKLY,
    # FREQ_MONTHLY,
]
