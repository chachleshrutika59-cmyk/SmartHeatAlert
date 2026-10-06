from datetime import datetime
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

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
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