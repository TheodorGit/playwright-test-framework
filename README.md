# E-Commerce Test Automation Framework

A comprehensive test automation framework built with **Playwright** and **Pytest**, demonstrating modern testing practices and design patterns.

## Features

- **Page Object Model (POM)** - Clean separation of page interactions from test logic
- **Pytest Fixtures** - Reusable test setup with session and function-scoped fixtures
- **Custom Markers** - Organized test categorization (functional, performance, e2e, smoke)
- **Performance Testing** - Load time measurements with configurable thresholds
- **Structured Reporting** - JSON-based test results for CI/CD integration
- **Environment Configuration** - Flexible setup via `.env` files

## Project Structure

```
portfolio_demo/
├── pages/                      # Page Object Model
│   ├── login_page.py          # Login page interactions
│   ├── products_page.py       # Product listing & cart operations
│   ├── cart_page.py           # Shopping cart management
│   └── checkout_page.py       # Checkout flow handling
│
├── tests/
│   ├── conftest.py            # Pytest fixtures & configuration
│   ├── functional/            # UI functional tests
│   │   ├── test_login.py      # Authentication tests
│   │   ├── test_products.py   # Product page tests
│   │   ├── test_cart.py       # Cart functionality tests
│   │   └── test_checkout.py   # Checkout validation tests
│   ├── performance/           # Performance tests
│   │   └── test_page_load_times.py
│   └── e2e/                   # End-to-end workflow tests
│       └── test_complete_purchase.py
│
├── utils/                     # Utility modules
│   ├── generators.py          # Test data generation
│   ├── performance_utils.py   # Performance measurement helpers
│   └── reporter.py            # JSON test reporting
│
├── test_results/              # Test execution reports
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
└── .env.example              # Environment template
```

## Tech Stack

- **Python 3.10+**
- **Playwright** - Browser automation
- **Pytest** - Test framework
- **python-dotenv** - Environment management

## Setup

1. **Clone and install dependencies:**
   ```bash
   cd portfolio_demo
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure environment:**
   ```bash
   copy .env.example .env
   # Edit .env if needed (defaults work with SauceDemo)
   ```

## Running Tests

```bash
# Run all tests
pytest

# Run by marker
pytest -m functional    # UI functional tests
pytest -m performance   # Performance tests
pytest -m e2e          # End-to-end tests
pytest -m smoke        # Quick smoke tests

# Run specific test file
pytest tests/functional/test_login.py

# Run with visible browser
# Set HEADLESS=false in .env, then:
pytest tests/e2e/test_complete_purchase.py
```

## Test Categories

| Marker | Description |
|--------|-------------|
| `functional` | UI functional tests |
| `performance` | Load time measurements |
| `e2e` | Complete user workflows |
| `smoke` | Quick CI validation |
| `slow` | Long-running tests |

## Key Design Patterns

### Page Object Model
Each page has a dedicated class encapsulating its locators and interactions:

```python
class LoginPage:
    USERNAME_INPUT = "[data-test='username']"

    def login(self, username: str, password: str) -> None:
        self.page.fill(self.USERNAME_INPUT, username)
        # ...
```

### Fixture-Based Setup
Reusable authentication and browser management:

```python
@pytest.fixture
def authenticated_page(page):
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(username, password)
    yield page
```

### Structured Reporting
JSON reports for CI/CD integration:

```python
reporter = ResultsReporter("test_name")
reporter.add_step("Login", "passed")
reporter.save()  # Outputs to test_results/
```

## CI/CD Integration

The framework produces JSON reports compatible with most CI systems. Test results are saved to `test_results/` with timestamps for historical tracking.

## License

MIT
