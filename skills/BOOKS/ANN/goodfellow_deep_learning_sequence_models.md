---
source: goodfellow_deep_learning
topic: sequence_models
title: "Deep Learning — Sequence Models"
authors: Goodfellow, Bengio, Courville
quality_score: 0.82
---

# Sequence Models (RNNs, LSTMs, GRUs)

## Key Definitions

| Term | Definition |
|------|-----------|
| **RNN** | Recurrent Neural Network: shares parameters across time; processes variable-length sequences by maintaining a hidden state h_t = f(h_{t-1}, x_t). |
| **BPTT** | Backpropagation Through Time: unrolls the RNN computational graph over T steps and applies standard backprop; gradient has O(T) multiplicative factors. |
| **Truncated BPTT** | Limits the unrolling window to k steps to bound memory and computation; hidden state still carries forward, but gradients are cut off. |
| **LSTM** | Long Short-Term Memory: gates (input, forget, output) control information flow into/out of a cell state c_t, mitigating vanishing gradients over long sequences. |
| **GRU** | Gated Recurrent Unit: simplified LSTM with reset and update gates; fewer parameters, often similar performance. |
| **Vanishing gradient (BPTT)** | Product of Jacobians over T steps → 0 if spectral radius < 1; gradient signal from distant timesteps disappears. |
| **Exploding gradient (BPTT)** | Product of Jacobians → ∞ if spectral radius > 1; fixed by gradient clipping. |
| **Bidirectional RNN** | Runs two RNNs (forward + backward); output is the concatenation of both; cannot be used autoregressively. |
| **Encoder–Decoder** | Encoder RNN compresses a sequence to a context vector; decoder RNN generates the output sequence conditioned on it (seq2seq). |
| **Teacher forcing** | During training, feed the ground-truth token at step t as input to step t+1, rather than the model's own prediction; speeds convergence but introduces exposure bias. |

## Core Equations

**Vanilla RNN:**
```
h_t = tanh(W_hh h_{t-1} + W_xh x_t + b_h)
y_t = W_hy h_t + b_y
```

**LSTM:**
```
f_t = σ(W_f [h_{t-1}, x_t] + b_f)   # forget gate
i_t = σ(W_i [h_{t-1}, x_t] + b_i)   # input gate
g_t = tanh(W_g [h_{t-1}, x_t] + b_g) # candidate cell
o_t = σ(W_o [h_{t-1}, x_t] + b_o)   # output gate
c_t = f_t ⊙ c_{t-1} + i_t ⊙ g_t    # cell state update (linear! → long-range gradient highway)
h_t = o_t ⊙ tanh(c_t)
```

**GRU:**
```
z_t = σ(W_z [h_{t-1}, x_t])          # update gate
r_t = σ(W_r [h_{t-1}, x_t])          # reset gate
ñ_t = tanh(W_n [r_t ⊙ h_{t-1}, x_t])
h_t = (1 − z_t) ⊙ h_{t-1} + z_t ⊙ ñ_t
```

**BPTT gradient (simplified for single-layer vanilla RNN):**
```
∂L/∂W_hh = Σ_t Σ_{k≤t} (∂L/∂h_t) · (∏_{j=k+1}^{t} diag(tanh'(·)) W_hh) · h_{k-1}ᵀ
```
The product of T Jacobians causes vanishing/exploding; LSTM's additive c_t update replaces multiplicative chain.

## Code Example (PyTorch)

