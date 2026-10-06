from datetime import datetime, timedelta, timezone

from extensions import db
from models.alert import Alert
from models.user import User


ALERT_DEDUPLICATION_HOURS = 6
ALERT_RISK_LEVELS = {"High Risk", "Critical Risk"}


def create_heat_alert_if_needed(
    user_id,
    temperature,
    safe_temperature,
    risk_score,
    risk_level,
    location
):
    """Create one alert for an actionable heat condition, with a cooldown."""
    if safe_temperature is None:
        return None

    above_safe_temperature = temperature > safe_temperature
    high_heat_risk = risk_level in ALERT_RISK_LEVELS

    if not above_safe_temperature and not high_heat_risk:
        return None

    condition_key = (
        f"{risk_level}|above_safe={int(above_safe_temperature)}"
    )
    location = (location or "Unknown location")[:200]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(hours=ALERT_DEDUPLICATION_HOURS)

    # Serialize alert checks for this user so concurrent refreshes don't
    # both pass the cooldown query on PostgreSQL.
    User.query.filter_by(id=user_id).with_for_update().one()

    duplicate = (
        Alert.query
        .filter(
            Alert.user_id == user_id,
            Alert.condition_key == condition_key,
            Alert.location == location,
            Alert.created_at >= cutoff
        )
        .order_by(Alert.created_at.desc())
        .first()
    )
    if duplicate:
        return duplicate

    if above_safe_temperature and high_heat_risk:
        message = (
            f"{risk_level} heat risk ({risk_score}/100) at {location}. "
            f"Current temperature {temperature}°C exceeds your safe "
            f"temperature of {safe_temperature}°C."
        )
    elif high_heat_risk:
        message = (
            f"{risk_level} heat risk ({risk_score}/100) detected at "
            f"{location}. Current temperature is {temperature}°C."
        )
    else:
        level_description = (
            f"{risk_level} heat risk ({risk_score}/100)"
            if risk_score is not None
            else "Heat temperature threshold exceeded"
        )
        message = (
            f"{level_description} at {location}. Current temperature "
            f"{temperature}°C exceeds your safe temperature of "
            f"{safe_temperature}°C."
        )

    alert = Alert(
        user_id=user_id,
        temperature=temperature,
        threshold=safe_temperature,
        risk_score=risk_score,
        heat_level=risk_level,
        location=location,
        condition_key=condition_key,
        message=message,
        is_read=False,
        created_at=now
    )
    db.session.add(alert)
    db.session.commit()
    return alert
