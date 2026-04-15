---
source: fowler_refactoring
topic: replace_pattern
title: "Refactoring: Improving the Design of Existing Code"
authors: Fowler
quality_score: 0.79
---

# Replace Pattern

## Key Definitions

**Replace Pattern** (umbrella term): A family of refactorings that replace a low-level structural construct with a higher-level design pattern. Each "Replace X with Y" refactoring addresses a specific smell by introducing a pattern.

The four most critical Replace refactorings in Fowler:

| Refactoring | Replaces | Pattern introduced |
|---|---|---|
| Replace Conditional with Polymorphism | type-based if/switch | Polymorphism / Strategy |
| Replace Type Code with State/Strategy | mutable type code field | State or Strategy pattern |
| Replace Type Code with Subclasses | immutable type code | Subclassing |
| Replace Constructor with Factory Method | overloaded constructors | Factory Method |

**Type code**: An integer or string constant (or enum) used in conditionals to vary behaviour — the primary target of Replace Conditional with Polymorphism.

**State pattern**: Encapsulates state-specific behaviour in separate state objects; the host delegates to the current state object. Use when the type code can change on an existing instance.

**Strategy pattern**: Encapsulates an algorithm (not state) in a separate object. Use when behaviour varies but the type doesn't change after construction.

---

## Core Algorithm (Step-by-Step Mechanics)

### Replace Conditional with Polymorphism

```
PRECONDITION: Extract Method has already isolated each branch into its own method.
PRECONDITION: All type-based switch/if chains operate on the same type discriminator.

1. CREATE a superclass (or use the existing one) with the method as an abstract/default
   implementation.

2. FOR EACH branch of the conditional:
   a. CREATE a subclass (if it doesn't exist).
   b. OVERRIDE the method in the subclass with the body of that branch.
   c. REMOVE the branch from the superclass conditional.

3. MAKE the superclass method abstract (or raise NotImplementedError) once all
   branches have been moved to subclasses.

4. COMPILE AND TEST after each subclass migration (don't move all at once).

5. REMOVE the conditional method from the superclass (it should now be empty or raise).

6. VERIFY callers — they should be calling the method on the superclass type;
   the runtime dispatches to the correct subclass.
```

### Replace Type Code with State/Strategy

```
WHEN: The type code field can change on an existing object at runtime.

1. CREATE a State/Strategy class hierarchy:
   - Abstract base: e.g. EmployeeType
   - Concrete subclasses: EngineerType, SalesmanType, ManagerType

2. ADD a type_code property to the abstract base (delegates to subclass constant).

3. IN the host class, REPLACE the primitive type_code field with a reference to
   a State/Strategy object.

4. CREATE a factory method or setter on the host:
       def set_type(self, type_code):
           self._type = EmployeeType.new_type(type_code)

5. CHANGE all reads of the type_code in conditionals to call self._type.type_code
   (no behaviour change yet — just access path change).

6. COMPILE AND TEST.

7. NOW apply Replace Conditional with Polymorphism to move branching logic
   into the State/Strategy subclasses.
```

---

## Code Example — Replace Conditional with Polymorphism

