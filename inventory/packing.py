"""Box recommendation for an order.

Selection rules
---------------
1. Only active boxes are considered.
2. Total order weight must not exceed the box's maximum weight.
3. Total item volume must not exceed the box's internal volume (cheap pre-check).
4. The units must actually be placed inside the box without overlapping,
   each unit axis-aligned in any of its 6 orientations (``_pack``).
5. Among the boxes that pass, the cheapest wins; smaller volume and then
   database id break ties so the result is deterministic.

``_pack`` is an extreme-point first-fit-decreasing heuristic. It is *sound*:
if it says a set of items fits, the placement it found is physically valid.
It is not *complete*: a rare feasible arrangement may be missed, in which case
a slightly larger box is recommended. That is the safe failure direction for a
warehouse (an oversized box rather than one that cannot close).
"""
from dataclasses import dataclass
from decimal import Decimal
from itertools import permutations

from .models import Order, ShippingBox

# Extreme-point packing is roughly cubic in the number of units, so cap it.
MAX_UNITS = 100


class OrderTooLarge(ValueError):
    """Raised when an order has more units than the packer is meant to handle."""


@dataclass(frozen=True)
class Recommendation:
    box: ShippingBox
    total_weight_kg: Decimal
    total_volume_cm3: Decimal


def _volume(dims):
    return dims[0] * dims[1] * dims[2]


def _overlaps(a, b):
    """Each argument is (x, y, z, l, w, h). Touching faces do not count."""
    return (
        a[0] < b[0] + b[3] and b[0] < a[0] + a[3]
        and a[1] < b[1] + b[4] and b[1] < a[1] + a[4]
        and a[2] < b[2] + b[5] and b[2] < a[2] + a[5]
    )


def _dimensions_fit(unit, box_dims):
    """Cheap rotation-aware necessary check before attempting a full layout."""
    return all(item <= inside for item, inside in zip(sorted(unit), sorted(box_dims)))


def _pack(units, box_dims):
    """Try to place every unit (a tuple of 3 dimensions) inside ``box_dims``.

    Returns the list of placements (x, y, z, l, w, h), or None if not placed.
    """
    bl, bw, bh = box_dims
    if any(not _dimensions_fit(unit, box_dims) for unit in units):
        return None

    ordered = sorted(units, key=lambda d: (_volume(d), sorted(d)), reverse=True)
    placed = []
    # A set prevents repeated placements from accumulating the same candidate
    # corner; sorted iteration below keeps the result deterministic.
    points = {(Decimal(0), Decimal(0), Decimal(0))}

    for unit in ordered:
        orientations = sorted(set(permutations(unit)))
        spot = None
        # Lowest, then back-most, then left-most extreme point first.
        for point in sorted(points, key=lambda p: (p[2], p[1], p[0])):
            for l, w, h in orientations:
                x, y, z = point
                if x + l > bl or y + w > bw or z + h > bh:
                    continue
                candidate = (x, y, z, l, w, h)
                if any(_overlaps(candidate, other) for other in placed):
                    continue
                spot = candidate
                break
            if spot:
                break
        if spot is None:
            return None
        placed.append(spot)
        x, y, z, l, w, h = spot
        points.discard((x, y, z))
        points.update({(x + l, y, z), (x, y + w, z), (x, y, z + h)})
    return placed


def can_pack(units, box):
    """True when every unit can be placed inside ``box`` without overlap."""
    return _pack(units, (box.length_cm, box.width_cm, box.height_cm)) is not None


def recommend_box(order: Order) -> Recommendation | None:
    """Return the cheapest box that fits the whole order, or None.

    None means the order is empty or no active box can hold it. Raises
    ``OrderTooLarge`` if the order has more than ``MAX_UNITS`` units.
    """
    items = list(order.items.select_related("product"))
    if not items:
        return None
    if sum(item.quantity for item in items) > MAX_UNITS:
        raise OrderTooLarge(f"Orders above {MAX_UNITS} units are not supported.")

    total_weight = sum((i.product.weight_kg * i.quantity for i in items), Decimal("0"))
    units = []
    for item in items:
        dims = (item.product.length_cm, item.product.width_cm, item.product.height_cm)
        units.extend([dims] * item.quantity)
    total_volume = sum((_volume(u) for u in units), Decimal("0"))

    # Try candidates in recommendation order and stop at the first valid box.
    # This avoids running the cubic placement heuristic for boxes that cannot
    # beat a box already found.
    candidates = sorted(
        ShippingBox.objects.filter(active=True),
        key=lambda box: (box.cost, box_volume_key(box), box.pk),
    )
    for box in candidates:
        if total_weight > box.max_weight_kg or total_volume > box_volume_key(box):
            continue
        if can_pack(units, box):
            return Recommendation(box, total_weight, total_volume)
    return None


def box_volume_key(box):
    return box.length_cm * box.width_cm * box.height_cm
