---
source: goodfellow_deep_learning
topic: convolutional_networks
title: "Deep Learning — Convolutional Networks"
authors: Goodfellow, Bengio, Courville
quality_score: 0.82
---

# Convolutional Networks (CNNs)

## Key Definitions

| Term | Definition |
|------|-----------|
| **Convolution** | Linear operation: output s(t) = (x * w)(t) = Σ_a x(t−a)w(a). In ML, typically discrete and finite-dimensional; in practice implemented as cross-correlation (filter not flipped). |
| **Cross-correlation** | S(i,j) = Σ_m Σ_n I(i+m, j+n) K(m,n). PyTorch `nn.Conv2d` computes this, not true convolution. |
| **Kernel / filter** | Learned weight tensor of shape (C_out, C_in, kH, kW); each output channel has its own filter. |
| **Feature map** | Output activation volume for one kernel applied across the spatial extent of the input. |
| **Receptive field** | Region in the input space that affects a particular output unit; grows with depth and dilation. |
| **Pooling** | Reduces spatial resolution by summarising a neighbourhood (max, average). Provides approximate translation invariance. |
| **Stride** | Step size of the filter slide; stride=2 halves spatial dimensions without pooling. |
| **Padding** | Zeros added around the border; `same` padding keeps spatial size; `valid` shrinks it by (k−1). |
| **Depthwise separable conv** | Factorises standard conv into depthwise (per-channel spatial filtering) + pointwise (1×1 mixing); ≈8–9× cheaper in FLOPs (MobileNet). |
| **Dilation / atrous conv** | Inserts zeros between kernel taps; expands receptive field without increasing parameters or reducing resolution (DeepLab, WaveNet). |

## Spatial Dimension Formula

```
output_size = floor((input_size + 2*padding - dilation*(kernel_size-1) - 1) / stride + 1)
```

## Core Architecture Pattern

```
# Canonical ConvNet block
Input → [Conv → BN → ReLU] × N → Pool → ... → GlobalAvgPool → Linear → Softmax

# Residual block (ResNet §skip connections)
def residual_block(x, channels, stride=1):
    h = conv3x3(x, channels, stride) → BN → ReLU
    h = conv3x3(h, channels)         → BN
    if stride != 1 or x.channels != channels:
        x = conv1x1(x, channels, stride) → BN    # projection shortcut
    return ReLU(h + x)
```

**Backprop through conv (forward is cross-correlation, backward uses full convolution):**
```
∂L/∂K  = x ⋆ δ      (cross-correlation of input with upstream gradient)
∂L/∂x  = K * δ      (full convolution of kernel with upstream gradient = transposed conv)
```

## Code Example (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    def __init__(self, channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, stride=stride, padding=1, bias=False)
        self.bn1   = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn2   = nn.BatchNorm2d(channels)
        self.shortcut = nn.Sequential()
        if stride != 1:
            self.shortcut = nn.Sequential(
                nn.Conv2d(channels, channels, 1, stride=stride, bias=False),
                nn.BatchNorm2d(channels),
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)         # skip connection
        return F.relu(out)


class TinyCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.stem  = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64), nn.ReLU(),
        )
        self.layer1 = ResidualBlock(64)
        self.layer2 = ResidualBlock(64, stride=2)   # spatial /2
        self.head   = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),                # global avg pool
            nn.Flatten(),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        return self.head(self.layer2(self.layer1(self.stem(x))))


# Receptive field calculation for a stack of 3×3 convs
def effective_rf(num_layers, kernel=3, dilation=1, stride=1):
    rf = 1
    for _ in range(num_layers):
        rf += (kernel - 1) * dilation
    return rf

# e.g. 5 layers of 3×3 → RF = 11
print(effective_rf(5))   # 11
```

## Common Pitfalls

1. **Bias with BatchNorm** — `nn.Conv2d(..., bias=False)` when followed by BN; the BN's β parameter already acts as bias, so a conv bias is redundant and wastes parameters.
2. **Wrong padding for "same" output size** — for stride=1, k×k conv, use `padding=(k-1)//2`; asymmetric kernels need manual padding.
3. **Channel order** — PyTorch uses (N, C, H, W); TensorFlow/Keras defaults to (N, H, W, C). Transposing is a common bug when porting models.
4. **Pooling before BN** — generally keep the order Conv → BN → Activation → Pool.
5. **Global average pooling vs flatten** — flattening large feature maps into a dense layer dramatically increases parameters; prefer `AdaptiveAvgPool2d(1)` for classification heads.
6. **Small spatial input with too many strides** — e.g. applying ResNet (designed for 224×224) to 32×32 without removing the 7×7 stem and initial max-pool.
7. **Data augmentation tied to normalisation** — always normalise with per-channel mean/std computed on the training set; apply augmentation only during training.

## Connections to Other Topics (this book)

- **Backprop (Ch. 6)** — backward through conv is a transposed convolution (∂L/∂x) and a cross-correlation (∂L/∂K); same chain-rule mechanism.
- **Regularization (Ch. 7)** — data augmentation (crop, flip, cutout) is the primary regulariser for image CNNs; BN adds implicit regularisation through mini-batch noise.
- **Optimization (Ch. 8)** — BN smooths the loss surface, enabling higher learning rates; SGD+momentum with cosine annealing outperforms Adam on many CNN benchmarks.
- **Sequence Models (Ch. 10)** — temporal/causal convolutions (WaveNet, TCN) apply 1-D dilated convs to sequences, offering a parallelisable alternative to RNNs.
