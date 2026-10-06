from datetime import datetime, timezone
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    mobile_number = db.Column(
        db.String(15),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=True
    )

    safe_temperature = db.Column(
        db.Float,
        nullable=True
    )

    age_group = db.Column(
        db.String(20),
        nullable=True
    )

    activity_level = db.Column(
        db.String(50),
        nullable=True
    )

    outdoor_exposure = db.Column(
        db.String(30),
        nullable=True
    )

    notification_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.true()
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    locations = db.relationship(
        "Location",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    temperature_records = db.relationship(
        "TemperatureRecord",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    alerts = db.relationship(
        "Alert",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )