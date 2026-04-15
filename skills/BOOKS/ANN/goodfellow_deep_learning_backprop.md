---
source: goodfellow_deep_learning
topic: backprop
title: "Deep Learning — Backpropagation"
authors: Goodfellow, Bengio, Courville
quality_score: 0.82
---

# Backpropagation

## Key Definitions

| Term | Definition |
|------|-----------|
| **Computational graph** | DAG where nodes are variables/operations; edges denote data flow. Backprop traverses it in reverse topological order. |
| **Forward pass** | Evaluates every node left-to-right, caching intermediate values needed for the backward pass. |
| **Backward pass** | Propagates gradients from loss L back to parameters using the chain rule. |
| **Jacobian** | Matrix of all first-order partial derivatives ∂y_i/∂x_j; backprop avoids materialising it by computing Jacobian-vector products. |
| **vjp (vector-Jacobian product)** | Core primitive: given upstream gradient v, compute v^T J cheaply. All modern AD frameworks (PyTorch, JAX) implement this. |
| **Vanishing / exploding gradient** | Gradients shrink or blow up exponentially with depth (§8.2.5). Mitigated by residuals, normalisation, careful initialisation. |

## Core Algorithm

```
# Pseudocode: reverse-mode automatic differentiation on a DAG
def backward(node, upstream_grad):
    for op, parent in reversed(node.computation_history):
        local_grad = op.local_gradient(parent.value)   # ∂output/∂input
        parent.grad += upstream_grad * local_grad       # chain rule
        backward(parent, parent.grad)                   # recurse
```

**Chain rule (scalar):**
```
∂L/∂x = (∂L/∂y) · (∂y/∂x)
```

**General (vector):**
```
∂L/∂x_i = Σ_j (∂L/∂y_j) · (∂y_j/∂x_i)
```

For a two-layer net with sigmoid σ:
```
δ² = ∂L/∂z²           (output layer delta)
δ¹ = (W²)ᵀ δ² ⊙ σ'(z¹)   (hidden layer delta, ⊙ = elementwise)
∂L/∂W¹ = δ¹ (a⁰)ᵀ
∂L/∂b¹ = δ¹
```

## Code Example (PyTorch)

```python
import torch
import torch.nn as nn

# Manual backprop inspection via hooks
class TwoLayerNet(nn.Module):
    def __init__(self, d_in, d_h, d_out):
        super().__init__()
        self.fc1 = nn.Linear(d_in, d_h)
        self.fc2 = nn.Linear(d_h, d_out)

    def forward(self, x):
        self.h = torch.relu(self.fc1(x))   # cache activation
        return self.fc2(self.h)

model = TwoLayerNet(784, 256, 10)
x = torch.randn(32, 784)
y = torch.randint(0, 10, (32,))

logits = model(x)
loss = nn.CrossEntropyLoss()(logits, y)
loss.backward()                            # fills .grad on all leaf tensors

# Inspect gradient norms per layer
for name, p in model.named_parameters():
    print(f"{name}: grad_norm={p.grad.norm().item():.4f}")

# Gradient clipping (prevents exploding gradients)
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

## Common Pitfalls

1. **Forgetting `zero_grad()`** — gradients accumulate across batches by default in PyTorch; call `optimizer.zero_grad()` before each `loss.backward()`.
2. **In-place operations on leaf tensors** — breaks the computation graph; use `x = x + delta` not `x += delta`.
3. **Detaching when you shouldn't** — calling `.detach()` or `.numpy()` inside the forward pass cuts gradient flow silently.
4. **Numerical gradient checks** — always verify custom ops with `torch.autograd.gradcheck`; use double precision for the check.
5. **Vanishing gradients with deep sigmoid/tanh** — switch to ReLU or use highway/residual connections.
6. **Second-order effects ignored** — standard backprop computes first-order gradients only; using the gradient as a "loss" to differentiate again is valid but expensive.

## Connections to Other Topics (this book)

- **Optimization (Ch. 8)** — gradient descent directly consumes the output of backprop; gradient noise and curvature both affect convergence.
- **Regularization (Ch. 7)** — L2 weight decay adds `λw` to every parameter gradient; dropout masks the backward pass.
- **Convolutional Networks (Ch. 9)** — backprop through conv layers becomes cross-correlation of the upstream gradient with the filter (transposed conv in the backward).
- **Sequence Models (Ch. 10)** — BPTT (backprop through time) unrolls the RNN computational graph; same algorithm, but gradient paths are O(T) long, intensifying vanishing/exploding issues.
