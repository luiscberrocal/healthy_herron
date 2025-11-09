# Data Model: Fasting Tracker App

**Date**: 2025-10-25  
**Phase**: 1 - Data Model Design

## Entity Overview

The fasting tracker application centers around tracking fasting periods for individual users with emotional status tracking, timezone support, data archival, and concurrency management.

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
| `start_time` | DateTimeField | When the fast began | timezone-aware | Yes |
| `end_time` | DateTimeField | When the fast ended | timezone-aware, null=True, blank=True | No |
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
- `duration_seconds`: Total duration in seconds for HTMX updates
- `elapsed_seconds`: Total elapsed time in seconds for HTMX updates

**Methods**:
- `end_fast(emotional_status, comments='')`: Complete the fast with emotional status
- `get_absolute_url()`: URL to fast detail view
- `to_user_timezone(dt, user)`: Convert datetime to user's configured timezone
- `from_user_timezone(dt, user)`: Convert datetime from user's timezone to UTC
- `__str__()`: String representation for admin and debugging

**Managers**:
- `FastManager`: Custom manager with user-filtered querysets and concurrency control
  - `for_user(user)`: Return fasts belonging to specific user
  - `active_for_user(user)`: Return active (unfinished) fasts for user
  - `completed_for_user(user)`: Return completed fasts for user
  - `with_lock()`: Apply database-level locking for concurrent operations

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

## Timezone Handling (FR-026)

### Design Approach
- Store all datetime fields in UTC in the database
- Convert to user's timezone for display and input
- Use Django's timezone utilities for consistent handling

### Model Methods for Timezone Conversion
```python
def to_user_timezone(self, user_timezone=None):
    """Convert stored UTC times to user's timezone"""
    if user_timezone is None:
        user_timezone = getattr(self.user, 'timezone', 'UTC')
    
    tz = zoneinfo.ZoneInfo(user_timezone)
    return {
        'start_time': self.start_time.astimezone(tz),
        'end_time': self.end_time.astimezone(tz) if self.end_time else None,
        'created': self.created.astimezone(tz),
        'modified': self.modified.astimezone(tz)
    }

def from_user_timezone(self, start_time, end_time=None, user_timezone=None):
    """Convert user input times to UTC for storage"""
    if user_timezone is None:
        user_timezone = getattr(self.user, 'timezone', 'UTC')
    
    tz = zoneinfo.ZoneInfo(user_timezone)
    
    # Ensure times are timezone-aware
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=tz)
    if end_time and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=tz)
    
    return {
        'start_time': start_time.astimezone(timezone.utc),
        'end_time': end_time.astimezone(timezone.utc) if end_time else None
    }
```

### User Timezone Storage
- Add `timezone` field to User profile or use session-based storage
- Default to UTC if no timezone specified
- Support for major timezones via Python's zoneinfo

## Concurrency Control (FR-027)

### Database-Level Locking
```python
# Manager method for safe concurrent access
class FastManager(models.Manager):
    def with_lock(self):
        """Get queryset with row-level locking for updates"""
        return self.select_for_update()

# Usage in views
def end_fast_view(request, fast_id):
    with transaction.atomic():
        fast = Fast.objects.with_lock().get(id=fast_id, user=request.user)
        if fast.end_time:
            raise ValidationError("Fast already ended")
        fast.end_time = timezone.now()
        fast.save()
```

### Optimistic Locking Strategy
- Use model timestamps for version control
- Check modified timestamp before updates
- Handle concurrent modification gracefully

### HTMX-Specific Features
```python
# Properties for HTMX polling updates
@property
def duration_seconds(self):
    """Duration in seconds for HTMX timer updates"""
    if not self.end_time:
        return int((timezone.now() - self.start_time).total_seconds())
    return int((self.end_time - self.start_time).total_seconds())

@property
def elapsed_seconds(self):
    """Alias for duration_seconds for clarity in templates"""
    return self.duration_seconds

def is_recently_modified(self, seconds=30):
    """Check if record was modified recently for HTMX updates"""
    return (timezone.now() - self.modified).total_seconds() < seconds
```

## Performance Considerations

### Indexing Strategy
- **Primary Index**: `(user_id, start_time DESC)` for fast history queries
- **Secondary Index**: `(user_id, end_time)` for active fast lookups
- **Timezone Index**: `(user_id, start_time DESC, end_time)` for timezone queries
- **Built-in**: Primary key index on `id`

### Query Patterns
1. **Get user's fast history**: `SELECT * FROM fasting_fast WHERE user_id = ? ORDER BY start_time DESC`
2. **Get active fast**: `SELECT * FROM fasting_fast WHERE user_id = ? AND end_time IS NULL`
3. **Get fast details**: `SELECT * FROM fasting_fast WHERE id = ? AND user_id = ?`
4. **Check for recent updates**: `SELECT * FROM fasting_fast WHERE user_id = ? AND modified > ?`

### Scalability Features
- Pagination for fast history to handle large datasets
- Database-level constraints for data integrity
- Efficient indexes for common query patterns
- Row-level locking for concurrent access
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

