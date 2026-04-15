# Sequence Models (RNN, LSTM, GRU)
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a
**Read more:** https://www.deeplearningbook.org/contents/rnn.html — Chapter 10: Sequence Modeling: Recurrent and Recursive Nets

## What this book adds
The book derives the **vanishing gradient problem from first principles** — showing it is an inevitable consequence of the Jacobian spectral radius, not a training artifact. It then explains LSTM gating as a solution that creates **additive gradient paths** through time, analogous to ResNet's skip connections through depth. The book also covers **teacher forcing** as a training/inference mismatch that has no clean solution — a nuance often omitted in tutorials.

## Core Concept
An RNN parameterizes a family of functions over sequences by sharing the same transition function across all time steps: `hₜ = f(hₜ₋₁, xₜ; θ)`. The key challenge is that gradients must flow through arbitrarily long sequences — the same Jacobian `∂hₜ/∂hₜ₋₁` is multiplied at every step, leading to exponential growth or decay.

## Key Definitions
- **Vanishing gradient:** `‖∂hₜ/∂h₀‖ → 0` exponentially when the spectral radius of the recurrent weight matrix `ρ(Wₕₕ) < 1`
- **Exploding gradient:** `‖∂hₜ/∂h₀‖ → ∞` exponentially when `ρ(Wₕₕ) > 1`
- **BPTT (Backpropagation Through Time):** backprop on the unrolled RNN graph; memory cost is O(T) for T time steps
- **Truncated BPTT:** limit the unroll to k steps; trades gradient accuracy for memory; introduces a bias toward recent context
- **Teacher forcing:** use ground-truth output `yₜ₋₁` as input `xₜ` during training instead of the model's own prediction; speeds up training but creates train/test mismatch
- **Exposure bias:** the distributional shift caused by teacher forcing; at test time, the model sees its own (imperfect) outputs, not ground-truth

## Deep Dive

### The vanishing gradient — the formal derivation (§10.7)
BPTT computes:
```
∂L/∂h₀ = Σₜ (∂Lₜ/∂hₜ) · Π_{k=1}^{t} (∂hₖ/∂hₖ₋₁)
```

Each Jacobian `∂hₖ/∂hₖ₋₁ = diag(σ'(hₖ)) · Wₕₕ`. The product of T such matrices has eigenvalues that grow as `ρᵀ` where `ρ` is the spectral radius. For tanh, `max(σ') = 0.25`, so the contribution of gradients from step 0 decays as `(0.25 · ‖Wₕₕ‖)ᵀ`.

The book makes the important observation: **this is not a problem that can be fixed by better initialization alone**. The product of Jacobians either explodes or vanishes — the only solution is architectural (LSTM, GRU) or algorithmic (gradient clipping for explosion).

### LSTM: additive gradient path (§10.10)
The LSTM cell state update is additive:
```
cₜ = f ⊙ cₜ₋₁ + i ⊙ g̃
```
where f (forget gate) ∈ (0,1) and i (input gate) ∈ (0,1) are learned. The gradient through cₜ₋₁ is `∂cₜ/∂cₜ₋₁ = f` — the forget gate value, not a full Jacobian multiplication. When `f ≈ 1`, the gradient flows through the cell state nearly unchanged over many steps.

This is directly analogous to ResNets: instead of `h = F(h_prev) * W`, use `h = h_prev + F(h_prev)` — the additive path creates a gradient highway.

```python
class LSTMCell(torch.nn.Module):
    """LSTM cell from scratch — shows the additive gradient path explicitly"""
    def __init__(self, input_size, hidden_size):
        super().__init__()
        # All four gates in one matrix multiplication for efficiency
        self.W = nn.Linear(input_size + hidden_size, 4 * hidden_size)

    def forward(self, x, state):
        h_prev, c_prev = state
        combined = torch.cat([x, h_prev], dim=-1)
        gates = self.W(combined)

        # Split into 4 gates
        i, f, g, o = gates.chunk(4, dim=-1)
        i = torch.sigmoid(i)   # input gate
        f = torch.sigmoid(f)   # forget gate — controls gradient flow through c
        g = torch.tanh(g)      # cell gate (candidate)
        o = torch.sigmoid(o)   # output gate

        # Additive update — this is the gradient highway
        c = f * c_prev + i * g  # gradient w.r.t. c_prev = f (not a Jacobian product)
        h = o * torch.tanh(c)
        return h, (h, c)
```

### Teacher forcing and exposure bias (§10.2.1)
During training with teacher forcing:
- Input at step t: `xₜ = y*ₜ₋₁` (ground-truth token)

During inference:
- Input at step t: `xₜ = argmax p(yₜ₋₁)` (model's own prediction)

If the model makes an error at step 3, at step 4 it receives a wrong input it has never seen during training. The error compounds — this is exposure bias. The book outlines **scheduled sampling** as a mitigation: with probability p (annealed from 0 to 1), feed the model's own prediction during training. This is a heuristic, not a theoretically clean solution.

### Bidirectional RNNs and their limitations (§10.3)
A bidirectional RNN runs one RNN forward and one backward, concatenating states: `hₜ = [h→ₜ ; h←ₜ]`. This provides full context at every step but **cannot be used for online/streaming inference** — the backward pass requires the full sequence. The book notes this makes bidirectional RNNs suitable for offline tasks (classification, NER, translation with encoder) but not autoregressive generation.

## Code Examples

### Truncated BPTT with detached state
```python
def train_rnn_truncated_bptt(model, data, k=35, optimizer=None):
    """
    Truncated BPTT: detach hidden state every k steps.
    This truncates gradients at step boundaries — a deliberate approximation
    that limits memory to O(k) instead of O(T).
    Book §10.2.2: the gradient bias introduced grows with the sequence's
    long-range dependencies, not with T.
    """
    h = model.init_hidden()
    total_loss = 0

    for i in range(0, len(data) - 1, k):
        chunk = data[i : i + k]
        h = h.detach()  # CRITICAL: detach from previous graph segment

        loss = 0
        for t in range(len(chunk) - 1):
            output, h = model(chunk[t], h)
            loss += criterion(output, chunk[t + 1])

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        total_loss += loss.item()

    return total_loss
```

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Not detaching hidden state between BPTT chunks | Gradients propagate through all previous chunks — memory grows as O(T) | `h = h.detach()` at the start of each chunk |
| Expecting LSTM to learn very long-range deps | Even LSTM vanishes over 100s of steps when forget gate is not near 1 | Use Transformer attention, or explicitly train the forget gate near 1 with initialization |
| Teacher forcing with no scheduled sampling | Exposure bias causes inference degradation, especially for long sequences | Anneal teacher forcing probability; use beam search at inference |
| Gradient clipping by value | Changes direction, introduces bias (§8.2.4) | Clip by norm: `clip_grad_norm_(params, 1.0)` |

## Connections
- **backprop.md** — BPTT is backprop on an unrolled graph; same Algorithm 6.4, same accumulation rules
- **optimization.md** — gradient clipping (§8.2.4) is especially critical here; discuss in context of BPTT Jacobian products
- **convolutional_networks.md** — TCN/WaveNet (dilated 1D conv) often outperforms LSTM on long sequences by avoiding the sequential bottleneck
