# Data Model: Fasting Tracker App

**Date**: 2025-10-25  
**Phase**: 1 - Data Model Design

## Entity Overview

The fasting tracker application centers around tracking fasting periods for individual users with emotional status and duration tracking.

## Core Entities

### 1. Fast Model

**Purpose**: Represents a single fasting period with start time, optional end time, emotional status, and user comments.

**Location**: `healthy_herron/fasting/models.py`

**Inheritance**: 
- `healthy_herron.core.models.AuditableModel` (constitution requirement)
- `model_utils.models.TimeStampedModel` (constitution requirement)

**Fields**:

| Field Name | Type | Description | Constraints | Required |
|------------|------|-------------|-------------|----------|
| `user` | ForeignKey(User) | Owner of the fast record | CASCADE delete, db_index=True | Yes |
| `start_time` | DateTimeField | When the fast began | auto_now_add=False | Yes |
| `end_time` | DateTimeField | When the fast ended | null=True, blank=True | No |
| `emotional_status` | CharField | User's emotional state when ending fast | choices=EMOTIONAL_STATUS_CHOICES, max_length=20, null=True, blank=True | No |
| `comments` | TextField | User's reflection on the fast | max_length=128, blank=True | No |

**Choices**:
```python
EMOTIONAL_STATUS_CHOICES = [
    ('energized', 'Energized'),
    ('satisfied', 'Satisfied'), 
    ('challenging', 'Challenging'),
    ('difficult', 'Difficult'),
]
```

**Properties**:
- `duration`: Calculated duration for completed fasts (end_time - start_time)
- `elapsed_time`: Time elapsed from start_time to now (for active fasts)
- `is_active`: Boolean indicating if fast is ongoing (end_time is None)
- `duration_hours`: Duration formatted in hours and minutes
- `elapsed_hours`: Elapsed time formatted in hours and minutes

**Methods**:
- `end_fast(emotional_status, comments='')`: Complete the fast with emotional status
- `get_absolute_url()`: URL to fast detail view
- `__str__()`: String representation for admin and debugging

**Managers**:
- `FastManager`: Custom manager with user-filtered querysets
  - `for_user(user)`: Return fasts belonging to specific user
  - `active_for_user(user)`: Return active (unfinished) fasts for user
  - `completed_for_user(user)`: Return completed fasts for user

**Meta Options**:
```python
class Meta:
    ordering = ['-start_time']  # Most recent first (FR-015)
    indexes = [
        models.Index(fields=['user', '-start_time']),
        models.Index(fields=['user', 'end_time']),
    ]
    permissions = [
        ('view_own_fast', 'Can view own fasting records'),
        ('change_own_fast', 'Can change own fasting records'),
        ('delete_own_fast', 'Can delete own fasting records'),
    ]
```

**Validation Rules**:
1. `end_time` must be after `start_time` if provided (FR-016)
2. `comments` cannot exceed 128 characters (FR-019)
3. `emotional_status` is required when `end_time` is set (FR-007)
4. User cannot have multiple active fasts simultaneously (FR-003)

**State Transitions**:
```
Active Fast (end_time=None) → Completed Fast (end_time set, emotional_status required)
                            ↓
                     Can be edited/deleted
```

### 2. User Model (Existing)

**Purpose**: Django's built-in User model for authentication and ownership.

**Relationship**: One-to-Many with Fast (User has many Fasts)

**Extensions**: No custom fields required; using django-guardian for object-level permissions.

## Relationships

### Fast ↔ User
- **Type**: Many-to-One (Foreign Key)
- **Cascade**: ON DELETE CASCADE (when user deleted, their fasts are deleted)
- **Access Pattern**: Always filter fasts by user for privacy
- **Permissions**: Object-level permissions via django-guardian

## Database Schema

