"""Shopping cart promotional rules engine."""


class Cart:
    """Shopping cart for items."""

    def __init__(self):
        self.items = []

    def add_item(self, sku, category, unit_price, qty):
        """Add an item to the cart."""
        self.items.append({
            'sku': sku,
            'category': category,
            'unit_price': unit_price,
            'qty': qty
        })

    def subtotal(self):
        """Calculate cart subtotal in cents."""
        total = 0
        for item in self.items:
            total += item['unit_price'] * item['qty']
        return total


class PercentOff:
    """Discount by percentage off a category."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def discount(self, cart):
        """Calculate discount amount."""
        category_total = 0
        for item in cart.items:
            if item['category'] == self.category:
                category_total += item['unit_price'] * item['qty']
        return (category_total * self.percent) // 100


class AmountOffOver:
    """Discount a fixed amount if subtotal meets threshold."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def discount(self, cart):
        """Calculate discount amount."""
        if cart.subtotal() >= self.threshold:
            return self.amount
        return 0


class BuyXGetY:
    """Discount by giving away units."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def discount(self, cart):
        """Calculate discount amount."""
        total_discount = 0
        for item in cart.items:
            if item['sku'] == self.sku:
                groups = item['qty'] // (self.x + self.y)
                total_discount += groups * self.y * item['unit_price']
        return total_discount


class Engine:
    """Apply promotional rules to a cart."""

    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        """Calculate final total after all discounts."""
        subtotal = cart.subtotal()
        total_discount = 0
        for rule in self.rules:
            total_discount += rule.discount(cart)
        return max(0, subtotal - total_discount)
