# HeatGuard 360

Personalized heat-risk analysis and safety recommendations using current and forecast weather.

## Project overview

HeatGuard 360 combines a user's selected location, local weather, and profile settings to estimate heat risk and present general safety guidance. The Flask application includes a dashboard, profile settings, in-app alerts, hourly forecast, and temperature history.

HeatGuard 360 is an informational tool. Its risk score and recommendations are not medical advice, a diagnosis, or an emergency service.

## Problem statement

Weather temperature alone does not describe the heat conditions a person may experience. Humidity, apparent temperature, activity, and time spent outdoors can change exposure. People need a concise way to view those conditions alongside their personal activity and temperature preferences.

## Objectives

- Present current and forecast weather for a user's saved location.
- Provide a deterministic, explainable heat-risk score.
- Tailor general precautions to activity and outdoor exposure settings.
- Keep user settings, alerts, and weather history scoped to the signed-in user.
- Provide responsive dashboard visualizations with a static fallback for unsupported 3D rendering.

## Features

- Mobile-number login with a six-digit, two-minute OTP challenge and three verification attempts.
- Explicit local-only demo OTP mode; no SMS/OTP delivery provider is integrated.
- User profile settings: name, age group, activity level, outdoor exposure, safe temperature, and notification preference.
- Browser geolocation and location search/reverse geocoding through OpenStreetMap Nominatim.
- Current weather and same-day hourly forecast from Open-Meteo.
- Personalized risk score, risk category, general safety recommendations, and hydration guidance.
- High/critical/temperature-threshold in-app alerts with a six-hour duplicate cooldown and mark-as-read support.
- Per-user temperature history with a table and chart.
- Responsive dashboard and lazily loaded procedural Three.js globe with a CSS fallback.

## Technology stack

- Python 3, Flask, Jinja
- Flask-SQLAlchemy and SQLAlchemy
- PostgreSQL (`psycopg2-binary`)
- Requests for Open-Meteo and Nominatim HTTP calls
- HTML, CSS, and browser JavaScript
- Three.js ES module loaded from a pinned jsDelivr CDN URL when the globe approaches the viewport
- `unittest` for automated tests

## System architecture

```text
Browser
  ├── Jinja pages and responsive CSS
  ├── Location JavaScript ── authenticated Flask location API
  └── Lazy Three.js globe (CSS fallback)
            │
            ▼
Flask application and blueprints
  ├── Authentication and profile settings
  ├── Dashboard, alerts, and history routes
  ├── Weather service ── Open-Meteo
  ├── Location lookup ── OpenStreetMap Nominatim
  ├── Risk and recommendation services
  └── Alert and history services
            │
            ▼
PostgreSQL through Flask-SQLAlchemy
```

The main application factory and blueprint registration are in `app.py`. Routes live in `routes/`, data models in `models/`, and reusable business logic in `services/`. Templates and static assets are under `templates/` and `static/`.

## Database overview

The application uses these PostgreSQL tables:

| Table | Purpose and principal columns |
|---|---|
| `users` | Account/profile: `id`, unique `mobile_number`, `name`, `safe_temperature`, `age_group`, `activity_level`, `outdoor_exposure`, `notification_enabled`, `created_at` |
| `locations` | User-owned coordinates and label: `id`, `user_id`, `latitude`, `longitude`, `location_name`, `created_at` |
| `alerts` | User-owned in-app alerts: `id`, `user_id`, `temperature`, `threshold`, `risk_score`, `heat_level`, `location`, `condition_key`, `message`, `is_read`, `created_at` |
| `temperature_records` | User/location observations: `id`, `user_id`, `location_id`, `temperature`, `humidity`, `feels_like`, `risk_score`, `risk_level`, `recorded_at` |

`locations`, `alerts`, and `temperature_records` reference `users`; temperature records also reference `locations`. The existing-schema SQL updates are additive and use `IF NOT EXISTS`:

- `migrations/001_add_user_profile_settings.sql`
- `migrations/002_extend_heat_alerts.sql`
- `migrations/003_extend_temperature_history.sql`

For a fresh development database, `flask --app app init-db` creates the current model schema. For an existing database, back it up and apply the three migration files in numeric order. `init-db` is not a schema-upgrade tool: SQLAlchemy `create_all()` does not alter existing tables.

## Heat Risk Algorithm

`services/risk_service.py` computes a deterministic score from 0 to 100. Temperature inputs are normalized against the user's safe temperature and humidity is mapped from 30–80% to 0–100; both mappings are clamped to that range. Activity and exposure categories are mapped in order to 0, 33.33, 66.67, and 100.

```text
temperature contribution = clamp((temperature - safe_temperature) × 100 / 15) × 0.40
humidity contribution    = clamp((humidity - 30) × 2) × 0.20
feels-like contribution  = clamp((feels_like - safe_temperature) × 100 / 15) × 0.20
activity contribution   = activity category value × 0.10
exposure contribution   = exposure category value × 0.10

score = round(clamp(sum of contributions, 0, 100))
```

| Score | Category |
|---:|---|
| 0–25 | Low Risk |
| 26–50 | Moderate Risk |
| 51–75 | High Risk |
| 76–100 | Critical Risk |

