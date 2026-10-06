from flask import Blueprint, redirect, render_template, session, url_for

from models.location import Location
from models.temperature import TemperatureRecord
from services.history_service import build_history_chart


history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history():
    if not session.get("logged_in") or not session.get("user_id"):
        return redirect(url_for("auth.login"))

    records = (
        TemperatureRecord.query
        .join(Location, TemperatureRecord.location_id == Location.id)
        .filter(
            TemperatureRecord.user_id == session["user_id"],
            Location.user_id == session["user_id"]
        )
        .order_by(TemperatureRecord.recorded_at.desc())
        .limit(100)
        .all()
    )
    chart_records = build_history_chart(records)

    return render_template(
        "history.html",
        records=records,
        chart_records=chart_records
    )
