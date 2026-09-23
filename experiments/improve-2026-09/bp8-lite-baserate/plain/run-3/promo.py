"""Promotional discount engine for shopping carts."""


class Cart:
    """Shopping cart implementation."""

    def __init__(self):
        self.lines = []

    def add_item(self, sku, category, unit_price, qty):
        """Add an item to the cart.

        Parameters:
            sku: Stock keeping unit identifier
            category: Item category
            unit_price: Price per unit in cents
            qty: Quantity
        """
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
    """Category-based percentage discount."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def apply(self, cart):
        """Calculate discount amount in cents."""
        matching_sum = sum(
            line['unit_price'] * line['qty']
            for line in cart.lines
            if line['category'] == self.category
        )
        return matching_sum * self.percent // 100


class AmountOffOver:
    """Fixed discount for orders over threshold."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def apply(self, cart):
        """Calculate discount amount in cents."""
        if cart.subtotal() >= self.threshold:
            return self.amount
        return 0


class BuyXGetY:
    """Buy X units get Y free discount."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def apply(self, cart):
        """Calculate discount amount in cents."""
        total_discount = 0
        for line in cart.lines:
            if line['sku'] == self.sku:
                groups = line['qty'] // (self.x + self.y)
                free_qty = groups * self.y
                total_discount += free_qty * line['unit_price']
        return total_discount


class Engine:
    """Applies promotional rules to calculate final cart total."""

    def __init__(self, rules):
        """Initialize with list of promotional rules."""
        self.rules = rules

    def total(self, cart):
        """Calculate total price after applying all promotions.

        Args:
            cart: Cart instance

        Returns:
            Total price in cents after all discounts, minimum 0
        """
        subtotal = cart.subtotal()
        total_discount = sum(rule.apply(cart) for rule in self.rules)
        return max(0, subtotal - total_discount)