```python
# BEFORE — switch on employee type repeated throughout the codebase
class Employee:
    ENGINEER = 0
    SALESMAN = 1
    MANAGER = 2

    def __init__(self, employee_type):
        self._type = employee_type

    def pay_amount(self, monthly_salary, commission, bonus):
        if self._type == self.ENGINEER:
            return monthly_salary
        elif self._type == self.SALESMAN:
            return monthly_salary + commission
        elif self._type == self.MANAGER:
            return monthly_salary + bonus
        raise ValueError(f"Unknown employee type: {self._type}")

    def vacation_days(self, years_of_service):
        if self._type == self.ENGINEER:
            return 15 + years_of_service
        elif self._type == self.SALESMAN:
            return 10
        elif self._type == self.MANAGER:
            return 20 + years_of_service * 2
        raise ValueError(f"Unknown employee type: {self._type}")


# AFTER — Replace Type Code with State/Strategy + Replace Conditional with Polymorphism
from abc import ABC, abstractmethod

class EmployeeType(ABC):
    @abstractmethod
    def pay_amount(self, monthly_salary, commission, bonus):
        ...

    @abstractmethod
    def vacation_days(self, years_of_service):
        ...

    @staticmethod
    def new_type(type_code):
        types = {0: Engineer, 1: Salesman, 2: Manager}
        cls = types.get(type_code)
        if cls is None:
            raise ValueError(f"Unknown type code: {type_code}")
        return cls()


class Engineer(EmployeeType):
    def pay_amount(self, monthly_salary, commission, bonus):
        return monthly_salary

    def vacation_days(self, years_of_service):
        return 15 + years_of_service


class Salesman(EmployeeType):
    def pay_amount(self, monthly_salary, commission, bonus):
        return monthly_salary + commission

    def vacation_days(self, years_of_service):
        return 10


class Manager(EmployeeType):
    def pay_amount(self, monthly_salary, commission, bonus):
        return monthly_salary + bonus

    def vacation_days(self, years_of_service):
        return 20 + years_of_service * 2


class Employee:
    def __init__(self, type_code):
        self._type = EmployeeType.new_type(type_code)

    def set_type(self, type_code):           # supports State pattern (mutable)
        self._type = EmployeeType.new_type(type_code)

    def pay_amount(self, monthly_salary, commission, bonus):
        return self._type.pay_amount(monthly_salary, commission, bonus)

    def vacation_days(self, years_of_service):
        return self._type.vacation_days(years_of_service)
```

### What changed and why
- Adding a new employee type now requires adding one new subclass — no existing method is touched (Open/Closed Principle).
- The type-based `if/elif` chains have been eliminated from `Employee` entirely.
- `set_type()` allows the State pattern — an existing Employee can change type at runtime.

---

## Replace Constructor with Factory Method

```python
# BEFORE — callers must know numeric codes
emp = Employee(0)   # What does 0 mean?

# AFTER — named factory methods encode intent
class Employee:
    @staticmethod
    def create_engineer():
        return Employee(0)

    @staticmethod
    def create_salesman():
        return Employee(1)

    @staticmethod
    def create_manager():
        return Employee(2)

emp = Employee.create_engineer()   # self-documenting
```

---

## Common Pitfalls / When NOT to Apply

- **Simple, stable two-branch conditionals**: a single `if/else` that will never grow and has no duplicate elsewhere is clearer than a two-class hierarchy. Apply polymorphism only when there are three or more variant behaviours or when new variants are expected.
- **Replacing with subclasses when type can change**: if an Employee can be promoted from Engineer to Manager, subclassing is wrong — the object can't change its class. Use State/Strategy instead.
- **Creating shallow subclasses**: if the overriding method is identical in all subclasses, the conditional is not really type-based; look for a different smell.
- **Ignoring the factory**: if you introduce a class hierarchy but leave `if type == X: return X()` constructions scattered in callers, you've moved the switch statement, not removed it. Centralise creation in a factory.
- **Premature polymorphism**: if the behaviour truly never varies, a class hierarchy adds complexity without benefit.

---

## Connections to Other Topics in This Book

- **Decompose Conditional**: prerequisite — branches must be extracted into named methods before they can be overridden.
- **Extract Class**: creates the subclass skeleton that will host the overriding methods.
- **Switch Statements** (Code Smell): Replace Conditional with Polymorphism is the canonical cure for this smell.
- **Temporary Field** (Code Smell): often caused by type codes; State/Strategy pattern resolves it.
- **Move Method**: once subclasses are created, type-specific helper methods are moved into the appropriate subclass.
- **Replace Parameter with Explicit Methods**: an alternative to polymorphism when the number of variants is small and stable.
- **Introduce Null Object**: a specialised Replace Pattern — replaces `if obj is None` checks with a NullObject that does nothing, enabling uniform treatment.
