# Convolutional Networks
**Source:** Deep Learning — Goodfellow, Bengio, Courville (deeplearningbook.org) | tier_1a

## Core Concept
CNNs exploit three properties: **sparse interactions** (small kernels), **parameter sharing** (one kernel slides across all positions), and **equivariant representations** (translation equivariance). This makes them dramatically more efficient than fully-connected layers on grid-structured data.

## Key Definitions
- **Convolution:** (I * K)[i,j] = Σₘ Σₙ I[i+m, j+n] · K[m,n]
- **Receptive field:** input region affecting one output unit; grows with depth
- **Pooling:** down-samples spatial dimensions; max-pool preserves dominant activations
- **Stride:** step size of the sliding kernel; stride 2 halves spatial resolution
- **Padding:** `same` preserves spatial size; `valid` shrinks it
- **Feature map:** output of one filter applied across all positions

## Architecture Pattern

```python
import torch.nn as nn

class ConvBlock(nn.Module):
    """Standard conv → BN → ReLU block"""
    def __init__(self, in_ch, out_ch, kernel=3, stride=1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel, stride=stride, padding=kernel//2, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.block(x)

# Output size formula: floor((W - K + 2P) / S) + 1
# W=input, K=kernel, P=padding, S=stride
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Using bias with BatchNorm | Set `bias=False` — BN's β already provides the offset |
| Spatial size mismatch in skip connections | Match with 1×1 conv or adaptive pooling |
| Checkerboard artifacts in upsampling | Use bilinear upsample + conv instead of transposed conv |
| Forgetting to account for receptive field size | Use dilated convs for larger context without extra params |

## Connections
- **backprop.md** — conv backward is a transposed convolution; weight gradients summed over positions
- **sequence_models.md** — 1D CNNs are a fast alternative to RNNs for sequential data
