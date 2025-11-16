# Research for User Profile Model

## Decision: Configuration Overwrite Only
- Configuration changes will overwrite previous values; no audit/history is required.
- Rationale: Simpler, aligns with typical user profile settings, no regulatory need for audit trail.
- Alternatives considered: Full audit/history, rolling history (last N changes)

## Decision: Use Pillow for Avatar Validation
- Pillow will be used for image format and size validation.
- Rationale: Standard for Django image handling, already widely used, minimal dependency.
- Alternatives considered: Custom validation, other image libraries

## Decision: Emoji Support in display_name
- Use Unicode-compatible CharField for display_name.
- Rationale: Unicode CharField supports emojis natively in Django/PostgreSQL.
- Alternatives considered: Custom field, third-party packages

## Decision: Profile Auto-Creation via Signal
- Use Django signals to auto-create Profile on user creation.
- Rationale: Standard pattern for one-to-one profile models in Django.
- Alternatives considered: Manual creation in registration flow

## Decision: Avatar Deletion on User/Profile Delete
- Use Django's storage API and model signals to delete avatar files when Profile is deleted.
- Rationale: Prevents orphaned files, aligns with best practices.
- Alternatives considered: Periodic cleanup scripts

## Decision: Test-First Development
- All code will be developed with tests written first, using pytest and FactoryBoy.
- Rationale: Required by constitution, ensures quality and maintainability.
- Alternatives considered: None (non-negotiable)