## Session Management (FR-028)

### Session Timeout Handling
- Configure Django session timeout for security
- Track user's last activity for fast management
- Handle session expiration during active fasts

### Session State Management
```python
# Session keys for fasting app
SESSION_KEYS = {
    'ACTIVE_FAST_ID': 'fasting_active_fast_id',
    'TIMEZONE': 'user_timezone',
    'LAST_ACTIVITY': 'last_activity'
}

def get_active_fast_from_session(request):
    """Retrieve active fast from session for quick access"""
    fast_id = request.session.get(SESSION_KEYS['ACTIVE_FAST_ID'])
    if fast_id:
        try:
            return Fast.objects.get(id=fast_id, user=request.user, end_time__isnull=True)
        except Fast.DoesNotExist:
            # Clean up stale session data
            del request.session[SESSION_KEYS['ACTIVE_FAST_ID']]
    return None

def set_active_fast_in_session(request, fast):
    """Store active fast in session"""
    request.session[SESSION_KEYS['ACTIVE_FAST_ID']] = fast.id
```

### HTMX Session Integration
- Use session data for real-time timer updates
- Handle session timeout gracefully in HTMX requests
- Maintain timer state across page refreshes

## Data Archival Strategy (FR-025)

### Archival Policy
- Keep all fast records for user analysis and history
- No automatic deletion of user data
- Support for user-requested data export/deletion (GDPR compliance)

### Data Export Functionality
```python
def export_user_fasts(user, format='json'):
    """Export user's fast data for archival or transfer"""
    fasts = Fast.objects.filter(user=user).order_by('-start_time')
    
    if format == 'json':
        return {
            'user_id': user.id,
            'export_date': timezone.now().isoformat(),
            'fasts': [
                {
                    'id': fast.id,
                    'start_time': fast.start_time.isoformat(),
                    'end_time': fast.end_time.isoformat() if fast.end_time else None,
                    'duration_hours': fast.duration_hours if fast.end_time else None,
                    'emotional_status': fast.emotional_status,
                    'comments': fast.comments,
                    'created': fast.created.isoformat(),
                    'modified': fast.modified.isoformat()
                }
                for fast in fasts
            ]
        }
```

### Data Retention
- No automatic purging of old records
- Support for user-initiated deletion
- Maintain referential integrity
- Consider database partitioning for large datasets

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
    start_time = factory.Faker('date_time_this_month', tzinfo=timezone.utc)
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
    end_time = factory.Faker('date_time_this_month', tzinfo=timezone.utc)
    emotional_status = factory.Iterator([choice[0] for choice in Fast.EMOTIONAL_STATUS_CHOICES])

class TimezoneTestFactory(FastFactory):
    """Factory for testing timezone conversions"""
    start_time = factory.LazyAttribute(
        lambda obj: timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
    )
    
    @factory.post_generation
    def set_user_timezone(obj, create, extracted, **kwargs):
        if create and extracted:
            obj.user.timezone = extracted
            obj.user.save()
```

### Test Cases for New Features
```python
class TestTimezoneHandling(TestCase):
    def test_to_user_timezone_conversion(self):
        """Test UTC to user timezone conversion"""
        fast = TimezoneTestFactory(set_user_timezone='America/New_York')
        user_times = fast.to_user_timezone()
        self.assertIsNotNone(user_times['start_time'].tzinfo)
    
    def test_from_user_timezone_conversion(self):
        """Test user timezone to UTC conversion"""
        fast = TimezoneTestFactory()
        user_time = timezone.now().replace(tzinfo=zoneinfo.ZoneInfo('Europe/London'))
        utc_times = fast.from_user_timezone(user_time)
        self.assertEqual(utc_times['start_time'].tzinfo, timezone.utc)

class TestConcurrencyControl(TestCase):
    def test_with_lock_queryset(self):
        """Test row-level locking for concurrent access"""
        fast = FastFactory()
        locked_fast = Fast.objects.with_lock().get(id=fast.id)
        self.assertEqual(fast.id, locked_fast.id)
    
    def test_duration_seconds_property(self):
        """Test HTMX duration calculation"""
        fast = FastFactory()
        self.assertIsInstance(fast.duration_seconds, int)
        self.assertGreater(fast.duration_seconds, 0)

class TestSessionManagement(TestCase):
    def test_active_fast_session_storage(self):
        """Test storing active fast in session"""
        request = RequestFactory().get('/')
        request.session = {}
        fast = FastFactory()
        set_active_fast_in_session(request, fast)
        self.assertEqual(request.session['fasting_active_fast_id'], fast.id)

class TestDataArchival(TestCase):
    def test_export_user_fasts(self):
        """Test data export functionality"""
        user = UserFactory()
        FastFactory.create_batch(3, user=user)
        export_data = export_user_fasts(user)
        self.assertEqual(len(export_data['fasts']), 3)
        self.assertIn('export_date', export_data)
```

This data model provides a solid foundation for the fasting tracker application, ensuring data integrity, performance, and security while meeting all functional requirements.