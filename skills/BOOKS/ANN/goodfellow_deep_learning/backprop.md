# Backpropagation
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a
**Read more:** https://www.deeplearningbook.org/contents/mlp.html — Chapter 6: Deep Feedforward Networks, §6.5 Back-Propagation and Other Differentiation Algorithms

## What this book adds
Goodfellow et al. present backprop as a **general algorithm on any DAG**, not just layered networks — the same algorithm computes gradients for recurrent networks, attention mechanisms, and arbitrary computational graphs. They formally distinguish **symbol-to-number differentiation** (Torch/TF eager) vs **symbol-to-symbol differentiation** (TF graph), and show that the memory cost of backprop is proportional to the number of operations, not the depth — a non-obvious result that explains why deep networks are feasible.

## Core Concept
Backprop applies the chain rule to a computational graph in reverse topological order. Each node computes its contribution to upstream gradients using only its local Jacobian and the gradient flowing into it — it does not need to know anything about the rest of the graph.

Formally: for loss L and any intermediate variable z with z = f(x, y),
```
∂L/∂x = Σ_j (∂L/∂z_j)(∂z_j/∂x)
```
Summed over all uses of x in the graph (the **multivariate chain rule** — easily missed when x feeds multiple paths).

## Key Definitions
- **Op node:** computes a function and stores the forward value; during backward, computes the **vjp** (vector-Jacobian product) with the upstream gradient
- **vjp:** given upstream gradient `g` and local Jacobian `J`, returns `gᵀJ` — this is the fundamental primitive of reverse-mode AD; it never materializes the full Jacobian
- **Reverse-mode AD (backprop):** optimal when |outputs| ≪ |inputs|; costs O(1) backward passes regardless of input dimension; this is why it dominates ML (1 loss, millions of params)
- **Forward-mode AD:** optimal when |inputs| ≪ |outputs|; used for Jacobian-vector products in second-order methods

## Deep Dive

### Why O(n) time — the key insight
The naive approach would compute a separate gradient for each parameter by running a forward pass for each. Backprop achieves O(n) by storing intermediate activations during the forward pass and reusing them. The book proves:

> *"The amount of computation required for the back-propagation algorithm is of the same order as the amount required for the forward pass"* (§6.5.2)

This works because every intermediate gradient ∂L/∂z is computed exactly once and used by all downstream consumers — analogous to dynamic programming.

### The general backprop algorithm (Algorithm 6.4 in the book)
```python
def backprop(graph, inputs, outputs, target_inputs):
    """
    graph: topologically sorted list of ops
    Computes gradient of outputs w.r.t. target_inputs.
    """
    # Forward pass: compute and cache all node values
    node_values = {}
    for op in graph:
        node_values[op] = op.forward(*[node_values[i] for i in op.inputs])

    # Backward pass: initialize output gradient = 1
    grads = {outputs: 1.0}
    for op in reversed(graph):
        upstream = grads[op]
        # Each op knows how to compute its own vjp
        for inp, g in zip(op.inputs, op.vjp(upstream, node_values)):
            grads[inp] = grads.get(inp, 0) + g  # sum over multiple uses

    return {t: grads[t] for t in target_inputs}
```

The critical line is `grads[inp] += g` — gradients from **all paths** through `inp` are accumulated. Forgetting this (i.e., overwriting instead of accumulating) is the source of subtle gradient bugs in custom autograd implementations.

### Symbol-to-symbol vs symbol-to-number (§6.5.6)
- **Symbol-to-number** (PyTorch eager, JAX): execute ops, then walk the recorded tape backward. No graph object exists at runtime.
- **Symbol-to-symbol** (TF graph, JAX `jit`): extend the symbolic graph with gradient nodes. Allows ahead-of-time optimization but requires the full graph in memory.

PyTorch's autograd is symbol-to-number; `torch.jit.trace` converts it to symbol-to-symbol. This distinction matters when debugging: in eager mode, Python exceptions propagate naturally; in graph mode, errors appear inside compiled ops.

### Gradient of a matrix operation — the Jacobian structure
For `Y = XW` (X: batch×in, W: in×out):
```
∂L/∂W = Xᵀ(∂L/∂Y)    shape: (in × out) — outer product summed over batch
∂L/∂X = (∂L/∂Y)Wᵀ    shape: (batch × in)
```
These shapes are non-obvious from the chain rule written in scalar form. The book derives them via the Frobenius inner product: ∂L/∂W = argmin_G ‖dL - tr(GᵀdW)‖.

## Code Examples

### Implementing vjp-based autograd from scratch (demonstrates Algorithm 6.4)
```python
import numpy as np

class Tensor:
    def __init__(self, data, _children=(), _op=''):
        self.data = np.array(data, dtype=float)
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)

    def __matmul__(self, other):
        out = Tensor(self.data @ other.data, (self, other), 'matmul')
        def _backward():
            # Accumulate (+=), never overwrite — handles diamond-shaped graphs
            self.grad  += out.grad @ other.data.T
            other.grad += self.data.T @ out.grad
        out._backward = _backward
        return out

    def relu(self):
        out = Tensor(np.maximum(0, self.data), (self,), 'relu')
        def _backward():
            self.grad += (out.data > 0) * out.grad
        out._backward = _backward
        return out

    def backward(self):
        topo = []
        visited = set()
        def build(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build(child)
                topo.append(v)
        build(self)
        self.grad = 1.0
        for node in reversed(topo):
            node._backward()
```

### Verifying a custom op with finite differences (book §6.5.10)
```python
def numerical_gradient(f, x, eps=1e-5):
    """Numerical gradient via central differences — use to verify analytical grad."""
    grad = np.zeros_like(x)
    it = np.nditer(x, flags=['multi_index'])
    while not it.finished:
        idx = it.multi_index
        orig = x[idx]
        x[idx] = orig + eps
        fp = f(x)
        x[idx] = orig - eps
        fm = f(x)
        grad[idx] = (fp - fm) / (2 * eps)
        x[idx] = orig
        it.iternext()
    return grad

# Usage: assert max absolute error < 1e-4 for float64
```

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Overwriting gradient instead of accumulating | A variable used in multiple paths requires summed gradients (§6.5.2) | Always `grad += ...` in custom backward implementations |
| Using float32 for gradient checks | Numerical precision loss makes the check unreliable | Use float64 for `gradcheck`; float32 for actual training |
| Assuming backprop cost ∝ depth | It is O(n) in ops, not depth — but memory cost IS proportional to stored activations | Use gradient checkpointing to trade memory for recomputation |

## Connections
- **optimization.md** — backprop outputs feed Adam/SGD; see also Hessian-free optimization (§8.9)
- **regularization.md** — L2 adds `λW` to `∂L/∂W`; dropout backward is a masked identity
- **sequence_models.md** — BPTT is backprop on the unrolled RNN graph; same algorithm, same memory-cost analysis
