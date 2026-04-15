---
source: fowler_refactoring
topic: move_field
title: "Refactoring: Improving the Design of Existing Code"
authors: Fowler
quality_score: 0.79
---

# Move Field

## Key Definitions

**Move Field**: Move a field from one class to another class that more logically owns it.

**Move Method**: Companion refactoring — move a method to the class that uses its data most, or that should own the behaviour. Almost always performed together with or before Move Field.

**Motivation**: A field is in the wrong class when another class uses it more often than its owning class does. Misplaced data causes Feature Envy (methods that reach across class boundaries), Inappropriate Intimacy, and Shotgun Surgery smells. Moving the field collocates data with the behaviour that acts on it.

**Heuristic — where does the field belong?**: The field belongs in the class whose objects it describes. If `Order` has a `discount_rate` that is actually a property of the `Customer`, move it.

---

## Core Algorithm (Step-by-Step Mechanics)

### Move Field

```
1. INSPECT all users of the field
   - Where is it read?  Where is it written?
   - Is it always passed in as a parameter from another class's context?

2. CREATE the field in the target class
   - Add a getter (and setter if mutable)
   - Initialise it appropriately (constructor parameter or default)

3. COMPILE the target class

4. DECIDE on access strategy:
   a. Source class holds a reference to target → delegate via target.get_field()
   b. Target class has a reference back to source (bidirectional) → use target reference
   c. No existing reference → add one, or redesign (sometimes the real fix)

5. REPLACE all uses in source class to go through the target's accessor

6. REMOVE the field from the source class (or make it private and delegating if
   source must temporarily retain it)

7. COMPILE AND TEST

8. If source class now has no other reason to hold data from target, consider
   whether an Inline Class is the next step
```

### Move Method (companion — apply first or in parallel)

```
1. IDENTIFY methods in source class that reference target-class data more than source-class data
2. CREATE the method in the target class (copy body)
3. FIX references — target class methods now use `self`; former source-class fields
   are received as parameters
4. In source class, replace method body with a delegation call: target.method(...)
5. If source class no longer needs the delegating method externally, remove it (or
   keep it as a forwarding stub during transition)
6. COMPILE AND TEST
```

---

## Code Example — Before / After

```python
# BEFORE — Account holds interest_rate, but it truly belongs to AccountType
class Account:
    def __init__(self, account_type, days_overdrawn):
        self._account_type = account_type
        self._days_overdrawn = days_overdrawn
        self._interest_rate = 0.0  # ← used exclusively by overdraft_charge below

    def overdraft_charge(self):
        if self._account_type.is_premium():
            base_charge = 10.0
            if self._days_overdrawn <= 7:
                return base_charge
            return base_charge + (self._days_overdrawn - 7) * self._interest_rate
        return self._days_overdrawn * self._interest_rate

    def bank_charge(self):
        result = 4.5
        if self._days_overdrawn > 0:
            result += self.overdraft_charge()
        return result


class AccountType:
    def __init__(self, name, premium):
        self._name = name
        self._premium = premium

    def is_premium(self):
        return self._premium


# AFTER — interest_rate moves to AccountType; overdraft_charge follows (Move Method)
class AccountType:
    def __init__(self, name, premium, interest_rate):
        self._name = name
        self._premium = premium
        self._interest_rate = interest_rate   # ← field now lives here

    def is_premium(self):
        return self._premium

    def overdraft_charge(self, days_overdrawn):   # ← method moved here
        if self._premium:
            base_charge = 10.0
            if days_overdrawn <= 7:
                return base_charge
            return base_charge + (days_overdrawn - 7) * self._interest_rate
        return days_overdrawn * self._interest_rate


class Account:
    def __init__(self, account_type, days_overdrawn):
        self._account_type = account_type
        self._days_overdrawn = days_overdrawn
        # interest_rate field removed

    def overdraft_charge(self):
        # delegation — Account no longer owns this logic
        return self._account_type.overdraft_charge(self._days_overdrawn)

    def bank_charge(self):
        result = 4.5
        if self._days_overdrawn > 0:
            result += self.overdraft_charge()
        return result
```

### What changed and why
- `interest_rate` describes a rate policy, not an individual account — it belongs to `AccountType`.
- `overdraft_charge` used `interest_rate` and `is_premium()` — both now in `AccountType`, so the method moved too.
- `Account.overdraft_charge()` is a thin delegation, preserving the public API.

---

## Common Pitfalls / When NOT to Apply

- **Field is truly shared / aggregate**: if the same field is legitimately used equally by two classes, introduce a third class (Extract Class) to own it — don't just move it.
- **Moving without moving the method**: moving a field but leaving behind methods that heavily access it creates a new Feature Envy. Always check whether methods should follow the field.
- **Breaking serialisation / persistence**: if field names are mapped in a schema or serialisation format, coordinate schema migration. Don't refactor field location without updating the data layer.
- **Bi-directional references as a solution**: resist adding a back-pointer just to allow the old class to continue accessing the moved field. That introduces coupling. Instead, pass the data as a parameter.
- **Premature move based on current use**: if the field is about to be used by the source class in upcoming work, moving it now may be premature.

---

## Connections to Other Topics in This Book

- **Move Method**: almost always applied alongside Move Field — data and its behaviour should collocate.
- **Extract Class**: when a cluster of fields (and methods) belongs together but not in the current class, Extract Class creates the new home before moving fields into it.
- **Inline Class**: the inverse of Extract Class; after moving fields out, the source class may become so thin it can be inlined.
- **Feature Envy** (Code Smell): Move Field and Move Method are the canonical cures.
- **Inappropriate Intimacy** (Code Smell): resolved by identifying which class should own shared data and moving field there.
- **Introduce Parameter Object**: if multiple fields always travel together as parameters, group them in a new class — which may then become the home of a Move Field.
- **Encapsulate Field**: run this first if the field is public — you need a controlled accessor before you can safely redirect all callers.
