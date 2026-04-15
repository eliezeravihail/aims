# Convolutional Networks
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a
**Read more:** https://www.deeplearningbook.org/contents/convnets.html — Chapter 9: Convolutional Networks

## What this book adds
The book formally defines convolution in the context of neural networks as **cross-correlation** (not true convolution), and explains why this distinction is irrelevant in practice — learned kernels absorb the flip. More importantly, it provides the theoretical justification for the three structural properties that make CNNs efficient: **sparse interactions**, **parameter sharing**, and **equivariant representations** — and shows how each reduces the parameter count and inductive bias relative to fully-connected networks.

## Core Concept
A convolutional layer replaces the dense weight matrix W ∈ ℝ^(m×n) of a fully-connected layer with a sparse weight tensor (kernel) that is reused at every spatial location. This reduces parameters from O(m·n) to O(k²·c_in·c_out) where k is the kernel size, while building in translation equivariance as a hard constraint.

## Key Definitions
- **Cross-correlation (what PyTorch calls "convolution"):** `(I * K)[i,j] = Σₘ Σₙ I[i+m, j+n] · K[m,n]` — kernel slides without flipping
- **True convolution:** same but K is flipped; learned kernels absorb the difference
- **Sparse interactions:** each output unit connects to only k² input units (not all n)
- **Parameter sharing:** the same kernel K is used at every position — one set of weights detects the same feature everywhere
- **Equivariance:** if the input shifts by (Δx, Δy), the output shifts by the same amount — formally: `f(T(x)) = T(f(x))` where T is a translation
- **Invariance (pooling):** output is unchanged by small input shifts — a different and stronger property than equivariance
- **Receptive field:** grows linearly with depth for stride-1 convs; grows exponentially with dilated convs

## Deep Dive

### The efficiency argument — comparing FC to conv (§9.2)
For a 256×256 image with 3 channels, a single FC layer to 1000 units needs 256×256×3×1000 ≈ 196M parameters. A 3×3 conv to 64 filters needs 3×3×3×64 = 1,728 parameters — a 100,000× reduction — while detecting local patterns at every position simultaneously.

This is not just a practical engineering trick; the book argues it is a **prior**: translation equivariance is almost always the correct inductive bias for natural images and signals.

### Strided convolution vs pooling — the tradeoff (§9.4)
Max pooling provides **invariance** (outputs don't change for small input shifts) and **dimensionality reduction**. Strided convolution provides **equivariance** (output shifts when input shifts) with dimensionality reduction.

The book notes the practical difference: max pooling is better when the task requires detecting *presence* of a feature regardless of exact location; strided conv is better when *position* matters. Modern architectures (ResNet, EfficientNet) increasingly prefer strided conv over pooling.

### Dilated (atrous) convolution — exponential receptive field growth
Standard conv: receptive field grows as O(depth × kernel_size).
Dilated conv with rate d: inserts (d−1) zeros between kernel elements.

With rates [1, 2, 4, 8, 16], a stack of 5 3×3 convs achieves a receptive field of (1 + 2×(3−1)×(1+2+4+8+16)) = 1 + 2×2×31 = 125, vs 11 for standard convs — without increasing parameters or losing resolution.

```python
import torch.nn as nn

# WaveNet-style dilated causal convolutions
class DilatedStack(nn.Module):
    def __init__(self, channels, kernel=3, num_layers=8):
        super().__init__()
        self.convs = nn.ModuleList([
            nn.Conv1d(channels, channels, kernel,
                      padding=(2**i) * (kernel-1),  # causal padding
                      dilation=2**i)
            for i in range(num_layers)
        ])
        # Receptive field = 1 + 2*(kernel-1)*(2^num_layers - 1)

    def forward(self, x):
        for conv in self.convs:
            residual = x
            x = conv(x)[..., :x.shape[-1]]  # trim causal padding
            x = x + residual
        return x
```

### Transposed convolution — the book's precise definition
The transposed conv is not "deconvolution" (the book explicitly rejects this name). It is the **gradient** of a forward conv — the same operation that appears in the backward pass. For a stride-s conv, the transposed conv increases spatial resolution by factor s by inserting (s−1) zeros between input elements.

```python
# What nn.ConvTranspose2d actually computes:
# If forward conv maps (H, W) → (H/s, W/s) with kernel k, stride s
# Transposed maps (H/s, W/s) → (H, W) — inserts zeros, then convolves

# Checkerboard artifacts happen when kernel_size is not divisible by stride
# Fix: upsample (bilinear) + regular conv — avoids the artifact entirely
def upsample_conv(in_ch, out_ch, scale=2):
    return nn.Sequential(
        nn.Upsample(scale_factor=scale, mode='bilinear', align_corners=False),
        nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1)
    )
```

## Code Examples

### Visualizing receptive field growth
```python
def receptive_field(num_layers, kernel_size, stride=1, dilation=1):
    """
    Compute the receptive field of a stacked conv network.
    Book §9.3: RF grows linearly with depth for standard convs.
    """
    rf = 1
    total_stride = 1
    for _ in range(num_layers):
        effective_kernel = dilation * (kernel_size - 1) + 1
        rf += (effective_kernel - 1) * total_stride
        total_stride *= stride
    return rf

# Standard 3×3, depth 10: RF = 21
# Dilated [1,2,4,8,16,32,64,128] + 3×3: RF = 511 — the WaveNet design choice
```

### Implementing parameter sharing explicitly (pedagogical)
```python
import torch, torch.nn.functional as F

def shared_weight_conv(x, kernel):
    """
    Demonstrates that conv is exactly parameter sharing:
    the same kernel is applied at every spatial position.
    This is what nn.Conv2d does internally.
    """
    B, C_in, H, W = x.shape
    C_out, C_in, kH, kW = kernel.shape
    # unfold extracts all patches, then a single matmul applies the shared kernel
    patches = x.unfold(2, kH, 1).unfold(3, kW, 1)  # (B, C_in, H', W', kH, kW)
    patches = patches.contiguous().view(B, C_in, -1, kH*kW)
    kernel_flat = kernel.view(C_out, -1)
    # same kernel_flat applied to every of the H'*W' patches
    out = torch.einsum('bclk,ok->bol', patches, kernel_flat)
    return out.view(B, C_out, H-kH+1, W-kW+1)
```

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Using `bias=True` with BatchNorm | BN's β parameter already provides a per-channel bias offset (§9.x) | Set `bias=False` in conv layers before BN |
| Checkerboard artifacts in transposed conv | Non-divisible kernel/stride creates uneven overlap in the backward conv (§9.4) | Use upsample + regular conv |
| Stacking many stride-1 convs without dilation | Receptive field grows too slowly for large inputs | Use dilated convs or periodic downsampling |

## Connections
- **backprop.md** — the backward pass of a conv layer is a transposed convolution; gradient w.r.t. kernel is a cross-correlation
- **sequence_models.md** — 1D CNNs (TCN, WaveNet) are a direct alternative to RNNs for sequence data; the dilated stack above is a TCN building block
