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
        return sum(item['unit_price'] * item['qty'] for item in self.items)


class Rule:
    """Base class for promotional rules. Subclasses implement discount()."""

    def discount(self, cart):
        """Return the discount amount in cents for this rule applied to the cart."""
        raise NotImplementedError


class PercentOff(Rule):
    """Discount as a percentage of the total price of items in a category."""

    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def discount(self, cart):
        """Return percent% off summed price of lines matching category (integer floor)."""
        category_price = sum(
            item['unit_price'] * item['qty']
            for item in cart.items
            if item['category'] == self.category
        )
        return category_price * self.percent // 100


class AmountOffOver(Rule):
    """Fixed discount amount if subtotal exceeds threshold."""

    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def discount(self, cart):
        """Return amount if cart subtotal >= threshold, else 0."""
        return self.amount if cart.subtotal() >= self.threshold else 0


class BuyXGetY(Rule):
    """Free items promotion: every x+y units purchased, y are free."""

    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def discount(self, cart):
        """Return discount for free items: (qty//(x+y))*y*unit_price per matching line."""
        total_discount = 0
        for item in cart.items:
            if item['sku'] == self.sku:
                free_groups = item['qty'] // (self.x + self.y)
                total_discount += free_groups * self.y * item['unit_price']
        return total_discount


class Engine:
    """Applies all promotional rules to a cart and computes the final total."""

    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        """Return final total: max(0, subtotal - sum of all discounts)."""
        subtotal = cart.subtotal()
        total_discount = sum(rule.discount(cart) for rule in self.rules)
        return max(0, subtotal - total_discount)
