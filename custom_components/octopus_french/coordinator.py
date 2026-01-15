
"""Data update coordinator for Octopus French Energy."""

from __future__ import annotations

from contextlib import suppress
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_SCAN_INTERVAL,
    CONF_READING_FREQUENCY,
    DEFAULT_READING_FREQUENCY,
    FREQ_HOURLY,
    FREQ_DAILY,
)

if TYPE_CHECKING:
    from .octopus_french import OctopusFrenchApiClient

_LOGGER = logging.getLogger(__name__)


class OctopusFrenchDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: OctopusFrenchApiClient,
        account_number: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        reading_frequency: str = DEFAULT_READING_FREQUENCY,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Octopus French Energy",
            update_interval=timedelta(minutes=scan_interval),
        )
        self.api_client = api_client
        self.account_number = account_number
        self.reading_frequency = reading_frequency

    # ---------------------------------------------------------------------
    # 🆕 Calcule dynamiquement la fenêtre temporelle (72h en horaire)
    # ---------------------------------------------------------------------
    def _compute_date_window(self) -> tuple[str, str]:
        now = dt_util.now()

        if self.reading_frequency == FREQ_HOURLY:
            # Étendu de 48h → 72h comme demandé
            start = now - timedelta(hours=72)

        elif self.reading_frequency == FREQ_DAILY:
            # 31 jours glissants
            start = now - timedelta(days=31)

        else:
            # Fallback
            start = now - timedelta(days=7)

        return start.isoformat(), now.isoformat()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            return await self._fetch_all_data()
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _fetch_all_data(self) -> dict[str, Any]:
        """Fetch all data from API."""
        account_data = await self.api_client.get_account_data(self.account_number)

        # Validation des données essentielles
        account_id = account_data.get("account_id")
        account_number = account_data.get("account_number")

        if not account_id:
            raise UpdateFailed("Missing account_id in API response")
        if not account_number:
            raise UpdateFailed("Missing account_number in API response")

        # Filtrer les compteurs résiliés
        account_data["supply_points"]["electricity"] = [
            sp
            for sp in account_data["supply_points"]["electricity"]
            if not (
                sp.get("distributorStatus") == "RESIL"
                and sp.get("poweredStatus") == "LIMI"
            )
        ]

        # Récupérer les IDs des compteurs
        electricity_supply_points = account_data.get("supply_points", {}).get(
            "electricity", []
        )
        electricity_meter_id = (
            electricity_supply_points[0]["id"] if electricity_supply_points else None
        )
        gas_supply_points = account_data.get("supply_points", {}).get("gas", [])
        gas_meter_id = gas_supply_points[0]["id"] if gas_supply_points else None

        # ---------------------------------------------------------------------
        # 🆕 Fenêtre temporelle dynamique
        # ---------------------------------------------------------------------
        elec_start, elec_end = self._compute_date_window()

        # ---------------------------------------------------------------------
        # Récupération des données électricité (fréquence dynamique)
        # ---------------------------------------------------------------------
        electricity_readings = []
        elec_index = None

        if electricity_meter_id:
            electricity_readings = await self.api_client.get_energy_readings(
                account_id,
                elec_start,
                elec_end,
                electricity_meter_id,
                utility_type="electricity",
                reading_frequency=self.reading_frequency,
                reading_quality="ACTUAL",
                first=500,
            )

            elec_index = await self.api_client.get_electricity_index(
