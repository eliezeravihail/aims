# Segmentation
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a
**Read more:** https://szeliski.org/Book — Chapter 5: Segmentation

## What this book adds
Szeliski derives segmentation as an **energy minimization problem** — the unified formulation that connects graph cuts, MRFs, and active contours. He explains why **graph cut produces globally optimal solutions** for certain energy functions (submodular) while dynamic programming is optimal for chain-structured problems — and when neither applies. This energy-minimization framing explains why modern deep segmentation heads (CRF post-processing, dense prediction) work the way they do.

## Core Concept
Segmentation assigns a label `l(x) ∈ {1…K}` to every pixel x. The goal is to find the labeling that minimizes an energy:
```
E(l) = Σₓ Edata(l(x), x) + λ Σ_{x,y∈N} Esmooth(l(x), l(y))
```
The **data term** penalizes labels inconsistent with pixel appearance; the **smoothness term** penalizes label discontinuities between neighboring pixels. The tension between these two terms defines the segmentation.

## Key Definitions
- **MRF (Markov Random Field):** probabilistic graphical model where each pixel's label depends only on its neighbors; the energy E(l) above is the negative log probability of an MRF
- **Graph cut:** minimum cut on a graph where nodes are pixels + source/sink (foreground/background); min-cut = minimum energy for binary labeling with submodular pairwise terms
- **Submodular function:** `f(A) + f(B) ≥ f(A∪B) + f(A∩B)` — the condition that guarantees graph cut finds the global optimum
- **α-expansion:** iterative algorithm for multi-label MRFs; each step optimally assigns pixels to label α or keeps their current label; converges to a local minimum with strong optimality guarantees
- **Superpixels:** over-segmentation into compact, perceptually uniform regions (SLIC, SEEDS); reduces pixels from ~megapixels to ~hundreds for downstream algorithms

## Deep Dive

### Why graph cut finds the global optimum — the max-flow / min-cut theorem (§5.3)
For binary segmentation with **submodular** pairwise terms, the energy minimization is equivalent to a max-flow problem on a graph:
- Source node s = foreground, sink node t = background
- Each pixel i has edges to s and t with weights from the data term
- Adjacent pixels i, j have bidirectional edges with weights from the smoothness term

The min-cut separates s-connected pixels (foreground) from t-connected (background). By the max-flow min-cut theorem, this is solvable in polynomial time. **The key constraint**: the pairwise term must satisfy `V(α, β) + V(γ, δ) ≤ V(α, δ) + V(γ, β)` (submodularity) for the graph to be representable with non-negative edge weights.

```python
import cv2
import numpy as np

def grabcut_segmentation(img, rect, num_iter=5):
    """
    GrabCut = iterative graph cut with GMM data term (Szeliski §5.3.2).
    Each iteration:
      1. Fit Gaussian Mixture Models to foreground/background pixels
      2. Compute per-pixel data term from GMM likelihoods
      3. Run graph cut to update segmentation
    """
    mask = np.zeros(img.shape[:2], np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)  # GMM state (internal to OpenCV)
    fgd_model = np.zeros((1, 65), np.float64)

    # GC_INIT_WITH_RECT: pixels outside rect are hard background
    cv2.grabCut(img, mask, rect, bgd_model, fgd_model, num_iter,
                cv2.GC_INIT_WITH_RECT)

    # mask: 0=background, 1=foreground, 2=probable background, 3=probable foreground
    fg_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)

    # Refinement: user can mark hard foreground/background pixels then re-run
    # with cv2.GC_INIT_WITH_MASK to fix errors
    return fg_mask

def refine_with_user_strokes(img, mask, bgd_model, fgd_model,
                              fg_strokes, bg_strokes):
    """Szeliski §5.3.2: interactive refinement via scribbles"""
    for pt in fg_strokes:
        cv2.circle(mask, pt, 5, cv2.GC_FGD, -1)   # hard foreground
    for pt in bg_strokes:
        cv2.circle(mask, pt, 5, cv2.GC_BGD, -1)   # hard background
    cv2.grabCut(img, mask, None, bgd_model, fgd_model, 5,
                cv2.GC_INIT_WITH_MASK)
    return np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
```

### SLIC superpixels — the distance metric (§5.2.1)
SLIC clusters pixels in a 5D space `[L, a, b, x, y]` (CIELAB + position), with a combined distance:
```
D = sqrt( d_color² + (m/S)² · d_spatial² )
```
where S is superpixel size and m controls color vs. spatial compactness tradeoff. Setting m=10 gives balanced superpixels; m→0 gives irregular, color-faithful superpixels; m→∞ gives regular grids (ignores color).

```python
from skimage.segmentation import slic, mark_boundaries

def compute_superpixels(img, n_segments=500, compactness=10.0):
    """
    SLIC superpixels following Szeliski §5.2.1.
    compactness (=m above): higher = more square superpixels, less color-faithful
    n_segments: approximate number of superpixels
    """
    segments = slic(img, n_segments=n_segments, compactness=compactness,
                    sigma=1, start_label=1, channel_axis=-1)
    # Each pixel now has a superpixel label; compute mean color per superpixel
    superpixel_means = np.array([
        img[segments == i].mean(axis=0)
        for i in np.unique(segments)
    ])
    return segments, superpixel_means
```

### Deep segmentation — why FCN works and what CRF post-processing adds (§5.5)
A Fully Convolutional Network (FCN) produces a coarse prediction map due to pooling (stride 32 in VGG). Skip connections fuse features from earlier (higher-resolution) layers to recover spatial detail. The resulting output still has blocky boundaries — a consequence of the receptive field averaging.

Dense CRF (DenseCRF, Krähenbühl 2011) adds a pairwise term that penalizes label differences between **all pairs** of pixels weighted by appearance similarity (not just 4-neighbors). This sharpens boundaries without retraining. The energy:
```
E(l) = Σᵢ θᵢ(lᵢ) + Σᵢ<ⱼ θᵢⱼ(lᵢ, lⱼ)
         ↑ CNN output      ↑ dense Gaussian pairwise (bilateral filter)
```

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Using pixel accuracy as the only metric | A model predicting "background" for all pixels gets 90%+ accuracy on PASCAL VOC | Always report mIoU = mean(TP/(TP+FP+FN)) per class |
| Smoothness term penalizing all discontinuities equally | Legitimate boundaries get over-smoothed | Weight smoothness by inverse image gradient: `λ·exp(-‖∇I‖²/σ²)` |
| Re-running graph cut from scratch after user refinement | GrabCut iterates from current state — re-init destroys the GMM | Pass `GC_INIT_WITH_MASK` not `GC_INIT_WITH_RECT` for refinement |

## Connections
- **recognition.md** — segmentation backbones are pretrained classifiers; same encoder, different head
- **feature_detection.md** — superpixel pre-segmentation reduces the graph size for graph-cut methods
- **geometric_transforms.md** — semantic segmentation maps must be transformed with the image when doing data augmentation (nearest-neighbor interpolation, not bilinear)
