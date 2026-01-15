
"""Binary sensors for OctopusFrench Energy integration."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any, Optional, Tuple, List

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    # ➕ nouvelles constantes exposées dans les attributs
    CONF_READING_FREQUENCY,
    DEFAULT_READING_FREQUENCY,
)
from .utils import parse_off_peak_hours


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OctopusFrench binary sensors."""
    store = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = store["coordinator"]

    # Récupérer la fréquence de relevé configurée (HOUR_INTERVAL / DAY_INTERVAL)
    reading_frequency: str = store.get(
        CONF_READING_FREQUENCY, DEFAULT_READING_FREQUENCY
    )

    # Valider la donnée du coordinator
    if not (data := coordinator.data):
        return
    if not isinstance(data, dict):
        return

    sensors: list[OctopusFrenchHcBinarySensor] = []

    # Détection des compteurs électricité avec plages HC
    supply_points = data.get("supply_points", {})
    electricity_points = supply_points.get("electricity", [])

    for meter in electricity_points:
        prm_id = meter.get("id")
        off_peak_label = meter.get("offPeakLabel")

        if not prm_id:
            continue

        if off_peak_label:
            off_peak_data = parse_off_peak_hours(off_peak_label)

            if off_peak_data.get("ranges"):
                # Attributs de base sur les HC
                electricity_attributes: dict[str, Any] = {
                    "off_peak_type": off_peak_data.get("type"),
                    "off_peak_total_hours": off_peak_data.get("total_hours"),
                    "off_peak_range_count": off_peak_data.get("range_count"),
                    # ➕ Exposer la fréquence de relevé configurée dans les attributs
                    "reading_frequency": reading_frequency,
                    # Info compteur utiles
                    "prm_id": prm_id,
                }

                # Ajouter chaque plage
                for i, time_range in enumerate(off_peak_data["ranges"], 1):
                    electricity_attributes[f"off_peak_range_{i}_start"] = time_range["start"]
                    electricity_attributes[f"off_peak_range_{i}_end"] = time_range["end"]
                    electricity_attributes[f"off_peak_range_{i}_duration"] = time_range["duration_hours"]

                # Créer le binaire HC pour ce PRM
                hc_sensor = OctopusFrenchHcBinarySensor(
                    coordinator=coordinator,
                    prm_id=prm_id,
                    electricity_sensor_attributes=electricity_attributes,
                    reading_frequency=reading_frequency,
                )
                sensors.append(hc_sensor)

    if sensors:
        async_add_entities(sensors)


class OctopusFrenchHcBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating if current time is in HC (Heures Creuses) period."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
