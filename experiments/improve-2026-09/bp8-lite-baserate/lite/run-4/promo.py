class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, sku, category, unit_price, qty):
        self.items.append({
            'sku': sku,
            'category': category,
            'unit_price': unit_price,
            'qty': qty
        })

    def subtotal(self):
        return sum(item['unit_price'] * item['qty'] for item in self.items)


class PercentOff:
    def __init__(self, category, percent):
        self.category = category
        self.percent = percent

    def discount(self, cart):
        matching_total = sum(
            item['unit_price'] * item['qty']
            for item in cart.items
            if item['category'] == self.category
        )
        return matching_total * self.percent // 100


class AmountOffOver:
    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount

    def discount(self, cart):
        if cart.subtotal() >= self.threshold:
            return self.amount
        return 0


class BuyXGetY:
    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y

    def discount(self, cart):
        total_discount = 0
        for item in cart.items:
            if item['sku'] == self.sku:
                groups = item['qty'] // (self.x + self.y)
                total_discount += groups * self.y * item['unit_price']
        return total_discount


class Engine:
    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        subtotal = cart.subtotal()
        total_discount = sum(rule.discount(cart) for rule in self.rules)
        return max(0, subtotal - total_discount)
