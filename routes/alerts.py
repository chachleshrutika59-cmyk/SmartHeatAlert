from flask import Blueprint, abort, flash, redirect, render_template, session, url_for

from extensions import db
from models.alert import Alert


alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/alerts")
def alerts():
    if not session.get("logged_in") or not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    user_alerts = (
        Alert.query
        .filter_by(user_id=user_id)
        .order_by(Alert.created_at.desc())
        .all()
    )

    return render_template(
        "alerts.html",
        alerts=user_alerts,
        unread_count=sum(not alert.is_read for alert in user_alerts)
    )


@alerts_bp.route("/alerts/<int:alert_id>/read", methods=["POST"])
def mark_alert_read(alert_id):
    if not session.get("logged_in") or not session.get("user_id"):
        return redirect(url_for("auth.login"))

    alert = Alert.query.filter_by(
        id=alert_id,
        user_id=session["user_id"]
    ).first()
    if alert is None:
        abort(404)

    alert.is_read = True
    db.session.commit()
    flash("Alert marked as read.", "success")
    return redirect(url_for("alerts.alerts"))
