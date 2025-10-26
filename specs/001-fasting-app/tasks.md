# Tasks: Fasting Tracker App

**Input**: Design documents from `/specs/001-fasting-app/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Summary

- **Total Tasks**: 45 tasks across 7 phases
- **User Stories**: 4 stories (US1-US4) with priority P1, P1, P2, P3
- **MVP Scope**: User Story 1 (Start New Fast) - 8 implementation tasks (T021-T021)
- **Parallel Opportunities**: 32 parallelizable tasks marked with [P]
- **Independent Test Criteria**: Each user story can be tested independently

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Django app structure

- [x] T001 Create healthy_herron.fasting Django app structure
- [x] T002 [P] Install django-guardian dependency in pyproject.toml
- [x] T003 [P] Configure Django settings for fasting app and guardian in config/settings/base.py
- [x] T004 [P] Create fasting app configuration in healthy_herron/fasting/apps.py
- [x] T005 [P] Setup URL routing in config/urls.py and healthy_herron/fasting/urls.py
- [x] T006 [P] Configure Tailwind CSS in base.html and remove Bootstrap dependencies from healthy_herron/templates/base.html
- [x] T007 [P] Add timezone field to User profile in healthy_herron/users/models.py and create migration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data model and authentication that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Create Fast model in healthy_herron/fasting/models.py with timezone methods
- [x] T009 [P] Create Guardian permission signals in healthy_herron/fasting/signals.py
- [x] T010 [P] Create FactoryBoy test factories in healthy_herron/fasting/tests/factories.py
- [x] T011 Create and apply Django migrations for Fast model
- [x] T012 [P] Setup session management utilities in healthy_herron/fasting/models.py
- [x] T013 [P] Create base fasting templates directory structure
- [x] T014 [P] Implement loading spinner components and HTMX indicators in healthy_herron/templates/components/loading.html

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Start New Fast (Priority: P1) 🎯 MVP

**Goal**: Allow users to begin tracking a new fasting period by recording the start time

**Independent Test**: Log in, click "Start Fast", verify new fast record created with current timestamp and user ownership

### Implementation for User Story 1

- [x] T015 [P] [US1] Create StartFastForm in healthy_herron/fasting/forms.py
- [x] T016 [P] [US1] Create StartFastView class-based view in healthy_herron/fasting/views.py
- [x] T017 [P] [US1] Create start_fast.html template in healthy_herron/fasting/templates/fasting/
- [x] T018 [P] [US1] Create dashboard view function in healthy_herron/fasting/views.py
- [x] T019 [P] [US1] Create dashboard.html template with HTMX timer in healthy_herron/fasting/templates/fasting/
- [x] T020 [P] [US1] Create fasting CSS styles using Tailwind classes in healthy_herron/static/css/fasting.css
- [x] T021 [US1] Implement Fast model validation preventing multiple active fasts
- [x] T022 [US1] Add URL patterns for start fast and dashboard in healthy_herron/fasting/urls.py

**Checkpoint**: At this point, User Story 1 should be fully functional - users can start fasts and see dashboard

---

## Phase 4: User Story 2 - End Active Fast (Priority: P1)

**Goal**: Allow users to complete their current fasting period by recording end time, emotional state, and comments

**Independent Test**: Start a fast, click "End Fast", select emotional state, add comments, verify all data recorded

### Implementation for User Story 2

- [x] T023 [P] [US2] Create EndFastForm with emotional status validation in healthy_herron/fasting/forms.py
- [x] T024 [P] [US2] Create EndFastView with concurrency locking in healthy_herron/fasting/views.py
- [x] T025 [P] [US2] Create end_fast.html template with emotional status choices in healthy_herron/fasting/templates/fasting/
- [x] T026 [P] [US2] Implement FastTimerView for HTMX polling in healthy_herron/fasting/views.py
- [x] T027 [US2] Add Fast model clean() validation for end time requirements
- [x] T028 [US2] Add URL patterns for end fast and timer endpoints in healthy_herron/fasting/urls.py

**Checkpoint**: Users can now complete full fasting cycles with emotional tracking

---

## Phase 5: User Story 3 - View Fasting History (Priority: P2)

**Goal**: Allow users to see their complete history of completed fasts to track patterns and progress

**Independent Test**: Create multiple completed fasts, verify they appear in chronological order with duration calculations

### Implementation for User Story 3

- [x] T029 [P] [US3] Create FastListView with pagination in healthy_herron/fasting/views.py
- [x] T030 [P] [US3] Create FastDetailView with permission checking in healthy_herron/fasting/views.py
- [x] T031 [P] [US3] Create fast_list.html template with responsive layout in healthy_herron/fasting/templates/fasting/
- [x] T032 [P] [US3] Create fast_detail.html template with HTMX timer in healthy_herron/fasting/templates/fasting/
- [x] T033 [US3] Add Fast model duration and formatting properties for display
- [x] T034 [US3] Add URL patterns for fast list and detail views in healthy_herron/fasting/urls.py

**Checkpoint**: Users can now view and analyze their complete fasting history

---

## Phase 6: User Story 4 - Edit Fast Details (Priority: P3)

**Goal**: Allow users to modify start/end times, emotional status, and comments of previously recorded fasts

**Independent Test**: Edit existing fast's times and emotional status, verify changes saved and duration recalculated

### Implementation for User Story 4

- [x] T035 [P] [US4] Create FastUpdateView with permission validation in healthy_herron/fasting/views.py
- [x] T036 [P] [US4] Create fast_form.html template for editing in healthy_herron/fasting/templates/fasting/
- [x] T037 [P] [US4] Create FastDeleteView with confirmation dialog in healthy_herron/fasting/views.py
- [x] T038 [US4] Add Fast model validation for edit operations
- [x] T039 [US4] Add URL patterns for fast update and delete views in healthy_herron/fasting/urls.py

**Checkpoint**: Users can now correct and update their fasting records

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final touches and system-wide improvements

- [x] T038 [P] Add export data functionality in healthy_herron/fasting/views.py
- [x] T039 [P] Implement automatic archival system for fast records older than 2 years in healthy_herron/fasting/management/commands/archive_old_fasts.py
- [x] T040 [P] Create comprehensive model tests in healthy_herron/fasting/tests/test_models.py
- [x] T041 [P] Create view tests with permission checking in healthy_herron/fasting/tests/test_views.py
- [x] T042 [P] Create form validation tests in healthy_herron/fasting/tests/test_forms.py
- [x] T043 [P] Add Django admin interface for Fast model in healthy_herron/fasting/admin.py

---

## Dependencies

### User Story Completion Order

```text
Phase 1 (Setup) → Phase 2 (Foundation) → All User Stories can run in parallel

