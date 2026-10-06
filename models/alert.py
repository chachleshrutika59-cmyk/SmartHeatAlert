from datetime import datetime, timezone
from extensions import db


class Alert(db.Model):
    __tablename__ = "alerts"
    __table_args__ = (
        db.Index("ix_alerts_user_created_at", "user_id", "created_at"),
    )

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

    risk_score = db.Column(
        db.Float,
        nullable=True
    )

    heat_level = db.Column(
        db.String(50),
        nullable=False
    )

    location = db.Column(
        db.String(200),
        nullable=True
    )

    condition_key = db.Column(
        db.String(120),
        nullable=True
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
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )