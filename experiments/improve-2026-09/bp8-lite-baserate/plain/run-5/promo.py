"""Shopping cart with promotional discount rules."""


class Cart:
    """Shopping cart containing line items."""

    def __init__(self):
        self._items = []

    def add_item(self, sku, category, unit_price, qty):
        """Add item to cart."""
        self._items.append({
            'sku': sku,
            'category': category,
            'unit_price': unit_price,
            'qty': qty,
        })

    def subtotal(self):
        """Return subtotal in cents."""
        return sum(item['unit_price'] * item['qty'] for item in self._items)


class PercentOff:
    """Apply percentage discount to items in a category."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent


class AmountOffOver:
    """Apply fixed discount if cart subtotal exceeds threshold."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount


class BuyXGetY:
    """Discount by offering free units after purchasing threshold."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y


class Engine:
    """Compute total after applying all rules."""

    def __init__(self, rules):
        self._rules = rules

    def total(self, cart):
        """Apply all rules and return final total."""
        subtotal = cart.subtotal()
        discount = 0

        for rule in self._rules:
            if isinstance(rule, PercentOff):
                category_sum = sum(
                    item['unit_price'] * item['qty']
                    for item in cart._items
                    if item['category'] == rule.category
                )
                discount += (category_sum * rule.percent) // 100
            elif isinstance(rule, AmountOffOver):
                if subtotal >= rule.threshold:
                    discount += rule.amount
            elif isinstance(rule, BuyXGetY):
                for item in cart._items:
                    if item['sku'] == rule.sku:
                        free_units = (item['qty'] // (rule.x + rule.y)) * rule.y
                        discount += free_units * item['unit_price']

        return max(0, subtotal - discount)
