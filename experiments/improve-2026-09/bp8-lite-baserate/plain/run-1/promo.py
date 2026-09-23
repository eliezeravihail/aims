"""Shopping cart promotional rules engine."""


class Cart:
    """Shopping cart for managing items."""

    def __init__(self):
        self.items = []

    def add_item(self, sku, category, unit_price, qty):
        """Add an item to the cart.

        Args:
            sku: Product SKU
            category: Product category
            unit_price: Price in cents
            qty: Quantity
        """
        self.items.append({
            'sku': sku,
            'category': category,
            'unit_price': unit_price,
            'qty': qty
        })

    def subtotal(self):
        """Return the subtotal in cents."""
        return sum(item['unit_price'] * item['qty'] for item in self.items)


class PercentOff:
    """Apply a percentage discount to items in a specific category."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def discount(self, cart):
        """Calculate discount for this rule."""
        category_total = sum(
            item['unit_price'] * item['qty']
            for item in cart.items
            if item['category'] == self.category
        )
        return category_total * self.percent // 100


class AmountOffOver:
    """Apply a fixed discount if subtotal exceeds threshold."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def discount(self, cart):
        """Calculate discount for this rule."""
        return self.amount if cart.subtotal() >= self.threshold else 0


class BuyXGetY:
    """Apply a buy X get Y free discount."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def discount(self, cart):
        """Calculate discount for this rule."""
        discount = 0
        for item in cart.items:
            if item['sku'] == self.sku:
                free_units = (item['qty'] // (self.x + self.y)) * self.y
                discount += free_units * item['unit_price']
        return discount


class Engine:
    """Apply promotional rules to a cart."""

    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        """Calculate the total after applying all rules.

        Args:
            cart: Cart instance

        Returns:
            Total in cents (subtotal minus all discounts, minimum 0)
        """
        subtotal = cart.subtotal()
        total_discount = sum(rule.discount(cart) for rule in self.rules)
        return max(0, subtotal - total_discount)
