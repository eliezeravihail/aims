# Segmentation
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a

## Core Concept
Segmentation partitions an image into meaningful regions. Classic methods use graph-based energy minimization; modern methods use CNNs that predict a class label per pixel (semantic) or per instance (instance segmentation).

## Key Definitions
- **Semantic segmentation:** assigns a class label to every pixel; no object instances distinguished
- **Instance segmentation:** distinguishes separate object instances of the same class
- **Graph cut:** models segmentation as min-cut on a graph; nodes = pixels, edges = smoothness + data terms
- **GrabCut:** iterative graph cut with Gaussian mixture models for foreground/background
- **Watershed:** treats gradient image as topographic surface; floods from markers
- **FCN (Fully Convolutional Network):** replace FC layers with conv layers; enables any input size

## Pattern

```python
import cv2
import numpy as np

# GrabCut (classic interactive segmentation)
mask = np.zeros(img.shape[:2], np.uint8)
bgd_model = np.zeros((1, 65), np.float64)
fgd_model = np.zeros((1, 65), np.float64)
rect = (50, 50, 400, 300)   # (x, y, w, h) — rough bounding box
cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
fg_mask = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
result = img * fg_mask[:, :, np.newaxis]

# Deep semantic segmentation (PyTorch)
from torchvision.models.segmentation import deeplabv3_resnet50
model = deeplabv3_resnet50(pretrained=True).eval()
with torch.no_grad():
    out = model(img_tensor)['out']          # (1, num_classes, H, W)
pred = out.argmax(dim=1).squeeze()          # (H, W) class map
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Graph cut with wrong λ (smoothness weight) | Tune λ per dataset; too high → over-smooth |
| Ignoring class imbalance in loss | Use weighted cross-entropy or focal loss |
| Evaluating with pixel accuracy only | Use mIoU — pixel accuracy is misleading on imbalanced classes |
| Not handling boundary pixels | Add boundary-aware loss or CRF post-processing |

## Connections
- **recognition.md** — segmentation backbones are often pretrained classifiers
- **feature_detection.md** — superpixel pre-segmentation can seed graph-cut methods