User Story 1 (MVP) ← Independent
User Story 2       ← Depends on US1 (needs Fast model)
User Story 3       ← Independent (can use existing Fast records)
User Story 4       ← Depends on US3 (needs fast detail views)
```

### Critical Dependencies

- **Foundation Phase**: Must complete before any user story work
- **US1 (Start Fast)**: Blocks US2 (need fasts to end)
- **US3 (View History)**: Blocks US4 (need detail views to edit)
- **All other tasks**: Can run in parallel within phases

## Parallel Execution Examples

### Phase 2 Foundation (can work in parallel):
- Developer A: Fast model (T006)
- Developer B: Permission signals (T007) + Test factories (T008)
- Developer C: Session utilities (T010) + Template structure (T011)

### Phase 3 User Story 1 (can work in parallel):
- Developer A: Forms (T012) + Views (T021)
- Developer B: Templates (T021, T021) + CSS (T021)
- Developer C: Validation (T021) + URLs (T021)

### Phase 4-6 User Stories (can work in parallel):
- Developer A: US2 (End Fast)
- Developer B: US3 (View History)  
- Developer C: US4 (Edit Details)

## Implementation Strategy

### MVP Delivery (Phase 1-3)
Focus on User Story 1 for initial release:
- Basic fast tracking (start/end)
- Dashboard with timer
- User authentication and permissions
- **Estimated effort**: 8 implementation tasks (T007-T021)

### Incremental Releases
- **Release 1**: US1 (Start Fast) - Core functionality
- **Release 2**: US1 + US2 (End Fast) - Complete cycle
- **Release 3**: US1 + US2 + US3 (History) - Analytics
- **Release 4**: All features + US4 (Edit) - Full feature set

### Testing Strategy
Each user story can be tested independently:
- **US1**: Create account → Start fast → Verify dashboard timer
- **US2**: Start fast → End fast → Verify emotional status saved  
- **US3**: Multiple fasts → View history → Verify chronological order
- **US4**: Existing fast → Edit details → Verify changes saved

This task structure enables parallel development while maintaining clear dependencies and deliverable increments.