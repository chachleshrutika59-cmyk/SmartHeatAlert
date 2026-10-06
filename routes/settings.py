import math

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from extensions import db
from models.user import User


settings_bp = Blueprint("settings", __name__)

AGE_GROUPS = {
    "under_18": "Under 18",
    "18_29": "18–29",
    "30_44": "30–44",
    "45_59": "45–59",
    "60_plus": "60+"
}

ACTIVITY_LEVELS = (
    "Indoor / Low Activity",
    "Normal Activity",
    "Outdoor Activity",
    "Heavy Outdoor Work"
)

OUTDOOR_EXPOSURES = (
    "Less than 1 hour",
    "1–3 hours",
    "3–6 hours",
    "More than 6 hours"
)

DEFAULT_SAFE_TEMPERATURE = 40.0
MIN_SAFE_TEMPERATURE = 0.0
MAX_SAFE_TEMPERATURE = 60.0


def _settings_values(user):
    return {
        "name": user.name or "",
        "age_group": user.age_group or "",
        "activity_level": user.activity_level or "",
        "outdoor_exposure": user.outdoor_exposure or "",
        "safe_temperature": (
            user.safe_temperature
            if user.safe_temperature is not None
            else DEFAULT_SAFE_TEMPERATURE
        ),
        "notification_enabled": user.notification_enabled is not False
    }


def _render_settings(values, errors=None, status=200):
    return render_template(
        "settings.html",
        values=values,
        errors=errors or [],
        age_groups=AGE_GROUPS,
        activity_levels=ACTIVITY_LEVELS,
        outdoor_exposures=OUTDOOR_EXPOSURES,
        min_safe_temperature=MIN_SAFE_TEMPERATURE,
        max_safe_temperature=MAX_SAFE_TEMPERATURE
    ), status


@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if not session.get("logged_in") or not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(id=session["user_id"]).first_or_404()
    values = _settings_values(user)

    if request.method == "GET":
        return _render_settings(values)

    values = {
        "name": request.form.get("name", "").strip(),
        "age_group": request.form.get("age_group", ""),
        "activity_level": request.form.get("activity_level", ""),
        "outdoor_exposure": request.form.get("outdoor_exposure", ""),
        "safe_temperature": request.form.get("safe_temperature", "").strip(),
        "notification_enabled": (
            request.form.get("notification_enabled") == "true"
        )
    }
    errors = []

    if len(values["name"]) > 100:
        errors.append("Name must be 100 characters or fewer.")

    if values["age_group"] not in AGE_GROUPS:
        errors.append("Select a valid age group.")

    if values["activity_level"] not in ACTIVITY_LEVELS:
        errors.append("Select a valid activity level.")

    if values["outdoor_exposure"] not in OUTDOOR_EXPOSURES:
        errors.append("Select a valid outdoor exposure range.")

    try:
        safe_temperature = float(values["safe_temperature"])
        if (
            not math.isfinite(safe_temperature)
            or not MIN_SAFE_TEMPERATURE <= safe_temperature <= MAX_SAFE_TEMPERATURE
        ):
            errors.append(
                "Safe temperature must be between 0°C and 60°C."
            )
    except ValueError:
        safe_temperature = None
        errors.append("Enter a valid safe temperature.")

    if errors:
        return _render_settings(values, errors, status=400)

    user.name = values["name"] or None
    user.age_group = values["age_group"]
    user.activity_level = values["activity_level"]
    user.outdoor_exposure = values["outdoor_exposure"]
    user.safe_temperature = safe_temperature
    user.notification_enabled = values["notification_enabled"]

    db.session.commit()
    flash("Your settings have been saved.", "success")
    return redirect(url_for("settings.settings"))