```sql
-- Fast table structure
CREATE TABLE fasting_fast (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    emotional_status VARCHAR(20) NULL,
    comments TEXT,
    created DATETIME NOT NULL,
    modified DATETIME NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    INDEX idx_fast_user_start (user_id, start_time DESC),
    INDEX idx_fast_user_end (user_id, end_time),
    
    CONSTRAINT chk_end_after_start CHECK (
        end_time IS NULL OR end_time >= start_time
    ),
    CONSTRAINT chk_comments_length CHECK (
        CHAR_LENGTH(comments) <= 128
    ),
    CONSTRAINT chk_emotional_status_values CHECK (
        emotional_status IN ('energized', 'satisfied', 'challenging', 'difficult') OR emotional_status IS NULL
    )
);
```

## Performance Considerations

### Indexing Strategy
- **Primary Index**: `(user_id, start_time DESC)` for fast history queries
- **Secondary Index**: `(user_id, end_time)` for active fast lookups
- **Built-in**: Primary key index on `id`

### Query Patterns
1. **Get user's fast history**: `SELECT * FROM fasting_fast WHERE user_id = ? ORDER BY start_time DESC`
2. **Get active fast**: `SELECT * FROM fasting_fast WHERE user_id = ? AND end_time IS NULL`
3. **Get fast details**: `SELECT * FROM fasting_fast WHERE id = ? AND user_id = ?`

### Scalability Features
- Pagination for fast history to handle large datasets
- Database-level constraints for data integrity
- Efficient indexes for common query patterns
- Soft deletion consideration for audit trails (handled by AuditableModel)

## Security Model

### Object-Level Permissions (django-guardian)
- Each Fast record has object-level permissions assigned to its owner
- Permissions: `view_fast`, `change_fast`, `delete_fast`
- Automatic permission assignment when Fast is created
- Permission checking in views and API endpoints

### Access Control Patterns
```python
# View-level permission checking
@permission_required_or_403('fasting.view_fast', (Fast, 'id', 'fast_id'))
def fast_detail_view(request, fast_id):
    pass

# QuerySet-level filtering
def get_user_fasts(user):
    return Fast.objects.filter(user=user)
```

## Data Validation

### Model-Level Validation
```python
def clean(self):
    # Validate end_time is after start_time
    if self.end_time and self.start_time and self.end_time <= self.start_time:
        raise ValidationError("End time must be after start time")
    
    # Validate emotional_status is provided when ending fast
    if self.end_time and not self.emotional_status:
        raise ValidationError("Emotional status is required when ending a fast")
    
    # Validate no multiple active fasts for same user
    if not self.end_time:  # Active fast
        existing_active = Fast.objects.filter(
            user=self.user, 
            end_time__isnull=True
        ).exclude(pk=self.pk)
        if existing_active.exists():
            raise ValidationError("User can only have one active fast at a time")
```

### Form-Level Validation
- Client-side validation for immediate feedback
- Server-side validation for security
- Character count display for comments field
- Date/time validation for reasonable ranges

## Migration Strategy

### Initial Migration
1. Create Fast model with all fields
2. Create database indexes
3. Set up django-guardian permissions
4. Create initial data fixtures if needed

### Data Migration Considerations
- No existing data to migrate (new feature)
- Consider creating superuser fasts for testing
- Set up guardian permissions for existing users

## Testing Data Model

### FactoryBoy Factories
```python
# healthy_herron/fasting/tests/factories.py
class FastFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Fast
    
    user = factory.SubFactory(UserFactory)
    start_time = factory.Faker('date_time_this_month')
    end_time = None  # Default to active fast
    emotional_status = None
    comments = factory.Faker('text', max_nb_chars=100)
    
    @factory.post_generation
    def assign_permissions(obj, create, extracted, **kwargs):
        if create:
            assign_perm('view_fast', obj.user, obj)
            assign_perm('change_fast', obj.user, obj)
            assign_perm('delete_fast', obj.user, obj)

class CompletedFastFactory(FastFactory):
    end_time = factory.Faker('date_time_this_month')
    emotional_status = factory.Iterator([choice[0] for choice in Fast.EMOTIONAL_STATUS_CHOICES])
```

This data model provides a solid foundation for the fasting tracker application, ensuring data integrity, performance, and security while meeting all functional requirements.