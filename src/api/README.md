# API client (src/api)

This package contains a small Zaptec API client used by the project to fetch charger and charging data.

Overview
--------
- `BaseApi` (in `base_api.py`) is a lightweight HTTP client that:
  - manages a `requests.Session()`
  - performs OAuth password-grant authentication against `/oauth/token`
  - caches the access token and refreshes it when expired (2-minute safety buffer)
  - exposes `_make_request()` for authenticated requests and supports context-manager usage
  - responses are validated with Pydantic models (see models/zaptec_models.py), so returned objects are type-checked and schema-validated before use

- `_ZaptecApi` (in `zaptec_api.py`) implements Zaptec-specific calls and Pydantic model validation.

Usage
-----
Basic example:

```python
from src.api.zaptec_api import _ZaptecApi

with _ZaptecApi() as api:
    installations = api.get_installation()
    chargers = api.get_chargers()
    sessions = api.get_charging_sessions(
        "2025-01-01T00:00:00.000Z", "2025-01-31T23:59:59.999Z"
    )
    report = api.get_installation_report("2025-01-01T00:00:00.000", "2025-01-31T23:59:59.999")

```

Environment variables
---------------------
- `ZAPTEC_USERNAME`, `ZAPTEC_PASSWORD` — credentials used for the password grant.
- `ZAPTEC_INSTALLATION_ID` — installation identifier used for queries.
- `ENV` — controls environment (defaults to `DEV`).
- `SSL_VERIFY` — set to `false` to disable SSL verification in dev environments.

Endpoints implemented
---------------------
- Authentication: `POST /oauth/token` — handled by `BaseApi.get_auth_token()`.
- `GET /api/installation` — `get_installation()` returns a list of `Installation` models.
- `GET /api/chargers` — `get_chargers()` returns `ChargersResponse`.
- `GET /api/chargehistory` — `get_charging_sessions(from_date, to_date)` implements pagination and returns a combined `ChargingSessionResponse`. Removes `SignedSession` from items and filters out guest/unauthenticated sessions.
- `POST /api/chargehistory/installationreport` — `get_installation_report(from_date, to_date)` returns `InstallationReport`. Note: this method expects date strings without a trailing `Z`.

Notes and behavior
------------------
- Token handling: tokens are cached and automatically refreshed when near expiry.
- Pagination: `get_charging_sessions` iterates pages using `PageIndex` and `Pages` from the API.
- Filtering: guest/unauthenticated sessions (missing `UserId` or `UserUserName`) are skipped to avoid including anonymous sessions in invoicing.
- Logging: both modules use the project's `setup_logger()` for debug/info/warning messages.

See code
--------
For implementation details, read the source files:

- [src/api/base_api.py](src/api/base_api.py)
- [src/api/zaptec_api.py](src/api/zaptec_api.py)
