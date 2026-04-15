# Optimization
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a
**Read more:** https://www.deeplearningbook.org/contents/optimization.html — Chapter 8: Optimization for Training Deep Models

## What this book adds
The book frames deep learning optimization as fundamentally different from classical convex optimization — the goal is **not** to reach a global minimum, but to reach a point that generalizes well. It analyzes why **sharp minima generalize worse than flat minima** (a finding with direct practical implications for batch size), explains the **pathological curvature** problem that motivates momentum and Adam, and shows why the condition number of the Hessian governs convergence speed.

## Core Concept
Training minimizes a non-convex loss over a high-dimensional parameter space. Classical convergence guarantees do not apply. In practice, SGD finds solutions that generalize well — not because it finds global minima, but because the optimization landscape of overparameterized networks has many good local minima that are essentially equivalent in loss.

## Key Definitions
- **Ill-conditioning:** when the Hessian H has a large condition number (ratio of max to min eigenvalue), gradient descent oscillates in high-curvature directions and crawls in low-curvature ones
- **Momentum:** maintains velocity `v ← μv - η∇L`; accumulates gradients in consistent directions, dampens oscillations in high-curvature directions
- **Adaptive learning rates:** scale η per parameter by accumulated gradient magnitude (RMSProp, Adam) — addresses ill-conditioning without computing H
- **Saddle points:** points where gradient = 0 but H has both positive and negative eigenvalues; common in high-dimensional loss surfaces; SGD escapes them via noise

## Deep Dive

### Why large batch size hurts generalization — the sharp/flat minima finding (§8.1.3)
The book cites evidence that large-batch SGD converges to **sharp minimizers** (high curvature, small neighborhood), while small-batch SGD converges to **flat minimizers** (low curvature, large neighborhood). Sharp minimizers generalize worse because small perturbations to the weights (equivalent to test-time distribution shift) cause large loss increases.

Practical implication: doubling batch size requires a compensating increase in learning rate AND training time — not just the learning rate as the linear scaling rule suggests.

### Momentum as a differential equation (§8.3.2)
SGD with momentum is a discretization of a continuous ODE. In the limit of small step size, momentum converges to the **critical damping regime** — it eliminates oscillations while descending the fastest possible path. The critical damping condition is `μ = (1 - ε)` where ε is the step size, leading to the practical recommendation of `μ = 0.9` for most settings.

### Why Adam works — the EMA interpretation (§8.5.3)
Adam maintains two exponential moving averages:
- `m ← β₁m + (1−β₁)g` — EMA of gradients (direction)
- `v ← β₂v + (1−β₂)g²` — EMA of squared gradients (magnitude)

The update `η·m̂/√v̂` normalizes each parameter's learning rate by the **RMS of its recent gradients**. Parameters with consistently large gradients get a smaller effective lr; parameters with small/noisy gradients get a larger one. This is the adaptive ill-conditioning correction — without computing the Hessian.

The bias correction `m̂ = m/(1−β₁ᵗ)` is critical at step 0: without it, m starts at 0 and the first update is too small by a factor of (1−β₁).

```python
# Adam from scratch — Algorithm 8.7 in the book
def adam_step(params, grads, state, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
    state['t'] = state.get('t', 0) + 1
    t = state['t']
    for p, g in zip(params, grads):
        key = id(p)
        m = state.get(f'm_{key}', np.zeros_like(p))
        v = state.get(f'v_{key}', np.zeros_like(p))

        m = beta1 * m + (1 - beta1) * g
        v = beta2 * v + (1 - beta2) * g ** 2

        m_hat = m / (1 - beta1 ** t)   # bias correction — critical at early steps
        v_hat = v / (1 - beta2 ** t)

        p -= lr * m_hat / (np.sqrt(v_hat) + eps)

        state[f'm_{key}'] = m
        state[f'v_{key}'] = v
```

### Gradient clipping — two strategies with different behaviors (§8.2.4)
The book distinguishes:
1. **Clip by value:** `g = clip(g, -c, c)` — changes gradient direction; can cause artifacts
2. **Clip by norm:** `g = g · c / max(‖g‖, c)` — preserves direction, only shrinks magnitude

Clip-by-norm is almost always preferred. The recommended threshold `c=1.0` is empirical — the book notes that a better principled choice is the 95th percentile of the gradient norm during a warm-up phase.

## Code Examples

### Visualizing why condition number matters
```python
import numpy as np
import matplotlib.pyplot as plt

# Loss surface with high condition number: L = 100x² + y²
# GD oscillates on x-axis while crawling on y-axis
def loss(x, y): return 100 * x**2 + y**2
def grad(x, y): return np.array([200*x, 2*y])

def sgd_path(start, lr=0.005, steps=50):
    path = [start.copy()]
    p = start.copy()
    for _ in range(steps):
        p -= lr * grad(*p)
        path.append(p.copy())
    return np.array(path)

def sgd_momentum_path(start, lr=0.005, mu=0.9, steps=50):
    path = [start.copy()]
    p, v = start.copy(), np.zeros(2)
    for _ in range(steps):
        v = mu * v - lr * grad(*p)
        p += v
        path.append(p.copy())
    return np.array(path)

# Momentum converges in far fewer steps — the book's key illustration
```

### AdamW — why it differs from Adam + L2 in PyTorch
```python
# Adam + L2 weight_decay (WRONG for adaptive optimizers)
# The L2 gradient gets divided by √v̂, making regularization weaker for params with high gradient variance
optimizer_wrong = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)

# AdamW — weight decay applied AFTER the adaptive update (correct)
# p = p - lr * m̂/√v̂  - lr * λ * p
# The λ term is not normalized by √v̂
optimizer_correct = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
```

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Linear learning rate scaling with batch size | Sharp/flat minima — large batches need more than proportionally higher lr to find flat minima | Use linear scaling + warmup, or LARS/LAMB for very large batches |
| Skipping bias correction in Adam | First several steps are severely underestimated — training instability | Always use bias correction; it's Algorithm 8.7's explicit step |
| Clipping by value | Changes gradient direction, introducing systematic bias | Always clip by norm |
| Tuning lr on training loss | Sharp minima have low train loss, bad generalization | Monitor validation loss, not training loss, when tuning lr |

## Connections
- **backprop.md** — gradients from backprop are the direct input to every update rule here
- **regularization.md** — AdamW is the canonical optimizer when using weight decay
- **sequence_models.md** — gradient clipping is especially critical for RNNs (§8.2.4 discusses this in the context of BPTT)
