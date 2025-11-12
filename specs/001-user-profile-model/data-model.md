# Data Model: User Profile Model

## Entity: Profile
- user: OneToOneField to User (unique, required)
- display_name: CharField (emoji/unicode support, required)
- avatar: ImageField (JPEG/PNG, max 2MB, optional)
- configuration: JSONField (default: {"fasting":{"min_fast_duration": 30, "max_fast_duration": 1440}})

## Entity: User
- Standard Django User model (referenced by Profile)

## Validation Rules
- display_name: Must allow emojis (unicode)
- avatar: Only JPEG/PNG, ≤2MB
- configuration: Must be valid JSON, overwrite only

## State Transitions
- On user creation: Profile auto-created
- On user deletion: Profile and avatar deleted
- On avatar update: Old avatar file deleted (if replaced)

## Relationships
- User 1:1 Profile
