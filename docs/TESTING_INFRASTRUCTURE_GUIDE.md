# Testing Infrastructure & Quality Assurance Guide
## iSwitch Roofs CRM Backend Testing Suite

**Version:** 1.0.0  
**Last Updated:** January 2025  
**Coverage Target:** 80%+

---

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Categories](#test-categories)
6. [Continuous Integration](#continuous-integration)
7. [Coverage Reports](#coverage-reports)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The iSwitch Roofs CRM testing infrastructure provides comprehensive quality assurance through multiple test layers:

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test API endpoints and service interactions
- **E2E Tests**: Test complete user workflows end-to-end
- **Performance Tests**: Ensure response times meet SLAs
- **Security Tests**: Validate authentication and data protection

### Testing Stack

- **Framework**: Pytest 8.0+
- **Mocking**: pytest-mock, unittest.mock
- **Coverage**: pytest-cov
- **HTTP Testing**: Flask test client
- **Fixtures**: Faker for test data generation

---

## Test Structure

```
backend/tests/
├── conftest.py                 # Global fixtures and configuration
├── pytest.ini                  # Pytest settings
├── unit/                       # Unit tests
│   ├── test_lead_service.py
│   ├── test_customer_service.py
│   ├── test_appointment_service.py
│   └── test_lead_scoring.py
├── integration/                # Integration tests
│   ├── test_api_leads.py
│   ├── test_api_customers.py
│   ├── test_api_projects.py
│   └── test_api_appointments.py
├── e2e/                        # End-to-end tests
│   ├── test_lead_workflows.py
│   ├── test_customer_workflows.py
│   └── test_quote_workflows.py
├── performance/                # Performance tests
│   └── test_load_testing.py
└── security/                   # Security tests
    └── test_authentication.py
```

---

## Running Tests

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only
pytest -m e2e

# Fast tests (exclude slow)
pytest -m "not slow"

# Performance tests
pytest -m performance

# Security tests
pytest -m security
```

### Run Specific Test Files

```bash
# Single file
pytest tests/unit/test_lead_service.py

# Specific test class
pytest tests/unit/test_lead_service.py::TestLeadServiceCreate

# Specific test function
pytest tests/unit/test_lead_service.py::TestLeadServiceCreate::test_create_lead_basic
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=app --cov-report=term-missing
```

### Run with Verbose Output

```bash
# Detailed output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

---

## Writing Tests

### Basic Test Structure

```python
import pytest
from app.services.lead_service import LeadService

@pytest.mark.unit
class TestLeadService:
    """Test lead service functionality"""
    
    def test_create_lead(self, sample_lead_data):
        """Test basic lead creation"""
        # Arrange
        lead_data = sample_lead_data
        
        # Act
        result = LeadService.create_lead(lead_data)
        
        # Assert
        assert result is not None
        assert result.first_name == lead_data['first_name']
```

### Using Fixtures

```python
@pytest.fixture
def sample_lead_data():
    """Fixture providing sample lead data"""
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'phone': '+15551234567'
    }

def test_with_fixture(sample_lead_data):
    """Test using fixture data"""
    assert sample_lead_data['first_name'] == 'John'
```

### Mocking External Services

```python
from unittest.mock import Mock, patch

def test_with_mock(mock_supabase_client):
    """Test with mocked Supabase client"""
    # Mock is provided by conftest.py
    mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = [
        {'id': '123', 'name': 'Test'}
    ]
    
    # Your test code here
    result = some_function_that_uses_supabase()
    
    assert result is not None
```

### Testing API Endpoints

```python
@pytest.mark.integration
def test_create_lead_endpoint(client, sample_lead_data):
    """Test lead creation API endpoint"""
    response = client.post(
        '/api/leads',
        data=json.dumps(sample_lead_data),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
```

### Parametrized Tests

```python
@pytest.mark.parametrize('status,expected_code', [
    ('new', 200),
    ('contacted', 200),
    ('invalid', 422)
])
def test_status_update(client, status, expected_code):
    """Test various status updates"""
    response = client.patch(
        '/api/leads/123',
        data=json.dumps({'status': status}),
        content_type='application/json'
    )
    
    assert response.status_code == expected_code
```

---

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Test individual functions/classes in isolation:

```python
@pytest.mark.unit
def test_calculate_lead_score():
    """Test lead scoring calculation"""
    score = calculate_score(budget=50000, urgency='immediate')
    assert score >= 80
```

**Purpose**: Fast, isolated tests for business logic  
**No External Dependencies**: Mock all external services  
**Coverage Target**: 90%+

### Integration Tests (`@pytest.mark.integration`)

Test API endpoints and service interactions:

```python
@pytest.mark.integration
def test_lead_creation_flow(client):
    """Test full lead creation through API"""
    response = client.post('/api/leads', data=lead_data)
    assert response.status_code == 201
```

**Purpose**: Test component interactions  
**Database**: Use test database or mocks  
**Coverage Target**: 80%+

### E2E Tests (`@pytest.mark.e2e`)

Test complete user workflows:

```python
@pytest.mark.e2e
def test_lead_to_customer_conversion(client):
    """Test complete workflow from lead to customer"""
    # Create lead
    # Schedule appointment
    # Generate quote
    # Convert to customer
    pass
```

**Purpose**: Validate business workflows  
**Execution**: Slower, run in CI/CD  
**Coverage Target**: Critical paths only

### Performance Tests (`@pytest.mark.performance`)

Test response times and load handling:

```python
@pytest.mark.performance
@pytest.mark.slow
def test_api_response_time(client, performance_timer):
    """Test API responds within SLA"""
    performance_timer.start()
    response = client.get('/api/leads')
    performance_timer.stop()
    
    assert performance_timer.elapsed < 1.0
```

**Purpose**: Ensure performance SLAs  
**Thresholds**: 
- API endpoints: < 200ms (p95)
- List endpoints: < 500ms (p95)
- Complex queries: < 2s (p95)

### Security Tests (`@pytest.mark.security`)

Test authentication and authorization:

```python
@pytest.mark.security
def test_unauthorized_access(client):
    """Test that protected endpoints require auth"""
    response = client.get('/api/admin/users')
    assert response.status_code == 401
```

**Purpose**: Validate security controls  
**Areas**: Authentication, Authorization, Input validation, SQL injection prevention

---

## Continuous Integration

### GitHub Actions Integration

Tests run automatically on:
- Every push to `develop` or `main`
- Every pull request
- Nightly scheduled runs

See `.github/workflows/ci-cd.yml`:

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Run Tests
      run: |
        pytest --cov=app --cov-report=xml
    - name: Upload Coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

Install pre-commit hooks to run tests before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Coverage Reports

### Viewing Coverage

```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Coverage Requirements

| Category | Minimum Coverage |
|----------|-----------------|
| **Services** | 90% |
| **API Routes** | 85% |
| **Models** | 80% |
| **Utilities** | 85% |
| **Overall** | 80% |

### Excluding Code from Coverage

```python
def debug_function():  # pragma: no cover
    """This won't be counted in coverage"""
    print("Debug output")
```

---

## Best Practices

### Test Organization

✅ **DO**:
- One test class per service/module
- Descriptive test names: `test_create_lead_with_invalid_email`
- Arrange-Act-Assert pattern
- Use fixtures for reusable test data
- Mock external dependencies
- Test edge cases and error conditions

❌ **DON'T**:
- Test implementation details
- Write tests that depend on other tests
- Use real external APIs in tests
- Commit large test datasets
- Skip tests without good reason

### Test Naming Convention

```python
def test_<function>_<scenario>_<expected_result>():
    """Clear description of what is tested"""
    pass

# Examples:
def test_create_lead_with_valid_data_returns_201():
def test_update_lead_not_found_returns_404():
def test_delete_lead_soft_deletes_record():
```

### Fixture Best Practices

```python
# Scope fixtures appropriately
@pytest.fixture(scope='session')  # Once per test session
@pytest.fixture(scope='module')   # Once per test module
@pytest.fixture(scope='function') # Once per test function (default)

# Use dependency injection
def test_example(client, auth_headers, sample_lead_data):
    # All fixtures available as parameters
    pass
```

### Mocking Best Practices

```python
# Mock at the boundary
with patch('app.services.external_api.call') as mock_call:
    mock_call.return_value = {'status': 'ok'}
    # Test your code
    
# Don't mock internal functions you're testing
# Don't over-mock - test real integration when possible
```

---

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "No module named 'app'"

```bash
# Solution: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

**Issue**: Database connection errors

```bash
# Solution: Use test configuration
export FLASK_ENV=testing
pytest
```

**Issue**: Import errors for fixtures

```bash
# Solution: Check conftest.py is in tests/ directory
ls tests/conftest.py
```

**Issue**: Coverage not tracking some files

```python
# Solution: Add to pytest.ini
[coverage:run]
source = app
omit = */tests/*
```

### Debug Mode

Run tests with debugging:

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb

# Print output
pytest -s

# Very verbose
pytest -vv
```

### Performance Issues

If tests are slow:

```bash
# Identify slow tests
pytest --durations=10

# Run only fast tests
pytest -m "not slow"

# Parallel execution (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

---

## Test Data Management

### Using Faker for Test Data

```python
from faker import Faker

fake = Faker()

def generate_lead():
    return {
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'address': fake.address()
    }
```

### Test Database Setup

```python
@pytest.fixture(scope='session')
def test_database():
    """Set up test database"""
    # Create tables
    db.create_all()
    
    yield db
    
    # Teardown
    db.drop_all()
```

---

## Quality Metrics

### Current Test Statistics

| Metric | Target | Current |
|--------|--------|---------|
| **Total Tests** | 200+ | 150+ |
| **Code Coverage** | 80% | 75% |
| **Average Test Time** | < 10s | 8s |
| **CI Pipeline Time** | < 5min | 4min |

### Test Execution Summary

```bash
# Run with summary
pytest --tb=line --cov=app --cov-report=term-missing

# Output:
# tests/unit ........................... [ 60% ]
# tests/integration .................... [ 85% ]
# tests/e2e ............................ [ 95% ]
# 
# ========== 150 passed, 2 skipped in 8.23s ==========
# TOTAL COVERAGE: 75%
```

---

## Next Steps

### Immediate Priorities

1. ✅ Set up pytest configuration
2. ✅ Create fixtures and test utilities
3. ✅ Write unit tests for core services
4. ✅ Write integration tests for APIs
5. ⏳ Implement E2E tests for critical workflows
6. ⏳ Set up performance testing with Locust
7. ⏳ Configure coverage reporting in CI/CD
8. ⏳ Achieve 80% code coverage target

### Future Enhancements

- Visual regression testing for Streamlit UI
- Mutation testing for test quality
- Contract testing for external APIs
- Load testing with realistic traffic patterns
- Chaos engineering for resilience testing

---

## Resources

### Documentation

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing Guide](https://flask.palletsprojects.com/testing/)
- [Faker Documentation](https://faker.readthedocs.io/)

### Internal Resources

- [Environment Configuration Guide](./ENVIRONMENT_CONFIGURATION_GUIDE.md)
- [Database Optimization Guide](./DATABASE_OPTIMIZATION_GUIDE.md)
- [Production Infrastructure Guide](./PRODUCTION_INFRASTRUCTURE_GUIDE.md)

### Support

For testing questions or issues:
1. Check this documentation
2. Review existing test examples in `backend/tests/`
3. Contact development team

---

**End of Testing Infrastructure Guide**
