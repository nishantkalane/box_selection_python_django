# Django Box Selection

A small Django system that recommends a low-cost shipping box for an ecommerce order. It checks the products' dimensions and total weight, then tries to place each unit inside active boxes without overlap.

## Features

- Product, shipping box, order, and order item models with database constraints.
- Rotation-aware packing heuristic for multiple products and quantities.
- Cheapest eligible box recommendation with deterministic tie-breaking.
- Read-only JSON endpoint, a `recommend_box` command, and a `seed_demo` command for sample data.
- 28 tests and a GitHub Actions workflow.

## Architecture

```text
config/                         Django settings and URL configuration
inventory/models.py             Product, ShippingBox, Order, OrderItem
inventory/packing.py            Recommendation and packing logic
inventory/views.py               JSON recommendation endpoint
inventory/management/commands/   `recommend_box` and `seed_demo` commands
inventory/migrations/            Database schema migrations
inventory/tests.py               Model, packing, endpoint, command tests
.github/workflows/tests.yml      CI checks on pushes and pull requests
```

`Order` links to `Product` through `OrderItem`, which stores each product's quantity. Dimensions are in centimetres, weight in kilograms, and box cost is a decimal amount.

## Recommendation algorithm

`inventory.packing.recommend_box(order)` checks active boxes in cost order. It filters by maximum weight and total volume, then attempts to place every unit using an extreme-point, first-fit-decreasing heuristic. Each item may use any of its six axis-aligned orientations. If a box passes, the function returns it along with total weight and volume; otherwise it returns `None`. An empty order also returns `None`. Orders above 100 units raise `OrderTooLarge`.

The placement check is **sound**: a box is returned only when the heuristic finds an actual non-overlapping placement. It is **not complete**: its greedy placement choices can miss a valid arrangement, which may lead to choosing a larger box. It does not model padding, fragile items, orientation labels, non-rectangular products, or weight distribution.

## Install and run

Python 3.10 or newer is recommended. From PowerShell in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py test
```

Quickest way to try it: `python manage.py seed_demo`, then `python manage.py recommend_box DEMO-1` (orders DEMO-1 to DEMO-3).

Or create sample data manually using the Django shell:

```powershell
python manage.py shell
```

Then enter:

```python
from inventory.models import Product, ShippingBox, Order, OrderItem

mug = Product.objects.create(name="Mug", length_cm=10, width_cm=8, height_cm=12, weight_kg="0.500")
ShippingBox.objects.create(name="Medium", length_cm=20, width_cm=20, height_cm=20, max_weight_kg=5, cost="2.50")
order = Order.objects.create(reference="ORD-1")
OrderItem.objects.create(order=order, product=mug, quantity=2)
```

Exit the shell and request a recommendation:

```powershell
python manage.py recommend_box ORD-1
python manage.py runserver
```

The API endpoint is `GET http://127.0.0.1:8000/orders/ORD-1/box/`. It returns JSON with the order, selected box, total weight, and total volume. Unknown orders return 404; orders over 100 units return 422. `POST` is not supported.

## Configuration and security

Local development defaults to `DEBUG=True` and a development-only secret. Do not deploy with those defaults. For a non-debug deployment, set `DJANGO_DEBUG=false`, a strong unique `DJANGO_SECRET_KEY`, `BOX_API_TOKEN`, and `DJANGO_ALLOWED_HOSTS` to the real hostnames. The app refuses to start with `DEBUG=False` if the secret or API token is missing. Keep these values in the hosting environment's secret store, not in source control. The recommendation endpoint requires `Authorization: Bearer <BOX_API_TOKEN>` whenever a token is configured; local development can leave it unset. Serve production traffic over HTTPS.

## Verification

`python manage.py test` runs 28 tests covering model validation and database constraints, selection rules, packing edge cases, token access, the API endpoint, and the management command. The CI workflow runs `check`, migration consistency, and tests on each push and pull request. Recorded local output is in [TEST_OUTPUT.md](TEST_OUTPUT.md).

## Submission items

- Add the GitHub repository URL after publishing the project.
- `AI_USAGE.md` documents the AI tools and their contributions; review it for accuracy.
- Export the actual chat transcripts yourself, unedited, and add them under `transcripts/`. Do not use AI to create or edit them.
- Write your personal learning reflection yourself in `LEARNINGS.md`; the assignment requires your own answer.
