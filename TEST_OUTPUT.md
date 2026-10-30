# Test run output

Environment: Python 3.11.9, Django 4.2.28, Windows. Final run used non-debug settings with temporary test-only values for `DJANGO_SECRET_KEY`, `BOX_API_TOKEN`, and `DJANGO_ALLOWED_HOSTS`. Do not use these placeholder values for deployment. GitHub Actions is configured for the same non-debug checks on Python 3.11; it will run after the repository is pushed.

Commands run from the project directory:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py seed_demo
python manage.py recommend_box DEMO-1
python manage.py test
```

Output:

```text
System check identified no issues (0 silenced).
No changes detected
Applying contenttypes.0001_initial... OK
Applying contenttypes.0002_remove_content_type_name... OK
Applying auth.0001_initial... OK
Applying auth.0002_alter_permission_name_max_length... OK
Applying auth.0003_alter_user_email_max_length... OK
Applying auth.0004_alter_user_username_opts... OK
Applying auth.0005_alter_user_last_login_null... OK
Applying auth.0006_require_contenttypes_0002... OK
Applying auth.0007_alter_validators_add_error_messages... OK
Applying auth.0008_alter_user_username_max_length... OK
Applying auth.0009_alter_user_last_name_max_length... OK
Applying auth.0010_alter_group_name_max_length... OK
Applying auth.0011_update_proxy_permissions... OK
Applying auth.0012_alter_user_first_name_max_length... OK
Applying inventory.0001_initial... OK
Applying inventory.0002_orderitem_order_item_quantity_positive_and_more... OK
Demo data ready. Try: python manage.py recommend_box DEMO-1
{
  "order": "DEMO-1",
  "box": {
    "id": 2,
    "name": "Medium",
    "cost": "2.50",
    "internal_cm": ["25.00", "20.00", "15.00"],
    "max_weight_kg": "8.000"
  },
  "total_weight_kg": "1.000",
  "total_volume_cm3": "1920.000000"
}
Found 28 test(s).
System check identified no issues (0 silenced).
............................
----------------------------------------------------------------------
Ran 28 tests in 0.272s

OK
Destroying test database...
```

The 28-test suite also passed under local development settings. The separate 20,000-case packing fuzz check (9,025 successful placements, zero invalid layouts) was reported by Claude; it is not part of the Django test suite. GitHub Actions has not yet run because the repository has not been pushed.
