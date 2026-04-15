# Feature Detection
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a
**Read more:** https://szeliski.org/Book — Chapter 7: Feature Detection and Matching

## What this book adds
Szeliski derives feature detectors from first principles using the **second-moment matrix (structure tensor)**, explaining *why* corners are detectable (two large eigenvalues) and *why* edges are not (one large eigenvalue). He gives the precise conditions under which SIFT's scale selection is optimal and explains the Lowe ratio test in terms of the probability of false matches — something usually cited as a magic constant (0.75) without justification.

## Core Concept
A good feature point is **repeatable** (found in both images despite viewpoint/lighting changes), **distinctive** (its local patch is unique), and **accurate** (localized precisely). The structure tensor provides a unified mathematical tool to measure both corner strength and local anisotropy.

## Key Definitions
- **Second-moment matrix (M):** `M = Σ_{x∈W} w(x) [Iₓ², IₓIᵧ; IₓIᵧ, Iᵧ²]` where W is a local window and w is a Gaussian weight; eigenvalues λ₁ ≥ λ₂ characterize the local image structure
- **Harris response:** `R = det(M) − k·trace(M)² = λ₁λ₂ − k(λ₁+λ₂)²`; corner when R > 0 (both eigenvalues large); edge when R < 0; flat when R ≈ 0
- **Scale-space:** a family of images Lσ = G(σ) * I for increasing σ; features detected at their **characteristic scale** are scale-invariant
- **DoG (Difference of Gaussians):** L(x, kσ) − L(x, σ) ≈ (k−1)σ²∇²G * I — approximates the Laplacian of Gaussian at scale σ; SIFT blob detector
- **Lowe ratio test:** for a match with nearest distance d₁ and second-nearest d₂, accept if d₁/d₂ < 0.8; Lowe showed this has a well-defined ROC curve and 0.8 is near-optimal

## Deep Dive

### The eigenvalue interpretation of M (§7.1.1)
The eigenvalues of M represent the **principal curvatures of the local intensity surface**:
- `λ₁ ≈ λ₂ ≈ 0`: flat region — no gradient, no feature
- `λ₁ >> λ₂ ≈ 0`: edge — gradient in one direction only
- `λ₁ ≈ λ₂ >> 0`: corner — gradients in all directions

The Harris response `R = λ₁λ₂ − k(λ₁+λ₂)²` avoids computing eigenvalues (expensive) by using the determinant and trace — cheaper but equivalent for classification.

```python
import cv2
import numpy as np

def harris_from_scratch(img, k=0.04, sigma=1.5, threshold=0.01):
    """
    Implements Harris detector following Szeliski §7.1.1 exactly.
    Returns corner locations and response map.
    """
    gray = img.astype(np.float32) / 255.0
    # Compute image gradients
    Ix = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    Iy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    # Compute second-moment matrix elements (with Gaussian weighting)
    Ixx = cv2.GaussianBlur(Ix * Ix, (0,0), sigma)
    Iyy = cv2.GaussianBlur(Iy * Iy, (0,0), sigma)
    Ixy = cv2.GaussianBlur(Ix * Iy, (0,0), sigma)

    # Harris response R = det(M) - k * trace(M)^2
    det_M = Ixx * Iyy - Ixy ** 2
    trace_M = Ixx + Iyy
    R = det_M - k * trace_M ** 2

    # Non-maximum suppression + threshold
    R_max = cv2.dilate(R, np.ones((9,9)))
    corners = np.argwhere((R == R_max) & (R > threshold * R.max()))
    return corners, R
```

### Why SIFT is scale-invariant — the scale selection argument (§7.2)
SIFT detects extrema in the **scale-space DoG pyramid**. The key insight (Lindeberg 1994, cited by Szeliski): the normalized LoG `σ²∇²G` has a maximum response when σ equals the **characteristic scale** of the blob — i.e., the radius at which the blob's edge gradient is strongest. By searching across scales and selecting the σ that maximizes response, SIFT automatically finds the scale at which the feature is most prominent, making the detection scale-invariant.

The orientation assignment (histogram of gradients in a 36-bin orientation map, selecting the dominant orientation) achieves rotation invariance by canonicalizing the descriptor's reference frame.

### The Lowe ratio test — the probability interpretation
Given two candidate matches with distances d₁ < d₂:
- `d₁/d₂` is a measure of **distinctiveness**: close to 1 means the second-best match is nearly as good → ambiguous
- Lowe's experiment (2004): at ratio < 0.8, false match rate is ~10%; at ratio < 0.6, false match rate drops to ~1% but recall falls

```python
def lowe_ratio_match(des1, des2, ratio=0.75):
    """
    Lowe ratio test from Szeliski §7.1.3.
    Returns only unambiguous matches where the best match is distinctly better
    than the second-best.
    ratio=0.75 is Lowe's empirically optimal threshold (false positive rate ~5%).
    """
    bf = cv2.BFMatcher(cv2.NORM_L2)
    # k=2 returns the 2 nearest neighbors for each descriptor
    knn_matches = bf.knnMatch(des1, des2, k=2)
    good_matches = []
    for m, n in knn_matches:
        if m.distance < ratio * n.distance:
            good_matches.append(m)
    return good_matches
```

### ORB vs SIFT — the practical tradeoff (§7.1.4)
| Property | SIFT | ORB |
|----------|------|-----|
| Invariance | Scale + rotation + illumination | Rotation (approximate scale) |
| Descriptor | 128-float (512 bytes) | 256-bit binary (32 bytes) |
| Matching | L2 distance | Hamming distance (XOR + popcount) |
| Speed | ~1000 ms / 1000 keypoints | ~15 ms / 1000 keypoints |
| Patent | Free (expired 2020) | Free (BSD) |

Use SIFT when accuracy matters; ORB when real-time performance is required. For embedded vision, FAST detector + ORB descriptor is the standard combination.

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Using Hamming distance for SIFT | SIFT is a float descriptor; Hamming is undefined — silently returns wrong distances | Use L2 (NORM_L2) for SIFT/SURF; Hamming (NORM_HAMMING) for ORB/BRIEF |
| Skipping non-maximum suppression | Nearby redundant corners harm matching speed and accuracy | Apply NMS with window ≥ 2× expected keypoint spacing |
| Ratio test with threshold = 1.0 | Accepts all matches including ambiguous ones — ~50% false positives | Use 0.7–0.8 as Lowe recommends |
| Not converting to grayscale before detection | Color gradients in one channel can dominate; detectors assume luminance | Convert to grayscale (weighted: 0.299R + 0.587G + 0.114B) |

## Connections
- **geometric_transforms.md** — matched keypoints from this pipeline feed directly into RANSAC homography estimation
- **recognition.md** — SIFT descriptors are the basis for Bag-of-Visual-Words; cluster them with k-means to build a visual vocabulary
