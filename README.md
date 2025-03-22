# Solana Wallet Analytics API

## Overview
A Django REST framework based API for analyzing Solana wallet data, including transaction history, asset holdings, and investment performance metrics.

## Features
- Wallet overview and balance tracking
- Transaction history analysis
- Token holdings and NFT tracking
- Performance metrics calculation

## 项目结构
```
backend/
├── api/                # Contains API-related files
│   ├── __init__.py
│   ├── urls.py         # URL routing for API endpoints
│   ├── views.py        # View functions for handling requests
│   └── serializers.py   # Serializers for converting data to JSON
├── core/               # Core application files
│   ├── __init__.py
│   ├── settings.py     # Django settings
│   ├── urls.py         # Main application URL routing
│   └── wsgi.py         # WSGI entry point
├── manage.py           # Command-line utility for Django
├── requirements.txt    # Python package dependencies
└── README.md           # Documentation for the backend
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yangRg25089/sol-analytics-api.git
cd sol-analytics-api
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Setup database:
```bash
# Create PostgreSQL database and user
createdb solana_wallet_db
createuser solana_wallet_user

# Run migrations
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## API Documentation
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## API Endpoints
- `GET /api/account/<wallet_address>/`: Get account overview
- `GET /api/transactions/<wallet_address>/`: Get transaction history
- `GET /api/assets/<wallet_address>/`: Get token and NFT holdings
- `GET /api/performance/<wallet_address>/`: Get wallet performance metrics

## Development
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Check code style
black .
flake8 .
```

## License
MIT License