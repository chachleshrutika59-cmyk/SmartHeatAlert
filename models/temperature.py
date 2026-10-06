from datetime import datetime, timezone
from extensions import db


class TemperatureRecord(db.Model):
    __tablename__ = "temperature_records"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.id"),
        nullable=False
    )

    temperature = db.Column(
        db.Float,
        nullable=False
    )

    feels_like = db.Column(
        db.Float,
        nullable=True
    )

    humidity = db.Column(
        db.Float,
        nullable=True
    )

    risk_score = db.Column(
        db.Float,
        nullable=True
    )

    risk_level = db.Column(
        db.String(50),
        nullable=True
    )

    recorded_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )