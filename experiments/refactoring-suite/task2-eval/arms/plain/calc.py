"""A tiny arithmetic expression evaluator.

Grammar (recursive descent), standard precedence:
    expr   := term (('+' | '-') term)*
    term   := power (('*' | '/') power)*
    power  := factor ('^' power)?
    factor := NUMBER | '(' expr ')'

Numbers are non-negative integers. '/' is integer floor division. No unary operators.
'^' is exponentiation: binds tighter than '*'/'/' and is right-associative.
"""


def tokenize(s: str):
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            tokens.append(("num", int(s[i:j])))
            i = j
            continue
        if c in "+-*/^()":
            tokens.append((c, c))
            i += 1
            continue
        raise ValueError(f"bad character {c!r} at {i}")
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos][0] if self.pos < len(self.tokens) else None

    def eat(self, kind):
        tok = self.tokens[self.pos]
        if tok[0] != kind:
            raise ValueError(f"expected {kind}, got {tok[0]}")
        self.pos += 1
        return tok[1]

    def expr(self):
        value = self.term()
        while self.peek() in ("+", "-"):
            op = self.eat(self.peek())
            rhs = self.term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def term(self):
        value = self.power()
        while self.peek() in ("*", "/"):
            op = self.eat(self.peek())
            rhs = self.power()
            value = value * rhs if op == "*" else value // rhs
        return value

    def power(self):
        value = self.factor()
        if self.peek() == "^":
            self.eat("^")
            # Right-associative: the exponent is itself a power.
            return value ** self.power()
        return value

    def factor(self):
        if self.peek() == "(":
            self.eat("(")
            value = self.expr()
            self.eat(")")
            return value
        return self.eat("num")


def evaluate(s: str) -> int:
    p = _Parser(tokenize(s))
    value = p.expr()
    if p.pos != len(p.tokens):
        raise ValueError("trailing tokens")
    return value
