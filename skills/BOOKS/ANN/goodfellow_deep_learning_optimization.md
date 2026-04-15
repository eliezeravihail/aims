---
source: goodfellow_deep_learning
topic: optimization
title: "Deep Learning — Optimization"
authors: Goodfellow, Bengio, Courville
quality_score: 0.82
---

# Optimization for Deep Learning

## Key Definitions

| Term | Definition |
|------|-----------|
| **SGD** | Stochastic Gradient Descent — update parameters with the gradient estimated on a single mini-batch; introduces noise that can escape sharp minima. |
| **Momentum** | Accumulates a velocity vector in the direction of persistent gradients; dampens oscillations in high-curvature directions (§8.3.2). |
| **Nesterov momentum** | Evaluates gradient at the "look-ahead" position `w + μv`; converges faster than classical momentum on convex functions. |
| **AdaGrad** | Accumulates squared gradients per-parameter; divides lr by √(Σg²). Good for sparse gradients; lr decays to 0 over time. |
| **RMSProp** | Exponential moving average of squared gradients (fixes AdaGrad's monotone decay); widely used in non-stationary settings. |
| **Adam** | Combines momentum (first moment) + RMSProp (second moment) with bias correction; de-facto default for most DL tasks. |
| **AdamW** | Adam with decoupled weight decay (L2 applied to w directly, not to the adapted gradient); preferred over Adam+L2. |
| **Learning rate schedule** | Policy that changes lr over training: step decay, cosine annealing, 1-cycle, warmup+decay. |
| **Gradient clipping** | Scales the gradient when its norm exceeds a threshold; critical for RNNs and transformers. |
| **Loss surface** | High-dimensional, non-convex; has many saddle points (far more common than local minima at scale, §8.2.3). |
| **Batch size** | Larger batches → lower gradient variance but sharper minima and worse generalisation (linear scaling rule for lr). |

## Core Algorithms

**SGD with momentum (classical):**
```
v ← μv − η ∇_w L
w ← w + v
```

**Nesterov (PyTorch convention):**
```
v ← μv + ∇_w L(w + μv)    # gradient at look-ahead
w ← w − η v
```

**Adam update:**
```
m ← β₁ m + (1 − β₁) g          # first moment
v ← β₂ v + (1 − β₂) g²         # second moment
m̂ = m / (1 − β₁ᵗ)              # bias correction
v̂ = v / (1 − β₂ᵗ)
w ← w − η m̂ / (√v̂ + ε)
```
Defaults: β₁=0.9, β₂=0.999, ε=1e-8

**Gradient clipping by global norm:**
```
total_norm = sqrt(Σ_p ||grad_p||²)
clip_coef  = max_norm / max(total_norm, max_norm)
for each p: grad_p *= clip_coef
```

## Code Example (PyTorch)

```python
import torch
import torch.nn as nn

model = nn.Linear(256, 10)
optimizer = torch.optim.AdamW(
    model.parameters(), lr=3e-4, betas=(0.9, 0.999),
    eps=1e-8, weight_decay=1e-2
)

# Cosine annealing with linear warmup (common recipe)
total_steps = 10_000
warmup_steps = 500

def lr_lambda(step):
    if step < warmup_steps:
        return step / warmup_steps
    progress = (step - warmup_steps) / (total_steps - warmup_steps)
    return 0.5 * (1.0 + torch.cos(torch.tensor(progress * 3.14159)).item())

scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

for step, (x, y) in enumerate(dataloader):
    optimizer.zero_grad()
    loss = nn.CrossEntropyLoss()(model(x), y)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()
    scheduler.step()

# SGD + Nesterov for CV tasks
sgd = torch.optim.SGD(
    model.parameters(), lr=0.1, momentum=0.9,
    nesterov=True, weight_decay=1e-4
)
# With cosine annealing:
cos_sched = torch.optim.lr_scheduler.CosineAnnealingLR(sgd, T_max=200)
```

## Learning Rate Selection Guide

| Model type | Optimizer | Typical η | Notes |
|-----------|-----------|-----------|-------|
| ResNet (ImageNet) | SGD+Nesterov | 0.1 | Decay ×0.1 at epochs 30,60,90 |
| Transformer | AdamW | 1e-4 – 3e-4 | Warmup 4–10 % of steps + cosine |
| RNN/LSTM | Adam | 1e-3 | Clip gradients at 1.0 or 5.0 |
| MLP / small nets | Adam | 1e-3 | Often no schedule needed |

## Common Pitfalls

1. **Wrong weight decay with Adam** — use `AdamW`, not `Adam` with L2 in the loss; the latter adapts the decay per-parameter, undermining regularisation.
2. **Missing warmup with large batch / transformer** — cold-starting with a large lr causes loss spikes; always warm up ≥ 1 % of total steps.
3. **Not zeroing gradients** — `optimizer.zero_grad()` must precede `loss.backward()` every step (or set `set_to_none=True` for speed).
4. **Learning rate too low with momentum** — momentum amplifies the effective lr; if you add momentum to SGD, reduce η proportionally.
5. **Batch size scaling without lr scaling** — when doubling batch size, double lr (linear scaling rule, Goyal et al. 2017) and adjust warmup length.
6. **Saddle points vs local minima** — in high dimensions nearly all critical points with low loss are saddle points, not local minima; noise from SGD automatically escapes them.
7. **Plateau ≠ convergence** — a flat loss can indicate a saddle point; try perturbing lr slightly or switching optimizer.

## Connections to Other Topics (this book)

- **Backprop (Ch. 6)** — optimizers consume gradients; gradient clipping directly modifies the gradient before each optimizer step.
- **Regularization (Ch. 7)** — weight decay interacts with the optimizer; AdamW decouples it correctly from adaptive scaling.
- **Convolutional Networks (Ch. 9)** — SGD+momentum is the preferred optimizer for ResNets; batch normalisation makes the loss surface smoother, enabling larger lr.
- **Sequence Models (Ch. 10)** — gradient clipping is mandatory for RNNs/LSTMs due to long backprop-through-time paths causing exploding gradients.
