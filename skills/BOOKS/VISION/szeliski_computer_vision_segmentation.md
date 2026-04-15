---
source: "Computer Vision: Algorithms and Applications, 2nd ed. — Szeliski"
source_slug: szeliski_computer_vision
topic: segmentation
quality_score: 0.83
agent_version: "1.1"
---

# Segmentation (Szeliski Ch. 5)

## Key Definitions

- **Segmentation**: Partition an image into regions that are homogeneous with respect to some property (colour, texture, depth, semantics).
- **Superpixel**: An over-segmented compact region; used as a preprocessing step to reduce subsequent computation (e.g. SLIC, SEEDS).
- **Graph cut**: Minimise an energy E(label) = Σ unary(label_i) + Σ pairwise(label_i, label_j) over a pixel adjacency graph using min-cut / max-flow.
- **Markov Random Field (MRF)**: Probabilistic graphical model where each pixel's label depends only on its neighbourhood; MAP inference via graph cuts or belief propagation.
- **Active contour (snake)**: A parametric curve that minimises E = ∫ α|C'|² + β|C''|² + Eimage ds (elasticity + rigidity + image energy).
- **Level set**: Implicit representation of a contour as a zero-crossing of a scalar function φ(x,y); evolves via PDE `∂φ/∂t = F|∇φ|`.
- **GrabCut**: Iterative graph-cut algorithm seeded with a bounding box; models foreground/background as Gaussian mixtures (GMMs).
- **Normalised cut (Ncut)**: Spectral clustering criterion `Ncut(A,B) = cut(A,B)/assoc(A,V) + cut(A,B)/assoc(B,V)` minimised via generalised eigenproblem.

## Core Algorithms

### SLIC (Simple Linear Iterative Clustering)
- Superpixel algorithm operating in CIELAB + (x,y) space.
- Initialise `k` cluster centres on a grid spaced `S = sqrt(N/k)`.
- Each centre searches only within `2S × 2S` window (not all pixels).
- Distance: `d = sqrt(d_lab² + (d_xy/S)² · m²)` where `m` controls compactness.
- Iterate assignment + centre update until convergence.

### GrabCut (iterative graph cut)
1. User provides bounding box → background mask for exterior.
2. Fit GMM (5 components each) to foreground and background pixels.
3. Build graph: source = FG, sink = BG, t-links from GMM likelihoods, n-links from colour similarity.
4. Run min-cut (Ford-Fulkerson / Boykov-Kolmogorov).
5. Re-estimate GMMs from cut assignment; repeat.

### Energy formulation (generic MRF)
```
E(x) = Σ_i  Ψ_unary(x_i)           # data term: −log P(I_i | label x_i)
     + Σ_{i~j} Ψ_pairwise(x_i,x_j)  # smoothness: e.g. Potts = λ·[x_i≠x_j]·exp(-β·||I_i-I_j||²)
```

## Python Code Example

```python
import cv2
import numpy as np
from skimage.segmentation import slic, mark_boundaries

# --- GrabCut (OpenCV) ---
def grabcut_segment(img_bgr, bbox):
    """
    bbox: (x, y, w, h) bounding box around foreground object.
    Returns binary foreground mask (uint8, 0 or 1).
    """
    mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(img_bgr, mask, bbox, bgd_model, fgd_model,
                iterCount=5, mode=cv2.GC_INIT_WITH_RECT)

    # Definite or probable foreground → 1; else 0
    fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    result = img_bgr * fg_mask[:, :, np.newaxis]
    return fg_mask, result

# --- SLIC superpixels (scikit-image) ---
def slic_superpixels(img_bgr, n_segments=200, compactness=10):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    segments = slic(img_rgb, n_segments=n_segments, compactness=compactness,
                    start_label=1, channel_axis=2)
    boundary_img = (mark_boundaries(img_rgb, segments) * 255).astype(np.uint8)
    return segments, boundary_img

# --- Watershed segmentation ---
def watershed_segment(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Remove noise, find sure background/foreground
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    sure_bg  = cv2.dilate(opening, kernel, iterations=3)
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
    sure_fg = np.uint8(sure_fg)

    unknown = cv2.subtract(sure_bg, sure_fg)
    _, markers = cv2.connectedComponents(sure_fg)
    markers += 1
    markers[unknown == 255] = 0

    markers = cv2.watershed(img_bgr, markers)
    img_bgr[markers == -1] = [0, 0, 255]   # mark boundaries in red
    return markers

# --- Mean-shift segmentation ---
def meanshift_segment(img_bgr, spatial_radius=21, color_radius=51, min_density=100):
    return cv2.pyrMeanShiftFiltering(img_bgr, spatial_radius, color_radius, min_density)
```

## Common Pitfalls

1. **GrabCut requires a tight bounding box**: A box that's too loose includes too much background in the foreground GMM, causing bleed. Iterate with user-stroke corrections.
2. **Watershed over-segments without markers**: Always compute meaningful seed markers (distance transform + local maxima); running `watershed` with trivially-labelled markers produces thousands of fragments.
3. **SLIC compactness vs. boundary adherence trade-off**: High `m` → regular square superpixels (bad for non-rectangular objects); low `m` → irregular but boundary-adhering superpixels.
4. **MRF β calibration**: In the Potts pairwise term, `β = (2 · E[||I_i-I_j||²])⁻¹` (data-driven); a fixed `β` will either over-smooth or not smooth at all.
5. **Level-set re-initialisation**: The signed-distance property of `φ` degrades over time; re-initialise every ~10 iterations or use the variational regularisation term.
6. **Connected components after graph cut**: Graph-cut minimisation can leave isolated islands; always post-process with connected-component filtering.

## Connections to Other Book Topics

- **Image formation** (Ch. 2–3): Lighting model determines colour homogeneity assumptions; Lambertian assumption justifies colour-similarity pairwise terms.
- **Feature detection** (Ch. 7): Edges from gradient detectors (Canny) seed watershed markers and active contour external energy.
- **Geometric transforms** (Ch. 8): Affine/perspective-aligned image pairs share segmentation boundaries; stereo depth cues improve foreground/background separation.
- **Recognition** (Ch. 14): Semantic segmentation (DeepLab, Mask R-CNN) extends MRF graph cut with deep unary potentials; superpixels reduce spatial complexity of CRF post-processing.
