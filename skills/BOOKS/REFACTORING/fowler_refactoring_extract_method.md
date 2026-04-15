---
source: fowler_refactoring
topic: extract_method
title: "Refactoring: Improving the Design of Existing Code"
authors: Fowler
quality_score: 0.79
---

# Extract Method

## Key Definitions

**Extract Method**: Take a code fragment that can be grouped together, move it into its own method, and replace the old code with a call to the new method.

**Motivation**: The most frequently applied refactoring. Addresses Long Method, Duplicate Code, and Comments smells. Fine-grained methods improve reuse, enable polymorphism, and make higher-level algorithms self-documenting.

**Inverse operation**: Inline Method — when a method body is as clear as its name, eliminate the indirection.

**Composed Method pattern**: A method should be composed entirely of calls to other methods at the same level of abstraction (one sentence per line of the body). Extract Method is how you achieve this.

---

## Core Algorithm (Step-by-Step Mechanics)

```
1. IDENTIFY the fragment
   - Code that does one identifiable thing
   - Comments that explain what a block does → the comment becomes the method name
   - Any fragment more than 5–7 lines long

2. CREATE the new method
   - Name it for WHAT it does (intention), not HOW (implementation)
   - If you can't name it clearly, the extraction boundary is wrong

3. ANALYZE local variables (the hard part)
   a. Variables read but NOT modified by the fragment → pass as parameters
   b. Variables modified by the fragment:
      - Modified but not used after the fragment → declare inside new method
      - Modified AND used after the fragment:
          * Only one such variable → return it from new method
          * More than one → consider Extract Class, or split the fragment further
   c. Variables used before AND after AND inside the fragment → parameter + return

4. COPY the fragment into the new method

5. COMPILE and verify no references remain to local vars not passed in

6. REPLACE the original fragment with a call to the new method

7. COMPILE AND TEST

8. REVIEW the name — after seeing it in context, a better name often emerges
```

---

## Code Example — Before / After

```python
# BEFORE — one monolithic method; comment signals extraction point
class OrderProcessor:
    def print_owing(self, order):
        outstanding = 0.0

        # print banner
        print("***********************")
        print("***** Customer Owes ***")
        print("***********************")

        # calculate outstanding
        for item in order.items:
            outstanding += item.amount

        # print details
        print(f"name: {order.customer}")
        print(f"amount: {outstanding}")


# AFTER — each comment became a method name
class OrderProcessor:
    def print_owing(self, order):
        self._print_banner()
        outstanding = self._calculate_outstanding(order)
        self._print_details(order, outstanding)

    def _print_banner(self):
        print("***********************")
        print("***** Customer Owes ***")
        print("***********************")

    def _calculate_outstanding(self, order):
        return sum(item.amount for item in order.items)

    def _print_details(self, order, outstanding):
        print(f"name: {order.customer}")
        print(f"amount: {outstanding}")
```

### Why this works
- `print_owing` now reads like a table of contents — three steps at one abstraction level.
- Each extracted method is independently testable.
- `_calculate_outstanding` can be reused by any method that needs the total.

---

## Handling the Tricky Case: Multiple Modified Variables

```python
# BEFORE — two temps modified inside the fragment
def process(self, data):
    total = 0
    count = 0
    for x in data:
        total += x
        count += 1
    average = total / count if count else 0
    print(average)

# Option A: return a small object / named tuple (preferred when values are cohesive)
from collections import namedtuple

Stats = namedtuple("Stats", ["total", "count"])

def _accumulate(self, data):
    total = sum(data)
    count = len(data)
    return Stats(total, count)

def process(self, data):
    stats = self._accumulate(data)
    average = stats.total / stats.count if stats.count else 0
    print(average)

# Option B: if they aren't cohesive, split into two separate extractions
```

---

## Common Pitfalls / When NOT to Apply

- **Name is a question, not a declaration**: if you write `_do_stuff()` or `_helper()`, stop — you haven't found the right boundary yet.
- **Extracting too small**: a one-line extraction that will never be reused just adds a level of indirection. Apply only when the name communicates intent better than the expression.
- **Temp variable inflation**: extracting into a method removes the need for many temps — eliminate them with `Replace Temp with Query` first, then extract.
- **Over-passing parameters**: if you need to pass > 3 parameters into the extracted method, that is a signal to use `Introduce Parameter Object` or reconsider the extraction boundary.
- **Side effects in calculations**: extracted calculation methods should be pure (no I/O, no mutation). If the fragment mixes calculation and side effects, separate them first.

---

## Connections to Other Topics in This Book

- **Replace Temp with Query**: eliminates temps before extraction, simplifying parameter lists.
- **Introduce Parameter Object**: reduces long parameter lists created by extraction.
- **Move Method**: once extracted, a method may belong in a different class (often revealed by Feature Envy smell).
- **Decompose Conditional**: a specialised application of Extract Method applied to condition expressions and their branches.
- **Replace Conditional with Polymorphism**: requires prior extraction of the branching logic to make it overridable.
- **Form Template Method**: requires prior extraction of steps so that subclasses can override individual steps.
- **Pull Up Method**: extracted method may be common to multiple subclasses — move it to the superclass.
