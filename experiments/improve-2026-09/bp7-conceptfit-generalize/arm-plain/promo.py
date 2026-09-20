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


class Rule:
    """Base for promo rules: carries the stacking policy shared by every rule.

    `priority` orders rules (ascending, lower first); an `exclusive` rule that
    yields a nonzero discount stops any lower-priority rule from applying.
    """

    def __init__(self, priority=0, exclusive=False):
        self.priority = priority
        self.exclusive = exclusive


class PercentOff(Rule):
    """Take `percent`% off the summed price of lines in a given category."""

    def __init__(self, category, percent, priority=0, exclusive=False):
        super().__init__(priority, exclusive)
        self.category = category
        self.percent = percent

    def discount(self, cart):
        base = sum(
            line["unit_price"] * line["qty"]
            for line in cart.lines
            if line["category"] == self.category
        )
        return base * self.percent // 100


class AmountOffOver(Rule):
    """Take a flat `amount` off once the cart subtotal reaches `threshold`."""

    def __init__(self, threshold, amount, priority=0, exclusive=False):
        super().__init__(priority, exclusive)
        self.threshold = threshold
        self.amount = amount

    def discount(self, cart):
        return self.amount if cart.subtotal() >= self.threshold else 0


class BuyXGetY(Rule):
    """For a given sku, every group of `x + y` units makes `y` units free."""

    def __init__(self, sku, x, y, priority=0, exclusive=False):
        super().__init__(priority, exclusive)
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
        """Return max(0, subtotal - accumulated discount).

        Rules apply in ascending priority order (stable for ties). A nonzero
        discount from an exclusive rule is applied, then processing stops.
        """
        subtotal = cart.subtotal()
        total_discount = 0
        for rule in sorted(self.rules, key=lambda r: r.priority):
            discount = rule.discount(cart)
            total_discount += discount
            if getattr(rule, "exclusive", False) and discount:
                break
        return max(0, subtotal - total_discount)
