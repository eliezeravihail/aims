"""Promotional rules over a shopping cart.

All money is integer cents; every computation stays in integer arithmetic so no
rounding drift can enter. The three rule kinds share one seam: each is a `Rule`
that answers `discount(cart) -> int`, and the `Engine` combines those discounts
without knowing which kind it holds. A new rule kind is therefore added by
writing a new `Rule` subclass, never by editing the engine (Open/Closed over the
rule-kind change axis the spec anticipates).

Every rule also carries a *stacking policy* — `priority` (rules apply in ascending
priority order) and `exclusive` (an exclusive rule producing a nonzero discount
stops every lower-priority rule). This policy is orthogonal to a rule's discount
math: the metadata lives on the `Rule` abstraction, and how rules combine under it
is owned solely by `Engine.total`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Sequence

__all__ = [
    "Cart",
    "CartLine",
    "Rule",
    "PercentOff",
    "AmountOffOver",
    "BuyXGetY",
    "Engine",
]


@dataclass(frozen=True)
class CartLine:
    """One immutable line in a cart. `total` is `unit_price * qty` (cents)."""

    sku: str
    category: str
    unit_price: int
    qty: int

    @property
    def total(self) -> int:
        return self.unit_price * self.qty


class Cart:
    """A shopping cart: a sequence of lines and their summed price.

    Lines are appended via `add_item`; rules read them through `lines` (a
    read-only snapshot of `CartLine` value objects) and through `subtotal`.
    """

    def __init__(self) -> None:
        self._lines: list[CartLine] = []

    def add_item(self, sku: str, category: str, unit_price: int, qty: int) -> None:
        """Append a line. Command (mutates), returns nothing."""
        self._lines.append(CartLine(sku, category, unit_price, qty))

    @property
    def lines(self) -> tuple[CartLine, ...]:
        """A read-only snapshot of the cart's lines."""
        return tuple(self._lines)

    def __iter__(self) -> Iterator[CartLine]:
        return iter(self._lines)

    def subtotal(self) -> int:
        """Sum of `unit_price * qty` over all lines (0 for an empty cart)."""
        return sum(line.total for line in self._lines)


@dataclass(frozen=True)
class Rule(ABC):
    """A promotional rule: given a cart, name a discount, plus a stacking policy.

    `discount` returns a non-negative amount in cents. It reads the cart but
    never mutates it (pure query), so the engine may *evaluate* every rule
    against the same cart independently.

    Two stacking attributes are part of the rule abstraction (keyword-only, so a
    concrete kind's own positional fields are unaffected):

    - `priority` — rules combine in ascending priority order (lower number first;
      the ordering is stable for equal priorities).
    - `exclusive` — when this rule produces a *nonzero* discount, it is applied and
      then no lower-priority rule (any rule later in the sorted order) is applied.

    Both default to the additive, order-free behavior. How the policy is honored is
    owned by `Engine.total`, not by any concrete rule.
    """

    priority: int = field(default=0, kw_only=True)
    exclusive: bool = field(default=False, kw_only=True)

    @abstractmethod
    def discount(self, cart: Cart) -> int:
        raise NotImplementedError


@dataclass(frozen=True)
class PercentOff(Rule):
    """`percent`% off the summed price of lines in `category`, integer floor.

    Discount = base * percent // 100, where base is the summed `total` of the
    matching lines. An unmatched category has base 0, hence discount 0.
    """

    category: str
    percent: int

    def discount(self, cart: Cart) -> int:
        base = sum(line.total for line in cart if line.category == self.category)
        return base * self.percent // 100


@dataclass(frozen=True)
class AmountOffOver(Rule):
    """Flat `amount` off once the whole cart reaches `threshold`.

    Discount = amount if `cart.subtotal() >= threshold` (inclusive), else 0.
    """

    threshold: int
    amount: int

    def discount(self, cart: Cart) -> int:
        return self.amount if cart.subtotal() >= self.threshold else 0


@dataclass(frozen=True)
class BuyXGetY(Rule):
    """Buy `x`, get `y` free, per line matching `sku`.

    Within a matching line, every complete group of `x + y` units makes `y`
    units free: discount = (qty // (x + y)) * y * unit_price, summed over all
    matching lines. An unmatched sku contributes 0.
    """

    sku: str
    x: int
    y: int

    def discount(self, cart: Cart) -> int:
        group = self.x + self.y
        return sum(
            (line.qty // group) * self.y * line.unit_price
            for line in cart
            if line.sku == self.sku
        )


@dataclass(frozen=True)
class Engine:
    """Applies a fixed set of rules to a cart under their stacking policy.

    `total` combines the discount every rule names for the cart in ascending
    `priority` order, accumulating against the subtotal, and subtracts the
    combined discount, floored at 0 so an over-generous stack of rules can never
    make a cart worth negative money. An `exclusive` rule whose discount is
    nonzero is applied and then stops every remaining (lower-priority) rule; an
    exclusive rule with a zero discount does not stop the walk. With every rule at
    the default priority/exclusive, this reduces to the additive sum.
    """

    rules: Sequence[Rule] = field(default_factory=tuple)

    def total(self, cart: Cart) -> int:
        discount = 0
        for rule in sorted(self.rules, key=lambda rule: rule.priority):
            amount = rule.discount(cart)
            discount += amount
            if rule.exclusive and amount != 0:
                break
        return max(0, cart.subtotal() - discount)
