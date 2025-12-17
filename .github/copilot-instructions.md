# Zaptec Charge Report - Copilot Instructions

## Project Overview
A Python tool that fetches EV charging data from Zaptec API, generates monthly invoicing and summary reports, and distributes them via email. The Zaptec API wrapper (`src/api/`) is reusable for other integrations; report formatting is specific to current requirements.

## Architecture & Data Flow

### Core Components

**API Layer** (`src/api/`)
- `BaseApi`: Generic HTTP client with automatic OAuth token management and context manager support
- `ZaptecApi`: Zaptec-specific implementation handling pagination, Pydantic validation of responses
- Credentials: `ZAPTEC_USERNAME`, `ZAPTEC_PASSWORD`, `ZAPTEC_INSTALLATION_ID` from `.env`
- Token refresh: Automatic when expired (2-minute buffer before actual expiry)

**Report Generation** (`src/reports/`)
- `MonthlySummaryReport`: Aggregates charging stats by user for previous month, emails to `SUMMARY_RECIPIENTS`
- `InvoicingReport`: Detailed per-session records with cost calculation (rate in `CHARGING_TARIFF`), emails to `INVOICING_RECIPIENTS`
- Both inherit error handling: catch exceptions → `handle_error()` → send email to `ERROR_RECIPIENTS` with stack trace
- Reports saved to `DATA_DIR/reports/` as CSV files

**Models** (`src/models/`)
- Pydantic models for API responses: `ChargingSession`, `Installation`, `ChargersResponse`, `InstallationReport`
- Used for runtime validation in `ZaptecApi` methods to catch API breaking changes

**Data Flow**: 
1. `main.py` → create `ZaptecApi()` context (auto-auth) → instantiate both report classes with api reference
2. Each report calls `api.get_installation_report(from_date, to_date)` or `api.get_charging_sessions()`
3. Process response into DataFrame → CSV → email
4. On error at any step: log + send error email + exit

## Critical Development Patterns

### Testing Strategy
- **Unit tests** (90%+ coverage): Mock all external dependencies (`responses` library for HTTP, `patch` for env vars)
- **Integration tests** (marked with `@pytest.mark.integration`): Make real API calls, require `.env.test` file
- Run unit tests: `make test`; integration tests: `make test-contracts`
- Test config in `pytest.ini`: markers define integration vs unit test distinction
- Environment setup in `conftest.py`: `setup_test_env` fixture auto-cleans env vars after each test

### Error Handling Conventions
- All I/O operations catch exceptions and pass to `handle_error(error, logger, email_service)` 
- `handle_error()` logs traceback to file and attempts email notification
- EmailService initialization can fail (invalid SMTP config) → app should fail fast, not silently
- Dev environment auto-disables emails (`SEND_EMAILS` defaults to "0" if `ENV=DEV`)

### Logging
- Centralized `setup_logger()` returns singleton logger instance
- Debug logs go to file only; console level controlled by `LOG_LEVEL` env var (DEV: INFO, PROD: INFO+)
- Log file path: `{DATA_DIR}/logs/charge_report_YYYYMMDD_HHMMSS.log`
- Use `logger.debug()` for detailed API payloads, `logger.info()` for workflow milestones

### Environment Variables
- Dev/Prod distinction: `ENV` controls SMTP config lookup (`DEV_SMTP_*` vs `PROD_SMTP_*`)
- SSL verification disabled in DEV by default (`SSL_VERIFY=false`) for proxy compatibility
- Missing required vars (`ZAPTEC_*`, SMTP config) → raise `ValueError` at service init time
- Email recipients as comma-separated lists: `INVOICING_RECIPIENTS`, `SUMMARY_RECIPIENTS`, `ERROR_RECIPIENTS`

## Specific API Patterns & Gotchas

### Pagination
`get_charging_sessions()` implements manual pagination:
- Loop with `PageIndex` param starting at 0
- Extract `Pages` count from response to know total pages
- Accumulate results across pages into single list

### Token Management
- Tokens expire after `expires_in` seconds (typically 3600)
- `is_token_valid()` returns False if token expired OR if expiry within 2-minute buffer (prevents race conditions)
- Context manager (`with ZaptecApi() as api:`) auto-closes session; reuse context across multiple API calls in same execution

### Pydantic Models
- All API responses validated against models in `src/models/zaptec_models.py`
- `ValidationError` raised if API response structure changes (catches breaking API changes)
- Models use Pydantic's `model_validate()` method (v2 syntax)

