# Optimization
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a

## Core Concept
Deep learning optimization minimizes a non-convex loss over parameters. Gradient descent variants differ in how they accumulate gradient history and adapt per-parameter learning rates.

## Key Definitions
- **SGD:** θ ← θ − η∇L; noisy but generalizes well
- **Momentum:** accumulates velocity v ← μv − η∇L; dampens oscillations
- **RMSProp:** divides η by a running average of squared gradients; adapts per-parameter
- **Adam:** combines momentum + RMSProp; biased estimates corrected at startup
- **AdamW:** Adam with decoupled weight decay (use instead of Adam + L2)
- **Learning rate schedule:** step decay, cosine annealing, warm restarts (SGDR), linear warmup

## Algorithm

```python
# Adam update (from scratch)
m = beta1 * m + (1 - beta1) * g          # 1st moment (momentum)
v = beta2 * v + (1 - beta2) * g**2       # 2nd moment (RMS)
m_hat = m / (1 - beta1**t)               # bias correction
v_hat = v / (1 - beta2**t)
theta -= lr * m_hat / (sqrt(v_hat) + eps)

# PyTorch — recommended setup
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

for epoch in range(epochs):
    train(...)
    scheduler.step()
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Adam + L2 weight_decay | Use AdamW instead |
| Constant LR for long training | Add cosine decay or reduce-on-plateau |
| Skipping LR warmup for large batches | Linear warmup for first 5–10% of steps |
| Gradient explosion | Clip norm: `torch.nn.utils.clip_grad_norm_(params, 1.0)` |

## Connections
- **backprop.md** — gradients are the input to every optimizer
- **regularization.md** — AdamW is the canonical optimizer when using weight decay
