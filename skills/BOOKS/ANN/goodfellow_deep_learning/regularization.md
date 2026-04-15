# Regularization
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a

## Core Concept
Regularization reduces the gap between training and test error by constraining model capacity or adding noise. It addresses overfitting without reducing model size.

## Key Definitions
- **L2 (weight decay):** adds λ‖W‖² to the loss; shrinks weights toward zero each step
- **L1:** adds λ‖W‖₁; promotes sparsity — some weights become exactly zero
- **Dropout:** during training, randomly zero each unit with probability p; at test time, scale by (1−p)
- **Batch Normalization:** normalizes layer inputs per mini-batch; reduces internal covariate shift and acts as implicit regularizer
- **Early stopping:** halt training when validation loss stops improving; equivalent to L2 regularization under certain conditions

## Patterns

```python
# L2 via optimizer weight_decay (PyTorch)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)

# Dropout layer (applied during training only)
class MLP(nn.Module):
    def __init__(self):
        self.fc1 = nn.Linear(784, 256)
        self.drop = nn.Dropout(p=0.5)
        self.fc2 = nn.Linear(256, 10)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.drop(x)          # zeroed during train, scaled at eval
        return self.fc2(x)

# Always call model.eval() at inference — disables dropout + uses running BN stats
model.eval()
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Forgetting `model.eval()` at inference | Dropout stays active → stochastic predictions |
| Applying dropout before BN | Apply dropout after activation, BN before activation |
| Too-high dropout rate on small datasets | Start with p=0.2; 0.5 is for large overfit models |
| L2 + Adam double-regularization | Use AdamW (decoupled weight decay) instead of Adam + L2 |

## Connections
- **backprop.md** — L2 gradient contribution: `dW += λW`
- **optimization.md** — AdamW is the correct pairing for weight decay with adaptive optimizers
