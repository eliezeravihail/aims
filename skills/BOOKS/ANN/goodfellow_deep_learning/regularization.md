# Regularization
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a
**Read more:** https://www.deeplearningbook.org/contents/regularization.html — Chapter 7: Regularization for Deep Learning

## What this book adds
The book provides a unified theoretical framework showing that most regularization techniques reduce to the same underlying principle: constraining the **effective capacity** of the model. Notably, it proves that **early stopping is exactly equivalent to L2 regularization** under certain conditions, and it explains why **dropout can be interpreted as training an exponential ensemble** of 2ⁿ sub-networks — neither of which is obvious from standard documentation.

## Core Concept
Regularization modifies the training procedure to reduce generalization error (test error) without reducing the model's representation capacity. The book frames this as a bias-variance tradeoff: adding constraints introduces bias but reduces variance, and the optimal tradeoff depends on the ratio of training set size to model complexity.

## Key Definitions
- **Effective capacity:** the subset of functions a model can represent that are actually reachable by the optimizer from a given initialization — regularization constrains this, not the architectural capacity
- **Weight decay (L2):** adds `Ω(θ) = (λ/2)‖w‖²` to the loss; the gradient contribution is `λw`, which shrinks weights toward zero each step
- **L1 regularization:** adds `Ω(θ) = λ‖w‖₁`; produces **sparse** solutions because the gradient `λ·sign(w)` is constant regardless of weight magnitude — weights are pushed to exactly zero if small enough
- **Dropout:** each unit is retained with probability p during training; at test time, multiply weights by p (or use inverted dropout: divide by p during training)
- **Dataset augmentation:** creating virtual training examples by applying label-preserving transforms; the book argues this is the most effective regularizer when applicable

## Deep Dive

### Early stopping ≡ L2 regularization (§7.8 — the key theorem)
The book proves that for a quadratic loss (linear model) with gradient descent:

> *"Early stopping is equivalent to L2 regularization, with the regularization strength inversely proportional to the number of training steps."*

If τ is the number of steps, η the learning rate, and the loss is locally quadratic, then early stopping recovers the same solution as L2 with `λ ≈ 1/(τη)`. This is why early stopping works as a regularizer even though it adds no explicit penalty term.

Practical implication: **if you use L2 weight decay, you already have early stopping as a redundant safeguard** — adding both is not additive regularization.

### Dropout as ensemble training (§7.12)
With n binary masks (each unit on/off), there are 2ⁿ possible sub-networks. Dropout trains all of them with **shared weights** — each step trains a randomly sampled sub-network. At test time, the full network with scaled weights approximates the **geometric mean** of all sub-network predictions.

This is why dropout outperforms naive ensembles: the weight sharing forces each sub-network to work independently (can't co-adapt features), while still using all the parameters.

```python
# Inverted dropout — scales during training, not at test time
# This is what PyTorch nn.Dropout does internally
def dropout_forward(x, p_drop, training):
    if not training:
        return x
    mask = (np.random.rand(*x.shape) > p_drop) / (1 - p_drop)  # inverted scaling
    return x * mask

# The /( 1 - p_drop) means: no weight scaling needed at test time
# If p_drop=0.5 and a unit survives, its output is doubled → expected value preserved
```

### L1 vs L2 — why L1 produces sparsity (§7.1.2)
The gradient of L1 is `λ·sign(w)`, constant for any |w| > 0. The gradient of L2 is `λw`, proportional to the weight magnitude. For a small weight `w = 0.001`:
- L2 gradient: `λ × 0.001` — tiny push, weight stays near zero
- L1 gradient: `λ × 1.0` — full-strength push, weight driven to exactly zero

This is why L1 is used for feature selection: it produces models where most weights are exactly zero.

### The manifold hypothesis and why it matters for regularization (§7.4)
The book frames generalization through the **manifold hypothesis**: natural data (images, text) concentrates near a low-dimensional manifold in the high-dimensional input space. Regularizers that align with this manifold — e.g., data augmentation that stays on the manifold — are far more effective than generic weight penalties.

## Code Examples

### L1 regularization (not natively in PyTorch optimizers — must add manually)
```python
def l1_regularized_loss(model, base_loss, lambda_l1):
    """
    PyTorch's weight_decay is L2 only. L1 must be added to the loss manually.
    """
    l1_penalty = sum(p.abs().sum() for p in model.parameters())
    return base_loss + lambda_l1 * l1_penalty

# Training loop
for x, y in dataloader:
    optimizer.zero_grad()
    loss = criterion(model(x), y)
    loss = l1_regularized_loss(model, loss, lambda_l1=1e-5)
    loss.backward()
    optimizer.step()
```

### Demonstrating dropout's ensemble interpretation
```python
import torch
import torch.nn as nn

class MCDropout(nn.Module):
    """
    Monte Carlo Dropout: run forward pass T times to approximate the ensemble.
    Useful at test time to get prediction uncertainty.
    Keeps dropout active during inference (model.train() mode).
    """
    def __init__(self, base_model, T=50):
        super().__init__()
        self.model = base_model
        self.T = T

    def forward(self, x):
        self.model.train()  # keep dropout active
        preds = torch.stack([self.model(x) for _ in range(self.T)])
        mean = preds.mean(0)
        uncertainty = preds.var(0)  # epistemic uncertainty from the ensemble
        return mean, uncertainty
```

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Using Adam + L2 weight_decay | Adam adapts the learning rate per-parameter, which undoes the intended L2 shrinkage (§8.5.3 implication) | Use AdamW (decoupled weight decay) |
| Applying dropout before batch norm | BN statistics are computed over the full (non-dropped) batch; dropout before BN introduces noise into the mean/variance estimates | Apply: Conv → BN → activation → Dropout |
| Treating L2 and early stopping as independent | They are equivalent (§7.8) — using both over-regularizes relative to expectation | Choose one, or carefully tune their combined effect |
| High dropout rate on small datasets | With few samples, the ensemble diversity is low; high dropout just throws away too much signal | Use p=0.1–0.2 for small datasets; 0.5 only for large overfit models |

## Connections
- **backprop.md** — L2 gradient: `dW += λW`; dropout backward is the same mask applied to `dout`
- **optimization.md** — AdamW is the required pairing for L2 weight decay with adaptive optimizers