## Build & Deployment

### Common Commands
- `make test` - Run unit tests only
- `make test-cov` - Generate HTML coverage report in `htmlcov/`
- `make test-contracts` - Run integration tests against live API (requires `.env`)
- `make lint` - Check code style with flake8
- `make autofix` - Auto-format with autoflake, autopep8, black
- `python main.py` - Generate both reports and email them

### Local virtual environment (important)

- **Activate the project's `venv` before running code or tests**: the repository includes a local virtual environment named `venv`. On Linux/macOS (bash) run:
```bash
source venv/bin/activate
```
On Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```
- After activating the venv, install dependencies (if not already installed):
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
- Then run tests or the app as usual (e.g., `make test` or `python main.py`). Activating the venv ensures the correct Python interpreter and packages are used, and prevents `ModuleNotFoundError`.

### Key Files to Reference When Adding Features
- Report logic: `src/reports/invoicing_report.py` (lines 50-100 show CSV generation pattern)
- API pagination: `src/api/zaptec_api.py` (lines 60-90 show pagination loop)
- Email composition: `src/services/email_service.py` (lines 60-130 show SMTP logic)
- Date calculations: `src/utils/dateutils.py` (always uses `get_previous_month_range()` for consistency)

## When Adding New Features

### Adding a New API Endpoint - Step by Step

**Example: Adding `get_charger_status(charger_id: str)` to fetch real-time status of a specific charger**

1. **Define Pydantic model** in `src/models/zaptec_models.py`:
```python
class ChargerStatus(BaseModel):
    Id: str
    Name: str
    Status: int
    ModeId: int
    MaxCurrent: float
    IsOnline: bool
```

2. **Add method to `ZaptecApi`** in `src/api/zaptec_api.py`:
```python
def get_charger_status(self, charger_id: str) -> ChargerStatus:
    """
    Fetch real-time status of a specific charger.
    
    Args:
        charger_id (str): UUID of the charger
    
    Returns:
        ChargerStatus: Object containing charger status details
    """
    self.logger.debug(f"Calling /api/chargers/{charger_id}")
    response = self._make_request("GET", endpoint=f"/api/chargers/{charger_id}")
    return ChargerStatus.model_validate(response.json())
```
Key points:

3. **Add import** to `src/api/zaptec_api.py`:
```python
from src.models.zaptec_models import ChargerStatus  # Add to import list
```

4. **Write unit test** in `tests/test_api.py`:
```python
@responses.activate
def test_get_charger_status(self):
    """Test charger status retrieval"""
    responses.add(
        responses.POST,
        "https://api.zaptec.com/oauth/token",
        json={"access_token": "test_token", "expires_in": 3600},
    )
    
    responses.add(
        responses.GET,
        "https://api.zaptec.com/api/chargers/123e4567-e89b-12d3-a456-426614174000",
        json={
            "Id": "123e4567-e89b-12d3-a456-426614174000",
            "Name": "Charger 1",
            "Status": 1,
            "ModeId": 2,
            "MaxCurrent": 32.0,
            "IsOnline": True,
        },
    )
    
    with patch.dict("os.environ", {
        "ZAPTEC_USERNAME": "test_user",
        "ZAPTEC_PASSWORD": "test_pass",
        "ZAPTEC_INSTALLATION_ID": "install_id"
    }):
        api = ZaptecApi()
        status = api.get_charger_status("123e4567-e89b-12d3-a456-426614174000")
        assert status.IsOnline is True
        assert status.MaxCurrent == 32.0
```
Use `@responses.activate` decorator to mock HTTP calls without hitting real API.

5. **Run tests** to verify:
```bash
make test  # Should pass without calling real API
```

### Other Feature Types


### Recommended API client usage (avoid accidental multiple auth calls)

- **Prefer shared factory**: use `from src.api import get_zaptec_api` and call `get_zaptec_api()` to obtain a lazily-created, shared `ZaptecApi` instance. This avoids multiple OAuth calls and respects rate limits.
- **Runtime reminder**: The `ZaptecApi` constructor now emits a `UserWarning` when instantiated directly to remind developers to use the factory or dependency-inject an instance. It's safe to ignore if you intentionally want a new client.
- **Example**:
```python
from src.api import get_zaptec_api

api = get_zaptec_api()
with api as api_ctx:
    data = api_ctx.get_charging_sessions(from_date, to_date)
```

Include this pattern in new modules and tests to ensure a single shared client is reused across the process.
