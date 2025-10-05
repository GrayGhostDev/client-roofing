# Audit Fields Documentation

## Overview
The iSwitch Roofs CRM system includes comprehensive audit fields on all database entities to track who created and last updated each record. This provides accountability, traceability, and helps with debugging and compliance.

## Fields

### Core Audit Fields
All models that inherit from `BaseDBModel` automatically include these fields:

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `created_by` | String | User ID who created the record | No |
| `updated_by` | String | User ID who last updated the record | No |
| `created_by_email` | String | Email of user who created the record | No |
| `updated_by_email` | String | Email of user who last updated the record | No |
| `created_at` | DateTime | Timestamp when record was created | Auto |
| `updated_at` | DateTime | Timestamp when record was last updated | Auto |

## Implementation

### Model Definition
All models inherit audit fields from `BaseDBModel`:

```python
from app.models.base import BaseDBModel

class Lead(BaseDBModel):
    # Model fields...
    pass
```

### AuditMixin Helper
The `AuditMixin` class provides a helper method for setting audit fields:

```python
model = Lead()
model.set_audit_fields(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    user_email="admin@iswitchroofs.com",
    is_update=False  # False for create, True for update
)
```

### Middleware Integration
The audit middleware automatically extracts user information from JWT tokens and adds audit fields to requests:

```python
from app.middleware import audit_middleware

@app.route('/api/resource', methods=['POST'])
@audit_middleware
def create_resource():
    data = request.get_json()  # Will have audit fields
    # ...
```

## Usage Examples

### Creating a Record with Audit Fields

```python
# Manual setting
lead = Lead(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    created_by="user_123",
    created_by_email="sales@iswitchroofs.com"
)

# Using helper method
lead = Lead(first_name="John", last_name="Doe")
lead.set_audit_fields(
    user_id="user_123",
    user_email="sales@iswitchroofs.com",
    is_update=False
)
```

### Updating a Record

```python
# Only update the updated_by fields
lead.set_audit_fields(
    user_id="manager_456",
    user_email="manager@iswitchroofs.com",
    is_update=True
)
```

### API Endpoints
When making API requests with authentication, audit fields are automatically populated:

```bash
curl -X POST http://localhost:5000/api/leads/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "2485551234",
    "source": "website_form"
  }'
```

The created lead will automatically have:
- `created_by`: User ID from JWT token
- `created_by_email`: User email from JWT token
- `updated_by`: Same as created_by (on creation)
- `updated_by_email`: Same as created_by_email (on creation)

## Database Schema

### Supabase Migration
Add audit fields to all tables:

```sql
ALTER TABLE leads
ADD COLUMN created_by VARCHAR(255),
ADD COLUMN updated_by VARCHAR(255),
ADD COLUMN created_by_email VARCHAR(255),
ADD COLUMN updated_by_email VARCHAR(255);

-- Add indexes for performance
CREATE INDEX idx_leads_created_by ON leads(created_by);
CREATE INDEX idx_leads_updated_by ON leads(updated_by);
```

## JWT Token Structure

The JWT token should contain user information:

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@iswitchroofs.com",
  "name": "Admin User",
  "role": "admin",
  "exp": 1704067200
}
```

## Security Considerations

1. **Authentication Required**: Audit fields are only populated for authenticated requests
2. **Immutable Created Fields**: The `created_by` and `created_by_email` fields should never change after creation
3. **Validation**: User IDs should be validated against the user database
4. **Privacy**: Be mindful of exposing user information in API responses

## Testing

### Unit Tests
```python
def test_audit_fields():
    model = BaseDBModel()
    model.set_audit_fields(
        user_id="test_user",
        user_email="test@example.com",
        is_update=False
    )

    assert model.created_by == "test_user"
    assert model.created_by_email == "test@example.com"
    assert model.updated_by == "test_user"
```

### Integration Tests
```python
def test_api_audit_fields(client, auth_headers):
    response = client.post(
        '/api/leads/',
        json=lead_data,
        headers=auth_headers
    )

    data = response.json()
    assert 'created_by' in data
    assert 'updated_by' in data
```

## Best Practices

1. **Always Track**: Every create/update operation should populate audit fields
2. **Consistent Format**: Use UUIDs or consistent ID format for user IDs
3. **Email Validation**: Validate email format before storing
4. **Timezone Awareness**: Store timestamps in UTC
5. **Audit Logs**: Consider separate audit log table for sensitive operations
6. **Retention Policy**: Define how long to retain audit information
7. **Performance**: Index audit fields used in queries

## Troubleshooting

### Missing Audit Fields
If audit fields are not being populated:
1. Check JWT token is valid and contains user information
2. Verify middleware is applied to the route
3. Ensure user is authenticated
4. Check middleware configuration

### Incorrect User Information
If wrong user information is being recorded:
1. Verify JWT token payload
2. Check token expiration
3. Ensure proper token refresh logic
4. Validate middleware user extraction logic

## Related Documentation

- [Authentication Guide](./AUTHENTICATION.md)
- [API Endpoints](./endpoints/)
- [Security Guide](../security/SECURITY_GUIDE.md)
- [Database Schema](./DATABASE_SCHEMA.md)