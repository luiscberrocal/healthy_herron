# Healthy Herron Constitution

<!--
Sync Impact Report (2025-11-09):
Version: 0.0.0 → 1.0.0 (Initial constitution establishment)

Modified Principles:
- NEW: I. Clean Code (code quality and maintainability standards)
- NEW: II. Simple UX (user experience with HTMX-only interactivity)
- NEW: III. Responsive Design (NON-NEGOTIABLE - mobile-first approach)
- NEW: IV. Minimal Dependencies (dependency management philosophy)
- NEW: V. Django Best Practices (Django-specific architectural standards)

Added Sections:
- Frontend Interaction Standards (HTMX-only policy)
- Django Architecture Standards (app structure, model patterns)
- Testing Standards (pytest, FactoryBoy requirements)

Template Consistency Checks:
✅ plan-template.md - Constitution Check section aligns with principles
✅ spec-template.md - Requirements format supports testable, unambiguous requirements
✅ tasks-template.md - Task categorization supports principle-driven development
✅ All command templates - Generic guidance, no agent-specific references

Follow-up TODOs: None - all placeholders filled
-->

## Core Principles

### I. Clean Code

All code MUST be clean, readable, and maintainable. Functions and classes must have single responsibilities. Code must be self-documenting with meaningful names. Complex logic requires explanatory comments. Follow PEP 8 and use Ruff for linting. No dead code or commented-out code blocks in production branches.

**Rationale**: Clean code reduces cognitive load, facilitates onboarding, minimizes bugs, and ensures long-term maintainability. Single responsibility and self-documenting code eliminate the need for extensive external documentation that often becomes outdated.

### II. Simple UX

User interfaces MUST prioritize simplicity and usability over feature complexity. Every user interaction should be intuitive and require minimal cognitive load. Navigation must be clear and consistent. Error messages must be helpful and actionable. Forms should validate input client-side where possible. All interactive features MUST use HTMX for dynamic behavior - JavaScript is prohibited except for HTMX integration. HTMX provides the necessary interactivity while maintaining simplicity and reducing client-side complexity.

**Rationale**: Simplicity directly correlates with user adoption and satisfaction. HTMX-only policy eliminates the complexity of JavaScript frameworks, reduces bundle sizes, improves accessibility, and keeps frontend logic server-side where it can be tested and maintained alongside business logic.

### III. Responsive Design (NON-NEGOTIABLE)

All user interfaces MUST be fully responsive across desktop, tablet, and mobile devices. Use Tailwind CSS for consistent styling. Test on multiple screen sizes during development. No horizontal scrolling on mobile devices. Touch targets must be appropriately sized for mobile interaction.

**Rationale**: Mobile-first is non-negotiable in modern web development. Users access applications from various devices, and poor mobile experience leads to immediate abandonment. Tailwind CSS provides consistency and maintainability across the design system.

### IV. Minimal Dependencies

Prefer existing libraries from `pyproject.toml` over adding new dependencies. New dependencies require explicit justification and approval. Each dependency must provide significant value that outweighs maintenance overhead. Regular dependency audits for security and relevance. Remove unused dependencies promptly.

**Rationale**: Each dependency adds attack surface, maintenance burden, potential version conflicts, and increased build times. Dependencies must earn their place by providing value that significantly exceeds these costs.

### V. Django Best Practices

All Django apps MUST be created under the `healthy_herron` package. Models must inherit from both `core.models.AuditableModel` and `model_utils.models.TimeStampedModel`. Tests must be organized in a `tests` package within each app. Use class-based pytest tests exclusively. Create FactoryBoy factories for every model in the tests package. APIs must be organized in an `api` package within each app containing `urls.py`, `views.py`, and `serializers.py`. Use class-based views exclusively for both APIs and web pages.

**Model Managers Location**: All custom model managers MUST be defined in a separate `managers.py` module within the app. Managers MUST NOT be included in `models.py`. This ensures separation of concerns and improves maintainability.

**Rationale**: Consistent project structure eliminates decision fatigue and enables developers to navigate the codebase intuitively. Auditable models ensure data integrity and traceability. Factory-based testing provides reliable, maintainable test data. Separation of concerns (managers in separate files, API code in dedicated packages) improves code organization and testability.

## Frontend Interaction Standards

All dynamic user interactions must follow these patterns:

- **HTMX Only**: Use HTMX for all interactive features (real-time updates, form submissions, content loading)
- **No JavaScript**: Custom JavaScript is prohibited - all interactivity via HTMX attributes and server responses
- **Progressive Enhancement**: Features must work without JavaScript, enhanced with HTMX
- **Server-Side Rendering**: Dynamic content generated on server, returned as HTML fragments
- **HTMX Integration**: Include HTMX library as the sole client-side dependency for interactivity

**Rationale**: HTMX leverages HTML-over-the-wire architecture, keeping business logic on the server where it belongs. This approach simplifies debugging, improves security (no client-side logic to exploit), enhances accessibility, and reduces the need for API versioning. Progressive enhancement ensures baseline functionality for all users.

## Django Architecture Standards

All code must follow Django conventions and project-specific patterns:

- **App Structure**: New Django apps created under `healthy_herron` package only
- **Model Inheritance**: All models inherit from `AuditableModel` and `TimeStampedModel`
- **URL Patterns**: Follow RESTful conventions where applicable
- **Views**: Use class-based views exclusively for both web pages and APIs
- **API Organization**: APIs organized in `api` package within each app with `urls.py`, `views.py`, `serializers.py`
- **Templates**: Use Django template inheritance, organize in logical hierarchies
- **Managers**: All custom model managers MUST be placed in `managers.py` and NOT in `models.py`

**Rationale**: Consistent architecture patterns reduce cognitive overhead when switching between apps. Class-based views provide reusable mixins and inheritance. Centralized API organization makes endpoints discoverable. Template inheritance prevents duplication. Manager separation keeps model files focused on data structure rather than query logic.

## Testing Standards

Comprehensive testing is mandatory for all code:

- **Test Framework**: Use pytest with class-based test organization
- **Test Factories**: Create FactoryBoy factories for all models in `tests/factories.py`
- **Test Location**: Tests organized in `tests` package within each Django app
- **Coverage**: Maintain high test coverage, focus on business logic and edge cases
- **Test Types**: Unit tests for individual functions/methods, integration tests for workflows

**Rationale**: pytest provides powerful fixtures and better assertion messages than unittest. FactoryBoy generates realistic test data without database fixtures, improving test maintainability and speed. Class-based organization groups related tests logically. High coverage, especially of business logic, prevents regressions and documents expected behavior.

## Governance

This constitution supersedes all other development practices and guidelines. All code reviews and pull requests MUST verify compliance with these principles. Any complexity or deviation from these principles must be explicitly justified and documented.

Constitution amendments require:
1. Written proposal with rationale for changes
2. Review by project maintainers
3. Migration plan for existing code if applicable
4. Update of all dependent templates and documentation

All development decisions must align with these principles. When in doubt, choose the simpler, more maintainable solution.

**Versioning Policy**: Constitution follows semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Backward incompatible governance changes or principle removals/redefinitions
- **MINOR**: New principles added or materially expanded guidance
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

**Compliance Review**: All specifications, plans, and tasks must pass constitution checks before implementation. Use the Constitution Check gate in plan templates to verify compliance.

**Version**: 1.0.0 | **Ratified**: 2025-11-09 | **Last Amended**: 2025-11-09
