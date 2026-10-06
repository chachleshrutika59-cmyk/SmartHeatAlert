from datetime import datetime, timezone
from extensions import db


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    location_name = db.Column(
        db.String(200),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    temperature_records = db.relationship(
        "TemperatureRecord",
        backref="location",
        lazy=True
    )