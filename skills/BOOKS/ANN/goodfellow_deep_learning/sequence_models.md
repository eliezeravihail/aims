# Sequence Models
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a

## Core Concept
RNNs process sequences by maintaining a hidden state hₜ = f(hₜ₋₁, xₜ). Vanishing gradients through long sequences are the core limitation; LSTM and GRU solve this with gating mechanisms that create additive gradient paths.

## Key Definitions
- **RNN:** hₜ = tanh(Wₕhₜ₋₁ + Wₓxₜ + b); gradient decays as ∂hₜ/∂h₀ = Π∂hₜ/∂hₜ₋₁
- **LSTM:** 3 gates (input, forget, output) + cell state cₜ; additive update to cₜ preserves gradient
- **GRU:** 2 gates (reset, update); simpler than LSTM, similar performance
- **BPTT (Backprop Through Time):** unrolled RNN treated as a very deep network; truncated BPTT limits the unroll depth
- **Teacher forcing:** use ground-truth yₜ₋₁ as input at step t during training (faster convergence, exposure bias tradeoff)

## Pattern

```python
import torch.nn as nn

# LSTM sequence encoder
class LSTMEncoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers,
                            batch_first=True, dropout=0.3)

    def forward(self, x):
        # x: (batch, seq_len)
        emb = self.embed(x)                      # (batch, seq, embed_dim)
        out, (h_n, c_n) = self.lstm(emb)         # out: (batch, seq, hidden)
        return out, h_n[-1]                       # last layer hidden state

# GRU is identical but returns (out, h_n) — no cell state
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Vanishing gradient in plain RNN | Use LSTM or GRU; add gradient clipping |
| Exploding gradients during BPTT | `clip_grad_norm_(params, max_norm=1.0)` |
| Exposure bias at inference | Scheduled sampling or switch to Transformer |
| Forgetting to pack padded sequences | Use `pack_padded_sequence` for variable-length inputs |

## Connections
- **backprop.md** — BPTT is standard backprop on the unrolled graph
- **optimization.md** — gradient clipping is critical before optimizer step
- **convolutional_networks.md** — 1D CNNs / TCNs often outperform RNNs on long sequences
