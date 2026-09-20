"""Reference implementation for BP7 — used ONLY to validate the hidden tests.
Not shown to any arm. Concept-fit design (first-class Rule objects).

Engine.total uses the unified stage-2 algorithm, which reduces to the stage-1
"apply all rules" semantics when every rule has the default priority/exclusive."""

from dataclasses import dataclass
from typing import List


@dataclass
class Line:
    sku: str
    category: str
    unit_price: int  # cents
    qty: int


class Cart:
    def __init__(self) -> None:
        self._lines: List[Line] = []

    def add_item(self, sku: str, category: str, unit_price: int, qty: int) -> None:
        self._lines.append(Line(sku, category, unit_price, qty))

    @property
    def lines(self) -> List[Line]:
        return list(self._lines)

    def subtotal(self) -> int:
        return sum(l.unit_price * l.qty for l in self._lines)


@dataclass
class PercentOff:
    category: str
    percent: int
    priority: int = 0
    exclusive: bool = False

    def discount(self, cart: Cart) -> int:
        base = sum(l.unit_price * l.qty for l in cart.lines if l.category == self.category)
        return (base * self.percent) // 100


@dataclass
class AmountOffOver:
    threshold: int
    amount: int
    priority: int = 0
    exclusive: bool = False

    def discount(self, cart: Cart) -> int:
        return self.amount if cart.subtotal() >= self.threshold else 0


@dataclass
class BuyXGetY:
    sku: str
    x: int
    y: int
    priority: int = 0
    exclusive: bool = False

    def discount(self, cart: Cart) -> int:
        total = 0
        for l in cart.lines:
            if l.sku == self.sku:
                group = self.x + self.y
                free_units = (l.qty // group) * self.y
                total += free_units * l.unit_price
        return total


class Engine:
    def __init__(self, rules: list) -> None:
        self._rules = list(rules)

    def total(self, cart: Cart) -> int:
        disc = 0
        for r in sorted(self._rules, key=lambda r: r.priority):
            d = r.discount(cart)
            disc += d
            if getattr(r, "exclusive", False) and d > 0:
                break
        return max(0, cart.subtotal() - disc)
