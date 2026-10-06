from datetime import datetime

from extensions import db
from models.temperature import TemperatureRecord
from models.user import User


def save_temperature_record(
    user_id,
    location_id,
    weather,
    heat_risk
):
    """Persist one observation per user, location, and provider timestamp."""
    recorded_at_value = weather.get("time")
    try:
        recorded_at = datetime.fromisoformat(recorded_at_value)
    except (TypeError, ValueError):
        return None

    User.query.filter_by(id=user_id).with_for_update().one()

    existing_record = TemperatureRecord.query.filter_by(
        user_id=user_id,
        location_id=location_id,
        recorded_at=recorded_at
    ).first()
    if existing_record:
        return existing_record

    record = TemperatureRecord(
        user_id=user_id,
        location_id=location_id,
        temperature=weather["temperature"],
        humidity=weather.get("humidity"),
        feels_like=weather.get("feels_like"),
        risk_score=heat_risk["score"] if heat_risk else None,
        risk_level=heat_risk["level"] if heat_risk else None,
        recorded_at=recorded_at
    )
    db.session.add(record)
    db.session.commit()
    return record


def build_history_chart(records):
    """Add bounded chart heights while retaining only observed values."""
    chart_records = []
    for record in reversed(records):
        temperature_height = max(
            0,
            min(100, (record.temperature + 10) * (100 / 60))
        )
        risk_height = (
            max(0, min(100, record.risk_score))
            if record.risk_score is not None
            else 0
        )
        chart_records.append({
            "record": record,
            "temperature_height": round(temperature_height, 1),
            "risk_height": round(risk_height, 1)
        })
    return chart_records
