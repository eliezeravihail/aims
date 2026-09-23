"""Promotional discount engine for shopping carts."""


class Cart:
    """A shopping cart with line items."""

    def __init__(self):
        self.lines = []

    def add_item(self, sku, category, unit_price, qty):
        """Add a line item to the cart."""
        self.lines.append({
            'sku': sku,
            'category': category,
            'unit_price': unit_price,
            'qty': qty,
        })

    def subtotal(self):
        """Get cart subtotal in cents."""
        return sum(line['unit_price'] * line['qty'] for line in self.lines)


class PercentOff:
    """Percentage-based discount on category."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def apply(self, cart):
        """Calculate discount for this rule."""
        target_sum = sum(
            line['unit_price'] * line['qty']
            for line in cart.lines
            if line['category'] == self.category
        )
        return (target_sum * self.percent) // 100


class AmountOffOver:
    """Fixed amount off when threshold is met."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def apply(self, cart):
        """Calculate discount for this rule."""
        return self.amount if cart.subtotal() >= self.threshold else 0


class BuyXGetY:
    """Free items after purchase threshold."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def apply(self, cart):
        """Calculate discount for this rule."""
        savings = 0
        for line in cart.lines:
            if line['sku'] == self.sku:
                num_free = (line['qty'] // (self.x + self.y)) * self.y
                savings += num_free * line['unit_price']
        return savings


class Engine:
    """Apply all discount rules to a cart."""

    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        """Return cart total after all discounts."""
        base = cart.subtotal()
        discounts = sum(rule.apply(cart) for rule in self.rules)
        return max(0, base - discounts)
