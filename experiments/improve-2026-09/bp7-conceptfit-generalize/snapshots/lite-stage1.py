"""Apply promotional rules to a shopping cart. All money is in integer cents."""

from collections import namedtuple

Line = namedtuple("Line", ("sku", "category", "unit_price", "qty"))


class Cart:
    def __init__(self):
        self.lines = []

    def add_item(self, sku, category, unit_price, qty):
        self.lines.append(Line(sku, category, unit_price, qty))

    def subtotal(self):
        return sum(line.unit_price * line.qty for line in self.lines)


class PercentOff:
    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def discount(self, cart):
        base = sum(
            line.unit_price * line.qty
            for line in cart.lines
            if line.category == self.category
        )
        return base * self.percent // 100


class AmountOffOver:
    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def discount(self, cart):
        return self.amount if cart.subtotal() >= self.threshold else 0


class BuyXGetY:
    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def discount(self, cart):
        group = self.x + self.y
        return sum(
            (line.qty // group) * self.y * line.unit_price
            for line in cart.lines
            if line.sku == self.sku
        )


class Engine:
    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        total_discount = sum(rule.discount(cart) for rule in self.rules)
        return max(0, cart.subtotal() - total_discount)
