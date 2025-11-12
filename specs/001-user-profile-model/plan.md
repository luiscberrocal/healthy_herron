
# Implementation Plan: User Profile Model

**Branch**: `001-user-profile-model` | **Date**: 2025-11-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-user-profile-model/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a Profile model to the users app with a one-to-one relationship to User, including display_name (emoji support), avatar (JPEG/PNG, ≤2MB), and configuration (JSONField with default). Profiles are auto-created on user creation and deleted (with avatar) on user deletion. Configuration is managed via set/delete methods. All code must comply with the Healthy Herron Constitution (Django best practices, clean code, test-first, etc).

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Django, Pillow (for image validation), FactoryBoy, pytest, Ruff, model_utils  
**Storage**: PostgreSQL (via Django ORM), file storage for avatars  
**Testing**: pytest, FactoryBoy, Ruff (linting)  
**Target Platform**: Linux server  
**Project Type**: Django web application  
**Performance Goals**: Profile creation/deletion in <200ms; avatar upload validation <500ms  
**Constraints**: Avatar ≤2MB, JPEG/PNG only, display_name supports emojis, configuration overwrite only  
**Scale/Scope**: Up to 10k users, 10k profiles, 10k avatar files  


## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- All code must be clean, readable, and maintainable (PEP 8, Ruff, no dead code)
- User interfaces must be simple, intuitive, and use HTMX for interactivity (no custom JS)
- All UI must be fully responsive (Tailwind CSS, no horizontal scroll on mobile)
- Minimize dependencies; justify any new ones (e.g., Pillow for image validation)
- All Django code under `healthy_herron` package; models inherit from `AuditableModel` and `TimeStampedModel`
- Custom model managers in `managers.py` only
- APIs in `api` package with class-based views
- Tests must be written first (pytest, FactoryBoy), high coverage, class-based
- All features must work without JavaScript (progressive enhancement)
- Any deviation from these standards must be explicitly justified and documented

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
