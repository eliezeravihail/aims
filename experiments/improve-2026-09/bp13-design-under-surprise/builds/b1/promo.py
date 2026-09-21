"""Shopping cart with promotional discounts."""


class Cart:
    """Represents a shopping cart."""

    def __init__(self):
        self._items = []

    def add_item(self, sku, category, unit_price, qty):
        """Add item to cart.

        Args:
            sku: Product identifier
            category: Product category
            unit_price: Unit price in cents
            qty: Quantity to add
        """
        self._items.append({
            'sku': sku,
            'category': category,
            'unit_price': unit_price,
            'qty': qty,
        })

    def subtotal(self):
        """Return cart subtotal in cents."""
        total = 0
        for item in self._items:
            total += item['unit_price'] * item['qty']
        return total

    def get_items(self):
        """Return list of cart items."""
        return self._items


class PercentOff:
    """Percentage discount for a category."""

    def __init__(self, category, percent, priority=0, exclusive=False):
        self.category = category
        self.percent = percent
        self.priority = priority
        self.exclusive = exclusive


class AmountOffOver:
    """Fixed amount discount for orders over threshold."""

    def __init__(self, threshold, amount, priority=0, exclusive=False):
        self.threshold = threshold
        self.amount = amount
        self.priority = priority
        self.exclusive = exclusive


class BuyXGetY:
    """Buy X get Y free promotion."""

    def __init__(self, sku, x, y, priority=0, exclusive=False):
        self.sku = sku
        self.x = x
        self.y = y
        self.priority = priority
        self.exclusive = exclusive


class Engine:
    """Promotional discount engine."""

    def __init__(self, rules):
        """Initialize engine with rules.

        Args:
            rules: List of promotional rules
        """
        self.rules = rules

    def total(self, cart):
        """Calculate total price after discounts.

        Args:
            cart: Cart instance

        Returns:
            Total price in cents after all discounts applied
        """
        subtotal = cart.subtotal()
        total_discount = 0

        for rule in sorted(self.rules, key=lambda r: r.priority):
            before = total_discount

            if isinstance(rule, PercentOff):
                # Sum prices for items in matching category
                category_sum = 0
                for item in cart.get_items():
                    if item['category'] == rule.category:
                        category_sum += item['unit_price'] * item['qty']
                discount = category_sum * rule.percent // 100
                total_discount += discount

            elif isinstance(rule, AmountOffOver):
                # Apply fixed discount if threshold met
                if subtotal >= rule.threshold:
                    total_discount += rule.amount

            elif isinstance(rule, BuyXGetY):
                # Calculate free units for matching SKU
                discount = 0
                for item in cart.get_items():
                    if item['sku'] == rule.sku:
                        num_groups = item['qty'] // (rule.x + rule.y)
                        free_units = num_groups * rule.y
                        discount += free_units * item['unit_price']
                total_discount += discount

            if rule.exclusive and total_discount != before:
                break

        return max(0, subtotal - total_discount)
