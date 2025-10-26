<!-- Sync Impact Report:
Version change: N/A → 1.0.0 (initial constitution)
Added sections: Django Architecture Standards, Testing Standards
New principles: Clean Code, Simple UX, Responsive Design, Minimal Dependencies, Django Best Practices
Templates requiring updates: ⚠ pending manual review of all templates
Follow-up TODOs: None
-->

# Healthy Herron Constitution

## Core Principles

### I. Clean Code
All code MUST be clean, readable, and maintainable. Functions and classes must have single responsibilities. Code must be self-documenting with meaningful names. Complex logic requires explanatory comments. Follow PEP 8 and use Ruff for linting. No dead code or commented-out code blocks in production branches.

### II. Simple UX
User interfaces MUST prioritize simplicity and usability over feature complexity. Every user interaction should be intuitive and require minimal cognitive load. Navigation must be clear and consistent. Error messages must be helpful and actionable. Forms should validate input client-side where possible.

### III. Responsive Design (NON-NEGOTIABLE)
All user interfaces MUST be fully responsive across desktop, tablet, and mobile devices. Use Tailwind CSS for consistent styling. Test on multiple screen sizes during development. No horizontal scrolling on mobile devices. Touch targets must be appropriately sized for mobile interaction.

### IV. Minimal Dependencies
Prefer existing libraries from `pyproject.toml` over adding new dependencies. New dependencies require explicit justification and approval. Each dependency must provide significant value that outweighs maintenance overhead. Regular dependency audits for security and relevance. Remove unused dependencies promptly.

### V. Django Best Practices
All Django apps MUST be created under the `healthy_herron` package. Models must inherit from both `core.models.AuditableModel` and `model_utils.models.TimeStampedModel`. Tests must be organized in a `tests` package within each app. Use class-based pytest tests exclusively. Create FactoryBoy factories for every model in the tests package.

## Django Architecture Standards

All code must follow Django conventions and project-specific patterns:

- **App Structure**: New Django apps created under `healthy_herron` package only
- **Model Inheritance**: All models inherit from `AuditableModel` and `TimeStampedModel`  
- **URL Patterns**: Follow RESTful conventions where applicable
- **Views**: Prefer class-based views for consistency and reusability
- **Templates**: Use Django template inheritance, organize in logical hierarchies

## Testing Standards

Comprehensive testing is mandatory for all code:

- **Test Framework**: Use pytest with class-based test organization
- **Test Factories**: Create FactoryBoy factories for all models in `tests/factories.py`
- **Test Location**: Tests organized in `tests` package within each Django app
- **Coverage**: Maintain high test coverage, focus on business logic and edge cases
- **Test Types**: Unit tests for individual functions/methods, integration tests for workflows

## Governance

This constitution supersedes all other development practices and guidelines. All code reviews and pull requests MUST verify compliance with these principles. Any complexity or deviation from these principles must be explicitly justified and documented.

Constitution amendments require:
1. Written proposal with rationale for changes
2. Review by project maintainers  
3. Migration plan for existing code if applicable
4. Update of all dependent templates and documentation

All development decisions must align with these principles. When in doubt, choose the simpler, more maintainable solution.

**Version**: 1.0.0 | **Ratified**: 2025-10-25 | **Last Amended**: 2025-10-25
