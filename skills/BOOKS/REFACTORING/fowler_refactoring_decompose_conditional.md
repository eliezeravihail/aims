---
source: fowler_refactoring
topic: decompose_conditional
title: "Refactoring: Improving the Design of Existing Code"
authors: Fowler
quality_score: 0.79
---

# Decompose Conditional

## Key Definitions

**Decompose Conditional**: Extract the condition expression, the then-branch, and the else-branch each into their own well-named methods.

**Motivation**: Complex conditionals are the biggest source of obscurity in programs. The reader must mentally evaluate both the condition and its consequences. Naming each part forces clarity and reveals intent. The result is code that reads like a business rule specification.

**Consolidate Conditional Expression**: A related refactoring — when several conditions all lead to the same result, combine them with `and`/`or` before extracting (reduces the number of methods needed).

**Consolidate Duplicate Conditional Fragments**: When the same code appears in every branch, move it outside the conditional.

**Nested conditional vs. guard clause**: Two shapes of conditional warrant different treatments:
- **Nested if/else** (all branches are normal cases) → Decompose Conditional
- **One path is the normal case, others are edge cases** → Replace Nested Conditional with Guard Clauses

---

## Core Algorithm (Step-by-Step Mechanics)

### Decompose Conditional

```
1. IDENTIFY the conditional (if / else-if / else chain or ternary)

2. EXTRACT the condition expression
   - Name it for what the business rule IS, not what it compares
   - Bad:  is_date_before_summer_and_plan_is_regular()
   - Good: is_summer_rate()

3. EXTRACT the then-branch body into a method
   - Name it for what the branch DOES as an action or result
   - E.g.: summer_charge(), apply_winter_rate()

4. EXTRACT the else-branch body (and each else-if branch) similarly

5. REPLACE the original if/else with:
       if extracted_condition():
           extracted_then_body()
       else:
           extracted_else_body()

6. COMPILE AND TEST

7. REVIEW: can any of the extracted methods be combined with existing methods?
```

### Replace Nested Conditional with Guard Clauses

```
1. IDENTIFY the one "normal" execution path among the branches

2. For each abnormal/exceptional condition at the top of the method:
       if exceptional_condition:
           return early_result   # guard clause

3. REMOVE the now-unnecessary nesting

4. COMPILE AND TEST

5. Often reveals further consolidation opportunities
```

---

## Code Example — Before / After

```python
# BEFORE — complex conditional mixing business logic with computation
class BillingService:
    def calculate_charge(self, date, quantity, plan):
        if date < SUMMER_START or date > SUMMER_END:
            charge = quantity * plan.winter_rate + plan.winter_service_charge
        else:
            charge = quantity * plan.summer_rate
        return charge


# AFTER — Decompose Conditional applied
class BillingService:
    def calculate_charge(self, date, quantity, plan):
        if self._is_summer(date):
            return self._summer_charge(quantity, plan)
        else:
            return self._winter_charge(quantity, plan)

    def _is_summer(self, date):
        return SUMMER_START <= date <= SUMMER_END

    def _summer_charge(self, quantity, plan):
        return quantity * plan.summer_rate

    def _winter_charge(self, quantity, plan):
        return quantity * plan.winter_rate + plan.winter_service_charge
```

### Guard Clause example

```python
# BEFORE — nested conditionals, all paths look equally "normal"
def get_pay_amount(employee):
    if employee.is_dead:
        result = dead_amount()
    else:
        if employee.is_separated:
            result = separated_amount()
        else:
            if employee.is_retired:
                result = retired_amount()
            else:
                result = normal_pay_amount(employee)
    return result


# AFTER — guard clauses make the exceptional cases obvious; normal path is unindented
def get_pay_amount(employee):
    if employee.is_dead:
        return dead_amount()
    if employee.is_separated:
        return separated_amount()
    if employee.is_retired:
        return retired_amount()
    return normal_pay_amount(employee)
```

### Consolidate Conditional Expression example

```python
# BEFORE — three conditions, same result
def disability_amount(employee):
    if employee.seniority < 2:
        return 0
    if employee.months_disabled > 12:
        return 0
    if employee.is_part_time:
        return 0
    # ... calculate disability amount

# STEP 1 — Consolidate first, THEN extract (makes intent of combined check clear)
def disability_amount(employee):
    if _is_not_eligible_for_disability(employee):
        return 0
    # ... calculate disability amount

def _is_not_eligible_for_disability(employee):
    return (employee.seniority < 2
            or employee.months_disabled > 12
            or employee.is_part_time)
```

---

## Common Pitfalls / When NOT to Apply

- **Single-use, trivially short conditions**: if the condition is already `if x > 0:` — that is already readable. Extracting to `_is_positive(x)` adds a lookup with no comprehension benefit.
- **Conditions with many parameters**: if the extracted predicate method needs to receive 4+ variables to evaluate the condition, the condition expression may not be the right extraction boundary — consider Introduce Parameter Object first.
- **Boolean return as a workaround for early return**: don't decompose into `_should_return_early()` and then check its result; use guard clauses directly.
- **Over-decomposing**: extracting the then-branch into a method that's called exactly once and is two lines long can obscure rather than clarify. Extract only when the body has genuine conceptual identity.
- **Neglecting the else-if chain**: in a long if/elif chain, each branch must be reviewed — sometimes Replace Conditional with Polymorphism is the right follow-up.

---

## Connections to Other Topics in This Book

- **Extract Method**: Decompose Conditional IS Extract Method applied specifically to conditional expressions and branches — the mechanics are identical.
- **Replace Conditional with Polymorphism** (Replace Pattern): after decomposition reveals repeated type-based branching, polymorphism eliminates the branches entirely.
- **Replace Nested Conditional with Guard Clauses**: companion technique for the asymmetric conditional shape.
- **Consolidate Conditional Expression**: prerequisite when multiple conditions share the same outcome — consolidate first, then extract the predicate.
- **Introduce Null Object**: eliminates a whole class of defensive null-check conditionals.
- **Switch Statements** (Code Smell): decomposing the branches of a switch is the first step toward replacing it with polymorphism.
- **Specification Pattern**: when decomposed predicates grow into a family, the Specification pattern (compose predicates as objects) is the natural evolution.
