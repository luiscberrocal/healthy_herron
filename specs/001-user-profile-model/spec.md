# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently

  # Feature Specification: User Profile Model

  **Feature Branch**: `001-user-profile-model`
  **Created**: 2025-11-12
  **Status**: Draft
  **Input**: User description: "Add a Profile Django model to the users app. This Profile model should contain a one to one relationship with users. The profile should contain display_name, avatar and a configuration as a JSONField. Profiles should be created when a user is created. The default value for the configuration attribute should be: {\"fasting\":{\"min_fast_duration\": 30, \"max_fast_duration\": 1440}}. If the user is deleted the Profile should be deleted and the avatar image should be deleted too. The max size for the avatar image should be 2 MB. The accepted formats for the avatars are JPEG and PNG. The Profile model should contain a method that will create or updated configuration with this signature: def set_configuration(app_name:str, key:str, value: Any) -> dict[str, Any]:. Also should have a method to delete configuration with this signature: def delete_configuration(app_name:str, key:str|None) -> None: \"Delete configuration key. If key is none drop all app name values.\". Display name should allow emojis."

  ## User Scenarios & Testing *(mandatory)*

  ### User Story 1 - Profile Auto-Creation (Priority: P1)
  When a new user is created, a Profile is automatically created with default configuration.

  **Why this priority**: Ensures every user has a profile, enabling all other profile-related features.

  **Independent Test**: Register a user, verify Profile exists with correct default configuration.

  **Acceptance Scenarios**:
  1. **Given** a new user is registered, **When** registration completes, **Then** a Profile is created with default configuration.
  2. **Given** a user is deleted, **When** deletion completes, **Then** the Profile and avatar image are deleted.

  ---

  ### User Story 2 - Profile Update (Priority: P2)
  User updates display_name (including emojis) and uploads an avatar (JPEG/PNG, ≤2MB).

  **Why this priority**: Allows users to personalize their profile and visual identity.

  **Independent Test**: Update display_name with emojis, upload valid/invalid avatar files, check validation.

  **Acceptance Scenarios**:
  1. **Given** a user with a Profile, **When** display_name is updated with emojis, **Then** the new name is saved and displayed.
  2. **Given** a user with a Profile, **When** an avatar is uploaded, **Then** only JPEG/PNG ≤2MB are accepted; others are rejected.

  ---

  ### User Story 3 - Configuration Management (Priority: P3)
  User/system updates or deletes configuration via provided methods.

  **Why this priority**: Enables flexible, app-specific user settings.

  **Independent Test**: Call set_configuration and delete_configuration, verify configuration changes as expected.

  **Acceptance Scenarios**:
  1. **Given** a Profile, **When** set_configuration is called, **Then** the configuration is updated or created.
  2. **Given** a Profile, **When** delete_configuration is called, **Then** the specified key or app config is removed.

  ---

  ### Edge Cases
  - What happens if an avatar upload exceeds 2MB? (Rejected, user notified)
  - How does system handle unsupported avatar formats? (Rejected, user notified)
  - What if configuration is set with an invalid structure? (Validation error)
  - What if user is deleted but avatar file is missing? (No error, continue deletion)

  ## Requirements *(mandatory)*

  ### Functional Requirements
  - **FR-001**: System MUST create a Profile for each new user with a one-to-one relationship.
  - **FR-002**: Profile MUST include display_name (emoji support), avatar (JPEG/PNG, ≤2MB), and configuration (JSON, default: {"fasting":{"min_fast_duration": 30, "max_fast_duration": 1440}}).
  - **FR-003**: When a user is deleted, their Profile and avatar file MUST also be deleted.
  - **FR-004**: Avatar uploads MUST be validated for file type (JPEG/PNG) and size (≤2MB).
  - **FR-005**: Profile MUST provide set_configuration(app_name:str, key:str, value:Any) -> dict[str,Any].
  - **FR-006**: Profile MUST provide delete_configuration(app_name:str, key:str|None) -> None.
  - **FR-007**: set_configuration MUST create or update the specified configuration key.
  - **FR-008**: delete_configuration MUST remove the specified key, or all keys for the app if key is None.
  - **FR-009**: display_name MUST allow emojis.

  - **FR-010**: Configuration changes MUST overwrite previous values; no audit/history is required.

## Clarifications
### Session 2025-11-12
- Q: Should configuration changes be audited (history kept), or is overwrite sufficient? → A: Overwrite configuration (no history kept)

  ### Key Entities *(include if feature involves data)*
  - **User**: Represents an account in the system.
  - **Profile**: One-to-one with User, fields: display_name, avatar, configuration.
  - **Avatar**: Image file (JPEG/PNG, ≤2MB).
  - **Configuration**: JSON object, app-key-value structure.

  ## Success Criteria *(mandatory)*

  ### Measurable Outcomes
  - **SC-001**: 100% of new users have a Profile with correct default configuration.
  - **SC-002**: 100% of avatar uploads are rejected if not JPEG/PNG or >2MB.
  - **SC-003**: 100% of display_name updates allow emojis.
  - **SC-004**: 100% of configuration changes via methods are reflected in the Profile.
  - **SC-005**: 100% of Profile and avatar files are deleted when user is deleted.
  - **SC-006**: No orphaned avatar files remain after user deletion.