The current scoring weights are temperature 40%, humidity 20%, feels-like temperature 20%, activity 10%, and outdoor exposure 10%. Age group is saved in the profile but is not currently part of this specified scoring formula.

## Screenshots

_Placeholder: add screenshots of the dashboard, settings, alerts, and history pages here._

## Installation

Requirements: Python 3, PostgreSQL, and (for location/weather features) network access to Open-Meteo and Nominatim. On Windows PowerShell:

1. Clone the repository and change into the project directory.
2. Create and activate a virtual environment:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Create a PostgreSQL database and configure the environment variables below.
5. Initialize a fresh database:

   ```powershell
   flask --app app init-db
   ```

   For an existing database, back it up and apply the migration SQL files in numeric order instead. Example:

   ```powershell
   psql "$env:DATABASE_URL" -f .\migrations\001_add_user_profile_settings.sql
   psql "$env:DATABASE_URL" -f .\migrations\002_extend_heat_alerts.sql
   psql "$env:DATABASE_URL" -f .\migrations\003_extend_temperature_history.sql
   ```

## Environment variables

Place these values in a local `.env` file (it is ignored by Git). Do not commit real secrets.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Long random secret used to sign Flask sessions. Required. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `DATABASE_URL` | SQLAlchemy database URL, e.g. `postgresql://username:password@localhost:5432/heatguard360`. Required. URL-encode reserved characters in credentials. |
| `APP_ENV` | `local` by default. Set to `production` on a deployed server; production always disables demo OTP even if `DEMO_OTP_ENABLED` is mistakenly true. |
| `FLASK_DEBUG` | Enables Flask debug behavior. Defaults to true only when `APP_ENV=development`; otherwise false. |
| `DEMO_OTP_ENABLED` | Defaults to true for `APP_ENV=local`, `development`, or `demo`, and false for production. Set false to disable local OTP demo. No SMS provider is required. |
| `SESSION_COOKIE_SECURE` | Secure-cookie setting. Defaults to false for local/demo environments and true otherwise; production should use HTTPS. |

For local HTTP development, the defaults are `APP_ENV=local` and `DEMO_OTP_ENABLED=true`; the OTP page shows the code and no SMS service is called. You may set `DEMO_OTP_ENABLED=false` to disable demo login. The demo OTP is deliberately exposed in the local OTP page/session and is **not safe for production**. Set `APP_ENV=production` for deployment: demo login and OTP display are disabled. A real OTP delivery provider would be needed before enabling production login.

## How to run

After installing dependencies, configuring `.env`, and initializing/upgrading the database:

```powershell
python app.py
```

Open `http://127.0.0.1:5000/`. For deployment, use a production WSGI server behind HTTPS; do not enable Flask debug mode or the demo OTP.

## Routes

| Route | Purpose |
|---|---|
| `/` | Redirect to login |
| `/login`, `/otp` | Login and OTP challenge |
| `/resend-otp`, `/logout` | Resend demo OTP and sign out |
| `/dashboard` | Personalized weather and heat-risk dashboard |
| `/settings` | User profile and notification preferences |
| `/alerts` | User's in-app alerts |
| `/alerts/<id>/read` | Mark one owned alert as read |
| `/history` | User's weather/risk observations |
| `/api/location` | Save browser coordinates |
| `/api/search-location` | Search and save a location |

## Future scope

- Integrate and test a real SMS/OTP provider, including server-side challenge storage, provider failure handling, and rate limiting.
- Add database migration tooling/version tracking and production migration automation.
- Deliver configurable push, SMS, or email alerts and honor notification settings across each delivery channel.
- Evaluate additional factors and validate risk thresholds with domain experts; the current score is an explainable product heuristic, not a validated medical model.
- Add monitoring, structured operational logs, API caching/rate controls, and deployment health checks.
- Add browser-level visual tests and screenshots for supported mobile and desktop viewports.

## Testing checklist

- [ ] Run all tests: `python -m unittest discover -s tests -v`.
- [ ] Start with a fresh PostgreSQL database using `flask --app app init-db`; verify an existing database is upgraded with migrations `001`–`003` without losing records.
- [ ] With local demo OTP enabled, request a login code, verify it, try an incorrect code three times, and confirm expiry/resend behavior.
- [ ] Confirm login, logout, settings, alerts, and history routes behave correctly for logged-in and logged-out users.
- [ ] Save settings and verify invalid values are rejected; disable notifications and confirm a refresh does not create a new in-app alert.
- [ ] Save a location by geolocation and search; confirm malformed/out-of-range coordinates are rejected without creating records.
- [ ] Verify current weather/forecast render from API data and that API outages or malformed responses produce an unavailable state, not fabricated data or a traceback.
- [ ] Check risk results at low, moderate, high, and critical conditions; review recommendation and hydration guidance.
- [ ] Confirm alert duplicate cooldown, read/unread status, and user ownership; confirm history is user-scoped and deduplicated.
- [ ] Test the dashboard at narrow and wide viewport sizes and with reduced motion enabled.
- [ ] Verify the globe uses saved coordinates; test WebGL/CDN failure fallback and reduced-motion behavior.
- [ ] Before deployment, keep debug and demo OTP disabled, use HTTPS and a secure session cookie, and integrate a real OTP provider.
