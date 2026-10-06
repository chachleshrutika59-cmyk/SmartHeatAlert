from datetime import datetime
from extensions import db


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    temperature = db.Column(
        db.Float,
        nullable=False
    )

    threshold = db.Column(
        db.Float,
        nullable=False
    )

    heat_level = db.Column(
        db.String(50),
        nullable=False
    )

    message = db.Column(
        db.String(500),
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )