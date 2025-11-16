# Quickstart: User Profile Model

## 1. Install dependencies
- Ensure `Pillow` is in `pyproject.toml` for image validation
- Run `pip install -r requirements.txt` if needed

## 2. Model Implementation
- Add `Profile` model to `healthy_herron/users/models.py`
- Inherit from `AuditableModel` and `TimeStampedModel`
- Add fields: user (OneToOne), display_name, avatar, configuration
- Add methods: set_configuration, delete_configuration
- Add validation for avatar (JPEG/PNG, ≤2MB)

## 3. Signals
- Create signal to auto-create Profile on user creation
- Create signal to delete avatar file on Profile deletion

## 4. Admin & Forms
- Register Profile in admin
- Add form validation for avatar field

## 5. Testing
- Write tests in `healthy_herron/users/tests/` using pytest and FactoryBoy
- Test profile creation, avatar upload/validation, configuration methods, deletion

## 6. Migrations
- Run `python manage.py makemigrations users && python manage.py migrate users`

## 7. API/Views (if needed)
- Add endpoints in `healthy_herron/users/api/` for profile CRUD

## 8. Lint & Check
- Run `ruff check .` and ensure PEP 8 compliance

## 9. Documentation
- Update README and user docs as needed
