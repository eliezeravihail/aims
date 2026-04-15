# Backpropagation
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a

## Core Concept
Backprop computes ∂L/∂θ for every parameter via the chain rule in a single backward pass through the computational graph. It reuses forward-pass activations stored in memory, making it O(n) in the number of operations — the same cost as the forward pass.

## Key Definitions
- **vjp (vector-Jacobian product):** reverse-mode AD primitive; cheaper than full Jacobian when outputs ≪ parameters
- **Computational graph:** DAG of operations; backprop traverses it in reverse topological order
- **Vanishing gradient:** |∂L/∂h| → 0 through many layers when |σ′| < 1 repeatedly (sigmoid, tanh)
- **Exploding gradient:** gradient norm grows exponentially; clipping is the standard fix

## Algorithm

```python
# Linear layer backward (numpy)
# Forward: y = x @ W.T + b
def linear_backward(dout, cache):
    x, W = cache
    dx = dout @ W           # (batch, in_dim)
    dW = dout.T @ x         # (out_dim, in_dim)
    db = dout.sum(axis=0)   # (out_dim,)
    return dx, dW, db

# ReLU backward
def relu_backward(dout, cache):
    x = cache
    return dout * (x > 0)
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Forgetting to zero gradients | Call `optimizer.zero_grad()` before each step |
| In-place ops breaking autograd | Avoid `x += …` on tensors that require grad |
| Sigmoid saturation kills gradients | Switch to ReLU or use residual connections |
| Numerical check mismatch | Use `torch.autograd.gradcheck` with float64 |

## Connections
- **optimization.md** — gradients feed directly into SGD/Adam update rules
- **regularization.md** — L2 adds `λW` to `dW`; dropout zeroes activations before backward
- **convolutional_networks.md** — same algorithm; conv Jacobians are sparse and weight-shared
