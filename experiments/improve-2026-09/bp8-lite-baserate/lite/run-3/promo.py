class Cart:
    """Shopping cart that accumulates items and computes subtotal."""

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
        """Return sum of (unit_price * qty) for all items."""
        total = 0
        for item in self.items:
            total += item['unit_price'] * item['qty']
        return total


class PercentOff:
    """Discount as a percentage of the total price of items in a category."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def apply(self, cart):
        """Return percent% off summed price of lines matching category (integer floor)."""
        total_price = 0
        for item in cart.items:
            if item['category'] == self.category:
                total_price += item['unit_price'] * item['qty']
        return (total_price * self.percent) // 100


class AmountOffOver:
    """Fixed discount amount if subtotal exceeds threshold."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def apply(self, cart):
        """Return amount if cart subtotal >= threshold, else 0."""
        if cart.subtotal() >= self.threshold:
            return self.amount
        return 0


class BuyXGetY:
    """Free items promotion: every x+y units purchased, y are free."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def apply(self, cart):
        """Return discount for free items: (qty//(x+y))*y*unit_price per matching line."""
        discount = 0
        for item in cart.items:
            if item['sku'] == self.sku:
                full_sets = item['qty'] // (self.x + self.y)
                discount += full_sets * self.y * item['unit_price']
        return discount


class Engine:
    """Applies all promotional rules to a cart and computes the final total."""

    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        """Return final total: max(0, subtotal - sum of all discounts)."""
        subtotal = cart.subtotal()
        discount_total = 0
        for rule in self.rules:
            discount_total += rule.apply(cart)
        final = subtotal - discount_total
        return max(0, final)