```python
import torch
import torch.nn as nn

class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers, num_classes, drop_p=0.3):
        super().__init__()
        self.embed  = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm   = nn.LSTM(
            embed_dim, hidden_dim, num_layers=num_layers,
            batch_first=True, dropout=drop_p if num_layers > 1 else 0,
            bidirectional=False,
        )
        self.drop   = nn.Dropout(drop_p)
        self.head   = nn.Linear(hidden_dim, num_classes)

    def forward(self, x, lengths):
        # x: (B, T) token ids; lengths: (B,) actual sequence lengths
        emb = self.drop(self.embed(x))                          # (B, T, E)
        packed = nn.utils.rnn.pack_padded_sequence(
            emb, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, (h_n, _) = self.lstm(packed)                         # h_n: (layers, B, H)
        return self.head(self.drop(h_n[-1]))                    # last layer hidden state


# Training step
model = LSTMClassifier(10000, 128, 256, 2, 2)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.CrossEntropyLoss()

def train_step(x, lengths, y):
    optimizer.zero_grad()
    logits = model(x, lengths)
    loss = criterion(logits, y)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)   # CRITICAL for RNNs
    optimizer.step()
    return loss.item()


# Truncated BPTT for language modelling
def train_lm_tbptt(model, data, seq_len=35, optimizer=None):
    h = None
    for i in range(0, data.size(1) - 1, seq_len):
        x = data[:, i : i + seq_len]
        y = data[:, i + 1 : i + seq_len + 1]
        if h is not None:
            h = tuple(s.detach() for s in h)        # detach: stop gradient at window boundary
        optimizer.zero_grad()
        out, h = model(x, h)
        loss = criterion(out.reshape(-1, out.size(-1)), y.reshape(-1))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 0.25)
        optimizer.step()
```

## Initialisation Tips

| Parameter | Recommended init | Reason |
|-----------|-----------------|--------|
| Forget gate bias `b_f` | +1 (ones) | Starts with "remember everything", easing gradient flow early in training |
| Hidden-to-hidden `W_hh` | Orthogonal | Preserves gradient norm over time; use `nn.init.orthogonal_` |
| Embedding | Uniform ±0.1 or pretrained | Random init fine for small vocab |

```python
for name, p in model.lstm.named_parameters():
    if "weight_hh" in name:
        nn.init.orthogonal_(p)
    elif "bias" in name:
        # Set forget gate bias to 1 (second quarter of bias vector for LSTM)
        n = p.size(0)
        p.data[n // 4 : n // 2].fill_(1.0)
```

## Common Pitfalls

1. **Forgetting to clip gradients** — without `clip_grad_norm_`, LSTM/RNN training routinely diverges due to exploding gradients; use `max_norm=1.0–5.0`.
2. **Not packing padded sequences** — passing zero-padded inputs without `pack_padded_sequence` leaks padding tokens into the hidden state; use packed sequences or mask the loss.
3. **Hidden state not detached in TBPTT** — forgetting `.detach()` on `h` causes the computational graph to grow unboundedly, causing OOM.
4. **Teacher forcing rate not annealed** — pure teacher forcing causes exposure bias; in generation tasks, schedule mixing (scheduled sampling) helps.
5. **Using vanilla RNN for sequences > ~20 steps** — vanishing gradients make learning long-range dependencies effectively impossible; always use LSTM or GRU.
6. **Bidirectional RNN for autoregressive decoding** — bidirectional models see the future; do not use them as decoders in seq2seq / language modelling.
7. **Wrong hidden state shape** — `nn.LSTM` returns `(output, (h_n, c_n))`; `h_n` shape is `(num_layers * num_directions, batch, hidden_size)`. Index `[-1]` or concatenate `[0]` and `[1]` for bidirectional.

## Connections to Other Topics (this book)

- **Backprop (Ch. 6)** — BPTT is exactly backprop on an unrolled computation graph; the same chain-rule equations apply, but depth equals sequence length T.
- **Regularization (Ch. 7)** — variational (per-sequence) dropout and zoneout are RNN-specific regularisers; recurrent dropout (on h-to-h connections) outperforms naive per-step dropout.
- **Optimization (Ch. 8)** — gradient clipping is a first-class concern; Adam with lr=1e-3 and clipping is the standard recipe; orthogonal initialisation makes SGD viable.
- **Convolutional Networks (Ch. 9)** — temporal CNNs (TCNs, dilated causal convs) are a parallelisable alternative to RNNs for many sequence tasks; transformers have largely superseded both for NLP.
