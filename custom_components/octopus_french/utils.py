
"""Helper functions for OctopusFrench Energy."""

from datetime import datetime, time
import logging
import re
from typing import Any, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1) Parse des heures creuses / heures pleines (HC / HP)
# ---------------------------------------------------------------------------

def parse_off_peak_hours(off_peak_label: str | None) -> Dict[str, Any]:
    """
    Parse an Octopus off-peak label (e.g. "HC 00H30-06H30 14H30-16H30")
    and return a normalized structure.

    Returns:
        {
            "type": "HC",
            "ranges": [
                {
                    "start": "00:30",
                    "end": "06:30",
                    "start_time": time(0,30),
                    "end_time": time(6,30),
                    "start_minutes": 30,
                    "end_minutes": 390,
                    "duration_minutes": 360,
                    "duration_hours": 6.0,
                    "cross_midnight": False
                },
                ...
            ],
            "total_hours": 12.5,
            "range_count": 2
        }
    """
    result: Dict[str, Any] = {
        "type": None,
        "ranges": [],
        "total_hours": 0.0,
        "range_count": 0,
    }

    if not off_peak_label:
        return result

    try:
        # Extract HC/HP type
        if type_match := re.match(r"^([A-Z]+)", off_peak_label):
            result["type"] = type_match.group(1)

        # Extract ranges XXHYY-ZZHWW
        time_pattern = r"(\d+)H(\d+)-(\d+)H(\d+)"
        matches = re.findall(time_pattern, off_peak_label)

        total_minutes = 0

        for match in matches:
            start_hour, start_min, end_hour, end_min = map(int, match)

            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min

            crosses_midnight = end_minutes <= start_minutes

            duration_minutes = (
                end_minutes - start_minutes
                if not crosses_midnight
                else (24 * 60 - start_minutes) + end_minutes
            )

            total_minutes += duration_minutes

            result["ranges"].append(
                {
                    "start": f"{start_hour:02d}:{start_min:02d}",
                    "end": f"{end_hour:02d}:{end_min:02d}",
                    "start_time": time(start_hour, start_min),
                    "end_time": time(end_hour, end_min),
                    "start_minutes": start_minutes,
                    "end_minutes": end_minutes,
                    "duration_minutes": duration_minutes,
                    "duration_hours": round(duration_minutes / 60, 2),
                    "cross_midnight": crosses_midnight,
                }
            )

        result["total_hours"] = round(total_minutes / 60, 2)
        result["range_count"] = len(result["ranges"])

    except Exception as err:
        _LOGGER.warning("Failed to parse off-peak hours '%s': %s", off_peak_label, err)

    return result


# ---------------------------------------------------------------------------
# 2) Convertisseur basique ISO → YYYY-MM-DD
# ---------------------------------------------------------------------------

def convert_sensor_date(date_string: Optional[str]) -> Optional[str]:
    """Convert ISO8601 → YYYY-MM-DD."""
    if not date_string:
        return None

    try:
        dt = datetime.fromisoformat(date_string)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 3) Ajout: labels humain pour reading_frequency
# ---------------------------------------------------------------------------

def format_frequency_label(freq: str) -> str:
    """
    Convert internal frequency names to human-readable labels.
    Used for attributes of sensors.
    """
    mapping = {
        "HOUR_INTERVAL": "Hourly (72-hour window)",
        "DAY_INTERVAL": "Daily (31-day window)",
        "WEEK_INTERVAL": "Weekly",
        "MONTH_INTERVAL": "Monthly",
    }
    return mapping.get(freq, freq)
