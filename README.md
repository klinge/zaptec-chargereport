# Zaptec Charge Report Generator

[![CI](https://github.com/klinge/zaptec-chargereport/workflows/CI/badge.svg)](https://github.com/klinge/zaptec-chargereport/actions)
[![codecov](https://codecov.io/gh/klinge/zaptec-chargereport/branch/main/graph/badge.svg)](https://codecov.io/gh/klinge/zaptec-chargereport)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automated tool for generating and distributing monthly charging reports from Zaptec EV chargers.

> **Note**: The report output is formatted for specific requirements and may need modification for other use cases. However, the Zaptec API wrapper (`src/api/`) is reusable and can be adapted for other integrations.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/klinge/zaptec-chargereport.git
cd zaptec-chargereport

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp EXAMPLE.env .env
# Edit .env with your credentials

# Run the report generator
python main.py
``` 

## Features
- Simple wrapper around some of the endpoints in the Zaptec API (see `src/api` for more details)
- Fetches charging data from Zaptec API
- Generates summarized reports per user
- Exports data to CSV in a format that is specific to the requirements I have (probably not reusable for other purposes)
- Automatically emails reports to configured recipients

## 🔌 Reusable Components

### Zaptec API Wrapper
The `src/api/` module provides a clean Python interface to Zaptec's REST API:

```python
from src.api.zaptec_api import _ZaptecApi as ZaptecApi

with ZaptecApi() as api:
    # Get charging sessions for date range
    sessions = api.get_charging_sessions(from_date, to_date)
    
    # Get installation report
    report = api.get_installation_report(from_date, to_date)
```

**Features**:
- Automatic authentication and token management
- Pagination handling for large datasets
- Context manager support for proper cleanup

## 🧪 Testing

The project includes comprehensive testing:
- **Unit tests** (>90% coverage) - Test business logic
- **API contract tests** - Detect Zaptec API changes
- **Smoke tests** - Verify production deployments

## 🤝 Contributing

Contributions welcome! The API wrapper is especially useful for other Zaptec integrations.

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `make test`
5. Submit a pull request

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Zaptec API credentials
- SMTP server credentials for email distribution

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Configure environment**:
   ```bash
   cp EXAMPLE.env .env
   ```
   Edit `.env` with your actual credentials:
   - Zaptec username/password
   - Installation ID
   - SMTP server details
   - Email recipients

   ⚠️ **Security**: Never commit `.env` files to version control!

## 📊 Usage

### Basic Usage
```bash
python main.py
```

### Development
```bash
# Run tests
make test

# Run with coverage
make test-cov

# Lint code
make lint

# Auto-fix formatting
make autofix

# Run API contract tests
make test-contracts
```
