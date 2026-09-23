class Cart:
    def __init__(self):
        self._items = []

    def add_item(self, sku, category, unit_price, qty):
        self._items.append((sku, category, unit_price, qty))

    def subtotal(self):
        return sum(unit_price * qty for _, _, unit_price, qty in self._items)

    def items(self):
        return self._items


class PercentOff:
    def __init__(self, category, percent):
        self._category = category
        self._percent = percent

    def apply(self, cart):
        base = sum(
            unit_price * qty
            for sku, cat, unit_price, qty in cart.items()
            if cat == self._category
        )
        return base * self._percent // 100


class AmountOffOver:
    def __init__(self, threshold, amount):
        self._threshold = threshold
        self._amount = amount

    def apply(self, cart):
        return self._amount if cart.subtotal() >= self._threshold else 0


class BuyXGetY:
    def __init__(self, sku, x, y):
        self._sku = sku
        self._x = x
        self._y = y

    def apply(self, cart):
        reduction = 0
        for s, _, unit_price, qty in cart.items():
            if s == self._sku:
                num_groups = qty // (self._x + self._y)
                reduction += num_groups * self._y * unit_price
        return reduction


class Engine:
    def __init__(self, rules):
        self._rules = rules

    def total(self, cart):
        base = cart.subtotal()
        total_reduction = sum(rule.apply(cart) for rule in self._rules)
        return max(0, base - total_reduction)
