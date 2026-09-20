"""Shopping cart with promotional discounts.

Repaired per the BP9 aims review of b1-plain-run2.py: the anemic-rules +
Engine type-switch (S3, §4/§8/§9/§7) is replaced by polymorphic rule.discount(cart);
the representation leak (S2, get_items publishing the internal mutable list) is
closed by exposing an immutable snapshot. Behavior is byte-identical to the spec."""


class Cart:
    """Represents a shopping cart."""

    def __init__(self):
        self._items = []

    def add_item(self, sku, category, unit_price, qty):
        self._items.append({
            'sku': sku,
            'category': category,
            'unit_price': unit_price,
            'qty': qty,
        })

    def subtotal(self):
        return sum(i['unit_price'] * i['qty'] for i in self._items)

    @property
    def items(self):
        """Read-only snapshot of the lines (no internal reference leaked)."""
        return tuple(dict(i) for i in self._items)


class PercentOff:
    """Percentage discount for a category."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def discount(self, cart):
        base = sum(i['unit_price'] * i['qty'] for i in cart.items
                   if i['category'] == self.category)
        return base * self.percent // 100


class AmountOffOver:
    """Fixed amount discount for orders over a threshold."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def discount(self, cart):
        return self.amount if cart.subtotal() >= self.threshold else 0


class BuyXGetY:
    """Buy X get Y free promotion."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def discount(self, cart):
        total = 0
        for i in cart.items:
            if i['sku'] == self.sku:
                free_units = (i['qty'] // (self.x + self.y)) * self.y
                total += free_units * i['unit_price']
        return total


class Engine:
    """Promotional discount engine (polymorphic; no type-switch, no reopen on new rule kind)."""

    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        discount = sum(rule.discount(cart) for rule in self.rules)
        return max(0, cart.subtotal() - discount)
