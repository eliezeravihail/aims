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


class PercentOff:
    """Discount as a percentage of the total price of items in a category."""

    def __init__(self, category, percent, priority=0, exclusive=False):
        self.category = category
        self.percent = percent
        self.priority = priority
        self.exclusive = exclusive


class AmountOffOver:
    """Fixed discount amount if subtotal exceeds threshold."""

    def __init__(self, threshold, amount, priority=0, exclusive=False):
        self.threshold = threshold
        self.amount = amount
        self.priority = priority
        self.exclusive = exclusive


class BuyXGetY:
    """Free items promotion: every x+y units purchased, y are free."""

    def __init__(self, sku, x, y, priority=0, exclusive=False):
        self.sku = sku
        self.x = x
        self.y = y
        self.priority = priority
        self.exclusive = exclusive


class PercentOffOrder:
    """Discount as a percentage of the whole cart subtotal."""

    def __init__(self, percent, priority=0, exclusive=False):
        self.percent = percent
        self.priority = priority
        self.exclusive = exclusive


class Engine:
    """Applies all promotional rules to a cart and computes the final total."""

    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        """Return final total: max(0, subtotal - sum of all discounts)."""
        subtotal = cart.subtotal()
        total_discount = 0

        for rule in sorted(self.rules, key=lambda r: r.priority):
            before = total_discount
            if isinstance(rule, PercentOff):
                category_price = sum(
                    item['unit_price'] * item['qty']
                    for item in cart.items
                    if item['category'] == rule.category
                )
                total_discount += category_price * rule.percent // 100

            elif isinstance(rule, AmountOffOver):
                if subtotal >= rule.threshold:
                    total_discount += rule.amount

            elif isinstance(rule, PercentOffOrder):
                total_discount += subtotal * rule.percent // 100

            elif isinstance(rule, BuyXGetY):
                for item in cart.items:
                    if item['sku'] == rule.sku:
                        free_groups = item['qty'] // (rule.x + rule.y)
                        total_discount += free_groups * rule.y * item['unit_price']

            if rule.exclusive and total_discount != before:
                break

        return max(0, subtotal - total_discount)
