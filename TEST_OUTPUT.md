# Test run output

Environment: Python 3.11.9, Django 4.2.28, Windows. The local final run used non-debug settings with temporary test-only values for `DJANGO_SECRET_KEY`, `BOX_API_TOKEN`, and `DJANGO_ALLOWED_HOSTS`. Do not use those placeholder values for deployment.

Commands:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py seed_demo
python manage.py recommend_box DEMO-1
python manage.py test
```

Results:

```text
System check identified no issues (0 silenced).
No changes detected
Migrations applied successfully: contenttypes, auth, inventory.
Demo data ready. Try: python manage.py recommend_box DEMO-1
Recommendation for DEMO-1: Medium box, cost 2.50, total weight 1.000 kg, total volume 1920.000000 cm³.
Found 28 test(s).
System check identified no issues (0 silenced).
............................
Ran 28 tests in 0.272s

OK
```

The 28-test suite also passed under local development settings. Claude separately reported a 20,000-case packing fuzz check with 9,025 successful layouts and zero invalid placements; that was Claude’s reported result, not part of the Django test suite.

GitHub Actions also passed on `main`: [View the successful run](https://github.com/nishantkalane/box_selection_python_django/actions/runs/41066382540)
