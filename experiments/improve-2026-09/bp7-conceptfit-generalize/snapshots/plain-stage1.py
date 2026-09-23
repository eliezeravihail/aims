"""Apply promotional rules to a shopping cart. All money is integer cents."""


class Cart:
    """A shopping cart holding priced line items."""

    def __init__(self):
        self._lines = []

    def add_item(self, sku, category, unit_price, qty):
        """Add a line: `qty` units of `sku` (in `category`) at `unit_price` each."""
        self._lines.append(
            {
                "sku": sku,
                "category": category,
                "unit_price": unit_price,
                "qty": qty,
            }
        )

    @property
    def lines(self):
        """The cart's line items (read-only view)."""
        return tuple(self._lines)

    def subtotal(self):
        """Sum of unit_price * qty over all lines."""
        return sum(line["unit_price"] * line["qty"] for line in self._lines)


class PercentOff:
    """Take `percent`% off the summed price of lines in a given category."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def discount(self, cart):
        base = sum(
            line["unit_price"] * line["qty"]
            for line in cart.lines
            if line["category"] == self.category
        )
        return base * self.percent // 100


class AmountOffOver:
    """Take a flat `amount` off once the cart subtotal reaches `threshold`."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def discount(self, cart):
        return self.amount if cart.subtotal() >= self.threshold else 0


class BuyXGetY:
    """For a given sku, every group of `x + y` units makes `y` units free."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def discount(self, cart):
        group = self.x + self.y
        return sum(
            (line["qty"] // group) * self.y * line["unit_price"]
            for line in cart.lines
            if line["sku"] == self.sku
        )


class Engine:
    """Apply a list of rules to a cart and compute the discounted total."""

    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        """Return max(0, subtotal - sum of every rule's discount)."""
        total_discount = sum(rule.discount(cart) for rule in self.rules)
        return max(0, cart.subtotal() - total_discount)
