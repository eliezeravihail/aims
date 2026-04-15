---
source: goodfellow_deep_learning
topic: regularization
title: "Deep Learning — Regularization"
authors: Goodfellow, Bengio, Courville
quality_score: 0.82
---

# Regularization

## Key Definitions

| Term | Definition |
|------|-----------|
| **Regularization** | Any modification made to a learning algorithm intended to reduce its generalisation error, possibly at the cost of increased training error (§7.0). |
| **L2 / weight decay** | Adds `(λ/2)||w||²` to the loss; penalises large weights, shrinks them toward zero each step by factor `(1 − ηλ)`. |
| **L1 regularization** | Adds `λ||w||₁`; induces sparsity — many weights go to exactly zero (useful for feature selection). |
| **Dropout** | Randomly zero out each unit with probability p during training; at inference multiply weights by (1−p) (or use inverted dropout: divide training activations by (1−p)). |
| **Early stopping** | Stop training when validation loss stops improving; implicitly constrains effective model capacity. Equivalent to L2 under some conditions. |
| **Data augmentation** | Creating transformed copies of training examples (flips, crops, noise) — the most reliable regulariser in practice. |
| **Batch normalisation** | Normalises layer inputs per mini-batch; acts as a stochastic regulariser due to mini-batch noise (§8.7, §7.8). |
| **Max-norm constraint** | Clips incoming weight vector per unit to ||w||₂ ≤ c; more stable than L2 with large learning rates. |

## Core Algorithm

**L2 gradient update:**
```
w ← w − η (∂L_data/∂w + λw)
  = w(1 − ηλ) − η ∂L_data/∂w
```

**Inverted Dropout (canonical implementation):**
```
def dropout_forward(x, p_drop, training):
    if not training:
        return x
    mask = (random_uniform(x.shape) > p_drop) / (1.0 - p_drop)
    return x * mask
```

**Early stopping decision:**
```
best_val_loss = ∞
patience_count = 0
for epoch in training_loop:
    val_loss = evaluate(val_set)
    if val_loss < best_val_loss − δ:
        best_val_loss = val_loss
        save_checkpoint()
        patience_count = 0
    else:
        patience_count += 1
    if patience_count >= patience:
        restore_checkpoint(); break
```

## Code Example (PyTorch)

```python
import torch
import torch.nn as nn

class RegularisedNet(nn.Module):
    def __init__(self, d_in, d_h, d_out, drop_p=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, d_h),
            nn.ReLU(),
            nn.Dropout(p=drop_p),          # inverted dropout built-in
            nn.Linear(d_h, d_h),
            nn.ReLU(),
            nn.Dropout(p=drop_p),
            nn.Linear(d_h, d_out),
        )

    def forward(self, x):
        return self.net(x)

model = RegularisedNet(784, 512, 10)

# L2 via weight_decay parameter in optimizer
optimizer = torch.optim.SGD(
    model.parameters(), lr=0.01, weight_decay=1e-4
)

# Max-norm constraint applied after each step
def apply_max_norm(model, max_norm=3.0):
    for name, p in model.named_parameters():
        if "weight" in name:
            norms = p.data.norm(2, dim=1, keepdim=True).clamp(min=1e-8)
            desired = norms.clamp(max=max_norm)
            p.data *= desired / norms

# Training loop with early stopping
best_val, patience, wait = float("inf"), 10, 0
for epoch in range(200):
    model.train()
    # ... training step ...
    model.eval()
    with torch.no_grad():
        val_loss = compute_val_loss()          # your metric here
    apply_max_norm(model)
    if val_loss < best_val - 1e-4:
        best_val, wait = val_loss, 0
        torch.save(model.state_dict(), "best.pt")
    else:
        wait += 1
        if wait >= patience:
            model.load_state_dict(torch.load("best.pt"))
            break
```

## Common Pitfalls

1. **Dropout in eval mode** — always call `model.eval()` before inference; `model.train()` before the training loop. Forgetting this is the most common dropout bug.
2. **Applying weight decay to biases** — standard practice is to exempt biases and normalisation parameters from L2: pass separate parameter groups to the optimizer.
   ```python
   decay_params = [p for n, p in model.named_parameters() if "bias" not in n]
   no_decay_params = [p for n, p in model.named_parameters() if "bias" in n]
   optimizer = torch.optim.AdamW([
       {"params": decay_params, "weight_decay": 1e-4},
       {"params": no_decay_params, "weight_decay": 0.0},
   ], lr=1e-3)
   ```
3. **Too-high dropout** — p > 0.5 in early layers destroys too much signal; use lower p (0.1–0.3) for convolutional layers.
4. **Early stopping with noisy validation** — use a smoothed or exponential-moving-average of validation loss to avoid stopping on a lucky/unlucky batch.
5. **L1 + SGD instability** — L1 penalty has a non-smooth gradient at 0; use proximal SGD or simply sub-gradient `sign(w)` not `w/|w|`.
6. **BatchNorm as a substitute for all regularisation** — BN reduces covariate shift but is not equivalent to dropout; they are complementary.

## Connections to Other Topics (this book)

- **Backprop (Ch. 6)** — L2/L1 terms add directly to the gradient; dropout masks the backward pass through hidden units.
- **Optimization (Ch. 8)** — early stopping interacts with learning-rate schedules; weight decay is equivalent to a MAP estimate with Gaussian prior (§7.1).
- **Convolutional Networks (Ch. 9)** — data augmentation (crop, flip, colour jitter) is the primary regulariser; dropout is less common in conv layers, replaced by spatial dropout or batch norm.
- **Sequence Models (Ch. 10)** — variational dropout (same mask across timesteps) outperforms naive per-step dropout for RNNs; recurrent dropout applied to hidden-to-hidden connections.
