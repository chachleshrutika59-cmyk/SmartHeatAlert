from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from extensions import db
from models.user import User

import secrets
from datetime import datetime, timedelta, timezone


auth_bp = Blueprint("auth", __name__)


# OTP settings
OTP_EXPIRY_MINUTES = 2
MAX_OTP_ATTEMPTS = 3


def _demo_otp_for_template():
    if (
        _demo_otp_enabled()
    ):
        return session.get("demo_otp")
    return None


def _demo_otp_enabled():
    return (
        current_app.config.get("LOCAL_DEMO_MODE", False)
        and current_app.config.get("DEMO_OTP_ENABLED", False)
    )


def generate_otp():
    """Generate a secure random 6-digit OTP."""
    return f"{secrets.randbelow(1000000):06d}"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if not _demo_otp_enabled():
            return render_template(
                "login.html",
                error=(
                    "Local demo OTP is disabled. Set APP_ENV=local and "
                    "enable DEMO_OTP_ENABLED to test sign-in."
                )
            ), 503

        mobile_number = request.form.get("mobile_number", "").strip()

        # Basic mobile number validation
        if not mobile_number:
            return render_template(
                "login.html",
                error="Please enter your mobile number."
            )

        if not mobile_number.isdigit() or len(mobile_number) != 10:
            return render_template(
                "login.html",
                error="Please enter a valid 10-digit mobile number."
            )

        # Generate random OTP
        otp = generate_otp()

        # Store OTP information in session
        session.clear()
        session["mobile_number"] = mobile_number
        session["otp"] = otp
        session["otp_created_at"] = (
            datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        )
        session["otp_attempts"] = 0

        # Development/demo only
        session["demo_otp"] = otp

        return redirect(url_for("auth.otp"))

    return render_template("login.html")


@auth_bp.route("/otp", methods=["GET", "POST"])
def otp():
    if not _demo_otp_enabled():
        session.clear()
        return render_template(
            "login.html",
            error=(
                "Local demo OTP is disabled. Set APP_ENV=local and enable "
                "DEMO_OTP_ENABLED to test sign-in."
            )
        ), 503

    mobile_number = session.get("mobile_number")

    # User should not directly open OTP page
    if not mobile_number:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        entered_otp = request.form.get("otp", "").strip()

        # Check maximum attempts
        attempts = session.get("otp_attempts", 0)

        if attempts >= MAX_OTP_ATTEMPTS:

            return render_template(
                "otp.html",
                error="Maximum attempts reached. Please request a new OTP.",
                demo_otp=_demo_otp_for_template()
            )

        # Increase attempt count
        session["otp_attempts"] = attempts + 1

        # Check OTP expiry
        created_at_string = session.get("otp_created_at")

        if not created_at_string:

            return render_template(
                "otp.html",
                error="OTP session expired. Please request a new OTP.",
                demo_otp=_demo_otp_for_template()
            )

        created_at = datetime.fromisoformat(created_at_string)

        expiry_time = created_at + timedelta(
            minutes=OTP_EXPIRY_MINUTES
        )

        if datetime.now(timezone.utc).replace(tzinfo=None) > expiry_time:

            return render_template(
                "otp.html",
                error="OTP has expired. Please request a new OTP.",
                demo_otp=_demo_otp_for_template()
            )

        # Check OTP
        if entered_otp != session.get("otp"):

            remaining = MAX_OTP_ATTEMPTS - session["otp_attempts"]

            if remaining > 0:
                error_message = (
                    f"Invalid OTP. {remaining} attempt(s) remaining."
                )
            else:
                error_message = (
                    "Invalid OTP. Maximum attempts reached. "
                    "Please request a new OTP."
                )

            return render_template(
                "otp.html",
                error=error_message,
                demo_otp=_demo_otp_for_template()
            )

        # OTP is correct
        # Find existing user
        user = User.query.filter_by(
            mobile_number=mobile_number
        ).first()

        # Create user if not found
        if user is None:

            user = User(
                mobile_number=mobile_number
            )

            db.session.add(user)
            db.session.commit()

        # Replace the pre-authentication session data after OTP verification.
        session.clear()
        session["logged_in"] = True
        session["user_id"] = user.id
        session["mobile_number"] = mobile_number

        return redirect(
            url_for("dashboard.dashboard")
        )

    return render_template(
        "otp.html",
        demo_otp=_demo_otp_for_template()
    )


@auth_bp.route("/resend-otp")
def resend_otp():

    mobile_number = session.get("mobile_number")

    if not mobile_number or not _demo_otp_enabled():
        return redirect(url_for("auth.login"))

    # Generate completely new OTP
    otp = generate_otp()

    session["otp"] = otp
    session["otp_created_at"] = (
        datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    )
    session["otp_attempts"] = 0
    # Development/demo only
    session["demo_otp"] = otp

    return redirect(url_for("auth.otp"))


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))