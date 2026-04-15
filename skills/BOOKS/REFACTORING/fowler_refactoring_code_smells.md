---
source: fowler_refactoring
topic: code_smells
title: "Refactoring: Improving the Design of Existing Code"
authors: Fowler
quality_score: 0.79
---

# Code Smells

## Key Definitions

**Code smell**: A surface indication that usually corresponds to a deeper problem in the system. Not a bug — the code may work — but it signals that the design is degrading and refactoring is warranted.

**Technical debt**: The accumulation of smells over time that makes future changes progressively harder and riskier.

**Refactoring trigger**: A smell is the signal; a specific refactoring technique is the cure. Smells do not mandate refactoring — they prompt investigation.

---

## Canonical Smell Catalogue (Fowler's 22 Smells)

### Bloaters — things that have grown too large
| Smell | Symptom | Primary Refactoring |
|---|---|---|
| Long Method | Method body > ~10 lines | Extract Method |
| Large Class | Class has too many fields/methods | Extract Class, Extract Subclass |
| Primitive Obsession | Scalars used where objects belong | Replace Data Value with Object, Introduce Parameter Object |
| Long Parameter List | > 3–4 parameters | Introduce Parameter Object, Preserve Whole Object |
| Data Clumps | Same 2–3 fields always travel together | Extract Class, Introduce Parameter Object |

### Object-Orientation Abusers — OO principles misapplied
| Smell | Symptom | Primary Refactoring |
|---|---|---|
| Switch Statements | switch/if-else on type codes | Replace Conditional with Polymorphism |
| Temporary Field | Field set only in some scenarios | Extract Class, Introduce Null Object |
| Refused Bequest | Subclass ignores inherited methods | Replace Inheritance with Delegation |
| Alternative Classes with Different Interfaces | Two classes do the same thing | Rename Method, Move Method |

### Change Preventers — one logical change requires many edits
| Smell | Symptom | Primary Refactoring |
|---|---|---|
| Divergent Change | One class changed for many reasons | Extract Class |
| Shotgun Surgery | One change touches many classes | Move Method, Move Field, Inline Class |
| Parallel Inheritance Hierarchies | Adding a subclass requires adding another | Move Method, Move Field |

### Dispensables — unnecessary code
| Smell | Symptom | Primary Refactoring |
|---|---|---|
| Lazy Class | Class does too little to justify its existence | Inline Class, Collapse Hierarchy |
| Speculative Generality | Code added for hypothetical future use | Collapse Hierarchy, Remove Parameter, Rename Method |
| Dead Code | Unreachable or unused code | Delete it |
| Duplicate Code | Same structure in multiple places | Extract Method, Pull Up Method, Form Template Method |

### Couplers — excessive coupling between classes
| Smell | Symptom | Primary Refactoring |
|---|---|---|
| Feature Envy | Method uses another class's data more than its own | Move Method |
| Data Class | Class has only fields + getters/setters, no logic | Move Method (from clients) |
| Inappropriate Intimacy | Classes access each other's private parts | Move Method, Move Field, Extract Class |
| Message Chains | `a.getB().getC().getD()` | Hide Delegate, Extract Method |
| Middle Man | Class delegates most work to another | Remove Middle Man |
| Incomplete Library Class | Library class missing a needed method | Introduce Foreign Method, Introduce Local Extension |
| Comments | Comment is explaining bad code | Extract Method + rename to make comment unnecessary |

---

## Detection Algorithm

```
for each unit of code (method, class, module):
    1. Measure size metrics (lines, parameters, fields)
    2. Trace data flows — does data travel far from where it lives?
    3. Check for conditional logic on type/kind/category
    4. Look for duplicated structural patterns
    5. Ask: "If I changed X, how many files would I touch?"
    6. Ask: "Does this method use its own class's data, or another's?"
```

---

## Code Example — Detecting Feature Envy

```python
# BEFORE — SmellDetector: method envies another class's data
class Order:
    def __init__(self, customer, items):
        self.customer = customer  # Customer object
        self.items = items

class InvoicePrinter:
    def print_invoice(self, order):
        # This method uses Order.customer's data more than InvoicePrinter's own data
        name = order.customer.get_name()
        address = order.customer.get_address()
        city = order.customer.get_city()
        zip_code = order.customer.get_zip()
        header = f"{name}\n{address}\n{city}, {zip_code}"
        total = sum(item.price * item.qty for item in order.items)
        print(f"{header}\nTotal: {total}")

# AFTER — move the envied behaviour to where the data lives
class Customer:
    def __init__(self, name, address, city, zip_code):
        self._name = name
        self._address = address
        self._city = city
        self._zip_code = zip_code

    def formatted_address(self):          # behaviour now lives with data
        return f"{self._name}\n{self._address}\n{self._city}, {self._zip_code}"

class InvoicePrinter:
    def print_invoice(self, order):
        total = sum(item.price * item.qty for item in order.items)
        print(f"{order.customer.formatted_address()}\nTotal: {total}")
```

---

## Common Pitfalls / When NOT to Refactor

- **Refactoring during a deadline**: smells are notes for later; fix after delivery.
- **Over-reacting to Comments smell**: some comments are legitimately helpful (algorithm explanations, regulatory references). Only replace comments that compensate for unclear code.
- **Conflating smell with bug**: smells are design problems, not correctness problems. Fix bugs first, then refactor.
- **Middle Man is not always bad**: proxy and decorator patterns intentionally delegate — distinguish pattern from accident.
- **Speculative Generality**: resist the urge to remove "future-proof" abstractions if they're actively used by tests.

---

## Connections to Other Topics in This Book

- **Extract Method** is the single most-used cure for Long Method, Duplicate Code, and Comments smells.
- **Move Field / Move Method** cures Feature Envy, Inappropriate Intimacy, and Shotgun Surgery.
- **Decompose Conditional** directly attacks the Switch Statements smell and complex nested conditionals.
- **Replace Pattern** (Replace Conditional with Polymorphism, Replace Type Code with State/Strategy) is the systematic cure for Switch Statements and Temporary Field.
- Smells are the *diagnostic layer*; the refactoring catalogue is the *therapeutic layer* — always start with smell identification before choosing a technique.
