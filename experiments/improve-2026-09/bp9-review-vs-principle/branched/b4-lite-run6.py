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


class AmountOffOver:
    def __init__(self, threshold, amount):
        self.threshold = threshold
        self.amount = amount


class BuyXGetY:
    def __init__(self, sku, x, y):
        self.sku = sku
        self.x = x
        self.y = y


class Engine:
    def __init__(self, rules):
        self.rules = rules

    def total(self, cart):
        subtotal = cart.subtotal()
        total_discount = 0

        for rule in self.rules:
            if isinstance(rule, PercentOff):
                base = sum(
                    item['unit_price'] * item['qty']
                    for item in cart.items
                    if item['category'] == rule.category
                )
                total_discount += base * rule.percent // 100

            elif isinstance(rule, AmountOffOver):
                if subtotal >= rule.threshold:
                    total_discount += rule.amount

            elif isinstance(rule, BuyXGetY):
                for item in cart.items:
                    if item['sku'] == rule.sku:
                        groups = item['qty'] // (rule.x + rule.y)
                        total_discount += groups * rule.y * item['unit_price']

        return max(0, subtotal - total_discount)
