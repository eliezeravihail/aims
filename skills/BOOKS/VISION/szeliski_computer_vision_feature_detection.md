---
source: "Computer Vision: Algorithms and Applications, 2nd ed. — Szeliski"
source_slug: szeliski_computer_vision
topic: feature_detection
quality_score: 0.83
agent_version: "1.1"
---

# Feature Detection (Szeliski Ch. 7)

## Key Definitions

- **Feature / keypoint**: A salient, localised image region that is repeatable under viewpoint, illumination, and scale changes.
- **Corner**: A point where the image gradient has large magnitude in two independent directions (high curvature of the iso-intensity contour).
- **Scale space**: A continuous family of progressively blurred images `L(x,y,σ) = G(x,y,σ) * I(x,y)`, revealing structure at multiple resolutions.
- **Blob**: A region that is brighter (or darker) than its surroundings; detected as an extremum of LoG / DoG in scale space.
- **Descriptor**: A compact, invariant vector that characterises the local appearance around a keypoint (e.g. SIFT, SURF, ORB, BRIEF).
- **Harris response**: `R = det(M) − k·trace(M)²` where `M` is the second-moment (structure) matrix, `k ≈ 0.04–0.06`.
- **Second-moment matrix** `M`: `M = Σ w(x,y) [[Ix², IxIy],[IxIy, Iy²]]` summed over a window; eigenvalues λ₁,λ₂ classify corners (both large), edges (one large), flat (both small).

## Core Algorithms

### Harris Corner Detector
1. Compute image gradients `Ix = ∂I/∂x`, `Iy = ∂I/∂y` (Sobel or derivative-of-Gaussian).
2. Form products `Ix²`, `IxIy`, `Iy²`; apply Gaussian window to get `M`.
3. Compute `R = det(M) − k·trace(M)²`.
4. Threshold `R`; suppress non-maxima spatially.
- **Not scale-invariant**; combine with scale-space for Harris-Laplace.

### Shi-Tomasi (Good Features to Track)
- Use `min(λ₁, λ₂) > threshold` instead of Harris `R`; more stable for tracking.

### SIFT (Scale-Invariant Feature Transform — Lowe 2004)
1. **Scale-space extrema**: Build DoG pyramid; find pixel local minima/maxima across adjacent scales.  
   `DoG(x,y,σ) = L(x,y,kσ) − L(x,y,σ)`
2. **Keypoint localisation**: Fit 3-D quadratic to refine location and discard low-contrast points (`|D(x̂)| < 0.03`) and edge responses (ratio of principal curvatures > 10).
3. **Orientation assignment**: Histogram of gradient orientations in 36-bin, σ=1.5 neighbourhood; assign dominant peak ±80% peaks.
4. **Descriptor**: 4×4 spatial bins × 8-direction histogram = 128-D vector, normalised, clipped at 0.2, renormalised.

### ORB (Oriented FAST + Rotated BRIEF)
- **Fast**, patent-free SIFT alternative. Detects with FAST corner test; uses intensity centroid for orientation; descriptor = rBRIEF (steered binary strings, 256 bits).
- Match with Hamming distance.

## Python Code Example

```python
import cv2
import numpy as np

def detect_and_describe(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # --- Harris corners (raw R map) ---
    gray_f = np.float32(gray)
    harris_R = cv2.cornerHarris(gray_f, blockSize=2, ksize=3, k=0.04)
    harris_R = cv2.dilate(harris_R, None)                  # highlight local maxima
    corners_img = img_bgr.copy()
    corners_img[harris_R > 0.01 * harris_R.max()] = [0, 0, 255]

    # --- SIFT keypoints + descriptors ---
    sift = cv2.SIFT_create(nfeatures=500)
    kps, descs = sift.detectAndCompute(gray, None)
    sift_img = cv2.drawKeypoints(
        gray, kps, None,
        flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
    )

    # --- ORB (fast, binary) ---
    orb = cv2.ORB_create(nfeatures=500)
    kps_orb, descs_orb = orb.detectAndCompute(gray, None)

    # --- BF matching (SIFT: L2; ORB: Hamming) ---
    # Example: match two descriptors from two views
    bf_sift = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
    bf_orb  = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    return kps, descs, kps_orb, descs_orb

def ratio_test_match(descs1, descs2, ratio=0.75):
    """Lowe ratio test for robust SIFT matching."""
    bf = cv2.BFMatcher(cv2.NORM_L2)
    raw = bf.knnMatch(descs1, descs2, k=2)
    good = [m for m, n in raw if m.distance < ratio * n.distance]
    return good
```

## Common Pitfalls

1. **Applying Harris to uint8**: Always convert to `float32` before `cornerHarris`; integer arithmetic overflows gradient products.
2. **Forgetting NMS**: Raw `R` maps have clusters of high-response pixels; always apply non-maximum suppression (dilation trick or `goodFeaturesToTrack`).
3. **Scale sensitivity of Harris**: Harris corners drift under zoom — use SIFT/ORB for cross-scale matching.
4. **Descriptor normalisation before ratio test**: Do NOT re-normalise SIFT descriptors externally; `cv2.SIFT_create` already outputs L2-normalised, clipped vectors.
5. **ORB orientation failure on blur**: ORB's FAST requires sufficient contrast; pre-process very dark/blurry images.
6. **Large `k` in Harris**: k > 0.06 over-suppresses true corners in textured scenes; stay at 0.04–0.05.
7. **Descriptor database size**: 128-D float SIFT at scale: use FLANN (KD-tree) not BFMatcher for >10k descriptors.

## Connections to Other Book Topics

- **Image formation** (Ch. 2–3): Gaussian PSF models relate directly to scale-space construction.
- **Geometric transforms** (Ch. 8): Detected feature correspondences feed homography / essential matrix estimation via RANSAC.
- **Segmentation** (Ch. 5): Superpixel boundaries coincide with edge/corner maps; features can seed region growing.
- **Recognition** (Ch. 14): Bag-of-words and Fisher vectors quantise SIFT descriptors for image classification; CNN feature maps are the modern successor.
