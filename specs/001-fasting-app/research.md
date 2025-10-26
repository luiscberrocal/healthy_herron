# Research: Fasting Tracker App

**Date**: 2025-10-25  
**Phase**: 0 - Research & Design Decisions

## Research Tasks Completed

### 1. Django-Guardian Object-Level Permissions

**Decision**: Use django-guardian for implementing object-level permissions on Fast models

**Rationale**: 
- Requirement FR-012 explicitly states "System MUST restrict access so users can only view and modify their own fast records"
- Requirement FR-013 mandates "System MUST implement object-level permissions using django-guardian"
- Django's built-in permissions only handle model-level access, not instance-level
- django-guardian is the established Django library for object-level permissions

**Implementation Approach**:
- Use `@permission_required_or_403` decorators on views
- Implement custom manager methods for user-filtered querysets
- Use Guardian's `assign_perm()` to grant object permissions when Fast records are created
- Create mixin classes for permission checking in views

**Alternatives Considered**:
- Custom middleware for permission checking: Rejected due to complexity and maintainability concerns
- Manual QuerySet filtering in views: Rejected as it doesn't provide comprehensive security and violates DRY principle

### 2. Real-Time Updates Implementation

**Decision**: Use JavaScript with setInterval for 15-second elapsed time updates

**Rationale**:
- Requirement FR-006 specifies "System MUST update elapsed time automatically every 15 seconds for active fasts"
- Success Criteria SC-005 defines tolerance of ±2 seconds for update frequency
- Simple client-side JavaScript is sufficient for this use case without requiring WebSocket complexity
- Minimal server load compared to constant AJAX polling

**Implementation Approach**:
- JavaScript function to calculate elapsed time from start timestamp
- `setInterval()` with 15-second intervals
- Update DOM elements showing elapsed time
- Error handling for network failures with manual refresh option (FR-020)
- Page visibility API to pause updates when tab is inactive

**Alternatives Considered**:
- WebSocket real-time updates: Rejected due to added complexity and server infrastructure requirements for simple time display
- Server-sent events (SSE): Rejected as overkill for client-side time calculations
- AJAX polling every 15 seconds: Rejected due to unnecessary server load for time calculations

### 3. Emotional Status Data Model

**Decision**: Use Django choices field with predefined emotional states

**Rationale**:
- Requirement FR-007 specifies exactly four emotional states: "Energized, Satisfied, Challenging, Difficult"
- Fixed enumeration is appropriate for consistent data analysis and UI consistency
- Django choices provide built-in validation and display methods

**Implementation Approach**:
- Define `EMOTIONAL_STATUS_CHOICES` as tuple of tuples in Fast model
- Use `CharField` with `choices` parameter for validation
- Create choice constants for programmatic access
- Display choices as radio buttons or select dropdown in forms

**Alternatives Considered**:
- Separate EmotionalStatus model: Rejected as emotional states are fixed and unlikely to change
- Free-text emotional status: Rejected as it doesn't allow for consistent data analysis

### 4. Fast Model Duration Calculation

**Decision**: Calculate duration dynamically in model properties and database-level for queries

**Rationale**:
- Requirement FR-004 specifies duration calculation and display
- Requirement FR-005 requires elapsed hours display for both active and completed fasts
- Dynamic calculation ensures accuracy and consistency
- Property methods allow for easy template access

**Implementation Approach**:
- `@property` method for duration calculation using `end_time - start_time`
- `@property` method for elapsed time from start_time to current time
- Database annotations for filtering/ordering by duration
- Format duration display in human-readable format (hours and minutes)

**Alternatives Considered**:
- Store duration as separate field: Rejected due to data redundancy and potential inconsistency
- Calculate duration only in views: Rejected as it violates separation of concerns

### 5. Template Organization and Responsive Design

**Decision**: Use Tailwind CSS classes with mobile-first responsive design

**Rationale**:
- Constitution principle III mandates "Responsive Design (NON-NEGOTIABLE)"
- Requirement for templates in "fasting/templates" directory is explicitly stated
- Tailwind CSS is already configured in the project
- Mobile-first approach ensures optimal experience across devices

**Implementation Approach**:
- Create base template extending project's base.html
- Use Tailwind responsive prefixes (sm:, md:, lg:) for breakpoint-specific styling
- Implement CSS Grid/Flexbox for responsive layouts
- Optimize touch targets for mobile interaction
- Test across multiple screen sizes during development

**Alternatives Considered**:
- Custom CSS with media queries: Rejected as project already uses Tailwind CSS
- Bootstrap framework: Rejected as it would add unnecessary dependency when Tailwind is available

### 6. Form Validation and Error Handling

**Decision**: Implement comprehensive form validation with user-friendly error messages

**Rationale**:
- Requirement FR-016 mandates validation that "fast end time is after start time"
- Requirement FR-018 requires "user-friendly error messages for permission denials and validation failures"
- Requirement FR-019 enforces 128-character limit on comments
- Constitution principle II emphasizes "Error messages must be helpful and actionable"

**Implementation Approach**:
- Django ModelForm with custom clean() methods for cross-field validation
- Client-side validation for immediate feedback using HTML5 and JavaScript
- Custom form field validators for character limits and time validation
- Consistent error message formatting across all forms
- Loading states during form submission (FR-022)

**Alternatives Considered**:
- Server-side validation only: Rejected as it provides poor user experience
- Complex JavaScript validation frameworks: Rejected due to minimal dependencies principle

### 7. Database Query Optimization

**Decision**: Implement efficient querysets with select_related and prefetch_related for user isolation

**Rationale**:
- Performance requirement SC-010 mandates "2 seconds" response time for CRUD operations
- Scale requirement of "up to 100,000 fast records" requires efficient queries
- User isolation requires filtering by user in all queries

**Implementation Approach**:
- Custom manager methods that automatically filter by user
- Use `select_related('user')` for single fast queries
- Implement pagination for fast history lists
- Database indexes on user_id and timestamp fields
- QuerySet optimization for common access patterns

**Alternatives Considered**:
- Raw SQL queries: Rejected due to reduced maintainability and ORM benefits
- No query optimization: Rejected due to performance requirements

## Technology Decisions Summary

| Component | Technology | Justification |
|-----------|------------|---------------|
| Object Permissions | django-guardian | Required by specification, industry standard |
| Real-time Updates | JavaScript setInterval | Simple, efficient for time updates |
| Emotional Status | Django Choices | Fixed enumeration, built-in validation |
| Duration Calculation | Model Properties | Dynamic calculation, consistency |
| Responsive Design | Tailwind CSS | Already configured, mobile-first |
| Form Validation | Django Forms + HTML5 | Comprehensive validation, good UX |
| Query Optimization | Custom Managers | Performance requirements, user isolation |

## Architecture Patterns

### Model Layer
- Models inherit from `AuditableModel` and `TimeStampedModel` (constitution requirement)
- Object-level permissions using django-guardian
- Custom managers for user-filtered querysets
- Property methods for calculated fields (duration, elapsed time)

### View Layer  
- Class-based views exclusively (constitution requirement)
- Permission mixins for object-level access control
- Separate views for web pages and API endpoints
- Form views with comprehensive validation

### Template Layer
- Templates in `healthy_herron/templates/fasting/` (spec requirement)
- Responsive design with Tailwind CSS (constitution requirement)
- JavaScript for real-time updates
- Progressive enhancement for accessibility

### API Layer
- RESTful API design following Django REST Framework patterns
- Organized in `api` package within app (constitution requirement)
- Consistent JSON response formats
- API authentication and permissions

This research provides the foundation for implementing the fasting tracker app according to the specifications and constitution requirements.