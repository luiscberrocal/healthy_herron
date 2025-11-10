# Tasks: User Profile Model

## Phase 1: Setup
- [X] T001 Create/verify `healthy_herron/users/` app structure
- [X] T002 Add `Pillow` to `pyproject.toml` for image validation
- [X] T003 [P] Install dependencies via `pip install -r requirements.txt`
- [X] T004 [P] Ensure `pytest`, `FactoryBoy`, `Ruff`, `model_utils` in environment

## Phase 2: Foundational
- [X] T005 Create/verify `AuditableModel` and `TimeStampedModel` base classes in `healthy_herron/core/models.py`
- [X] T006 [P] Create/verify `managers.py` in `healthy_herron/users/` for custom managers
- [X] T007 [P] Create/verify `api/`, `migrations/`, `tests/` subfolders in `healthy_herron/users/`

## Phase 3: User Story 1 - Profile Auto-Creation (P1)
- [X] T008 [US1] Add `Profile` model to `healthy_herron/users/models.py` (fields: user, display_name, avatar, configuration)
- [X] T009 [US1] Inherit `Profile` from `AuditableModel` and `TimeStampedModel`
- [X] T010 [US1] Add default configuration logic to `Profile`
- [X] T011 [US1] Implement signal to auto-create Profile on user creation in `healthy_herron/users/signals.py`
- [X] T012 [US1] Implement signal to delete Profile and avatar on user deletion in `healthy_herron/users/signals.py`
- [X] T013 [US1] Register Profile in `healthy_herron/users/admin.py`
- [X] T014 [US1] Create migration for Profile model
- [X] T015 [US1] [P] Write pytest/FactoryBoy test for auto-creation of Profile
- [X] T016 [US1] [P] Write pytest/FactoryBoy test for Profile/Avatar deletion on user delete

## Phase 4: User Story 2 - Profile Update (P2)
- [X] T017 [US2] Add/validate display_name field for emoji/unicode in `models.py`
- [X] T018 [US2] Add avatar field (ImageField) with JPEG/PNG, ≤2MB validation in `models.py`
- [X] T019 [US2] Add/validate avatar upload logic in `forms.py` (if present)
- [X] T020 [US2] [P] Write pytest/FactoryBoy test for display_name with emojis
- [X] T021 [US2] [P] Write pytest/FactoryBoy test for avatar upload (valid/invalid cases)

## Phase 5: User Story 3 - Configuration Management (P3)
- [X] T022 [US3] Implement `set_configuration` method in `Profile` model
- [X] T023 [US3] Implement `delete_configuration` method in `Profile` model
- [X] T024 [US3] [P] Write pytest/FactoryBoy test for set_configuration
- [X] T025 [US3] [P] Write pytest/FactoryBoy test for delete_configuration

## Phase 6: API/Views (if needed)
- [X] T026 Add profile CRUD endpoints to `healthy_herron/users/api/` (urls.py, views.py, serializers.py)
- [X] T027 [P] Add configuration endpoints to `healthy_herron/users/api/` (urls.py, views.py, serializers.py)
- [X] T028 [P] Write pytest test for profile API endpoints
- [X] T029 [P] Write pytest test for configuration API endpoints

## Phase 7: Polish & Cross-Cutting
- [X] T030 [P] Run `ruff check .` and fix lint issues
- [X] T031 [P] Update README and user docs for profile feature
- [X] T032 [P] Review and refactor for constitution compliance

## Dependencies
- Phase 1 must complete before Phase 2
- Phase 2 must complete before any user story phases
- User stories are independent but should be implemented in priority order (P1 → P2 → P3)
- API/Views phase depends on Profile model and configuration methods
- Polish phase can be done in parallel after main features

## Parallel Execution Examples
- T003, T004 can run in parallel
- T006, T007 can run in parallel
- T015, T016 can run in parallel
- T020, T021 can run in parallel
- T024, T025 can run in parallel
- T027, T028, T029, T030, T031, T032 can run in parallel

## Implementation Strategy
- MVP: Complete all tasks for User Story 1 (T008–T016)
- Incrementally deliver User Story 2, then 3, then API/Polish

