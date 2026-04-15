# Geometric Transforms
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a
**Read more:** https://szeliski.org/Book — Chapter 2: Image Formation §2.1, Chapter 6: Feature-Based Alignment §6.1

## What this book adds
Szeliski presents geometric transforms as a **hierarchy of groups** (translation ⊂ rigid ⊂ similarity ⊂ affine ⊂ projective), each with a precise DOF count and the geometric properties it preserves. He derives the **DLT algorithm** from scratch, explains why **RANSAC is effective despite its randomness** (the probability analysis that determines required iterations), and shows that homography decomposition into R, t is only valid for planar scenes — a constraint commonly violated in practice.

## Core Concept
A 2D geometric transform maps every point `(x,y)` in one image to a point `(x',y')` in another. The transform family determines what is preserved and how many point correspondences are needed to estimate it. All 2D transforms can be written as 3×3 matrix multiplication in homogeneous coordinates.

## Key Definitions

| Transform | DOF | Preserves | Min. correspondences |
|-----------|-----|-----------|---------------------|
| Translation | 2 | Orientation, distances | 1 point |
| Rigid (Euclidean) | 3 | Distances, angles | 2 points |
| Similarity | 4 | Angles, shape | 2 points |
| Affine | 6 | Parallel lines, ratios | 3 points |
| Projective (Homography) | 8 | Straight lines, cross-ratio | 4 points |

- **Homogeneous representation:** point `(x,y)` ↔ vector `(λx, λy, λ)` for any λ≠0; transforms become matrix multiplications
- **Homography H:** 3×3 matrix with 8 DOF (9 entries, 1 scale ambiguity); applies to any planar scene or pure camera rotation
- **Cross-ratio:** `(AC/BC)/(AD/BD)` — the only quantity preserved by projective transforms; useful for metric reconstruction from a single view
- **RANSAC:** Random Sample Consensus; estimates robust H by sampling minimal correspondences, computing H, counting inliers, keeping the H with most inliers

## Deep Dive

### The transform hierarchy — matrix forms in homogeneous coordinates (§2.1.2)

```
Translation:        Rigid:              Similarity:
[1  0  tx]          [cosθ -sinθ tx]     [s·cosθ -s·sinθ tx]
[0  1  ty]          [sinθ  cosθ ty]     [s·sinθ  s·cosθ ty]
[0  0   1]          [0     0    1 ]     [0       0       1 ]

Affine:             Projective (Homography):
[a b tx]            [h11 h12 h13]
[c d ty]            [h21 h22 h23]  (applied as: x' = Hx / (h31*x + h32*y + h33))
[0 0  1]            [h31 h32 h33]
```

Each level in the hierarchy can represent all transforms of lower levels — projective H includes all affine transforms when h31=h32=0.

### DLT — deriving the homography estimation equations (§6.1.1)
Each correspondence (x↔x') gives 2 linear equations in H's 9 unknowns. For N≥4 points:

```
x' × Hx = 0
→ [0ᵀ  -wᵢxᵢᵀ   yᵢ'xᵢᵀ ] [h]
  [wᵢxᵢᵀ  0ᵀ  -xᵢ'xᵢᵀ ] [  ] = 0
```

Stack into A (2N×9); solve via SVD: H = last row of Vᵀ (eigenvector of smallest singular value).

**Critical: normalize before DLT.** Without normalization, the condition number of A is ~10⁶, causing numerical instability. Normalize points so their centroid is at origin and mean distance is √2:

```python
import numpy as np

def normalize_points(pts):
    """
    Hartley normalization — required for numerically stable DLT (Szeliski §6.1.1).
    Returns normalized points and the 3×3 normalization transform T.
    """
    centroid = pts.mean(axis=0)
    shifted = pts - centroid
    mean_dist = np.sqrt((shifted**2).sum(axis=1)).mean()
    scale = np.sqrt(2) / mean_dist
    T = np.array([
        [scale,     0, -scale * centroid[0]],
        [0,     scale, -scale * centroid[1]],
        [0,         0,                    1]
    ])
    pts_h = np.hstack([pts, np.ones((len(pts), 1))])
    return (T @ pts_h.T).T[:, :2], T

def dlt_homography(src_pts, dst_pts):
    """
    Direct Linear Transform for homography estimation.
    Includes Hartley normalization for numerical stability.
    """
    src_n, T_src = normalize_points(src_pts)
    dst_n, T_dst = normalize_points(dst_pts)

    N = len(src_pts)
    A = np.zeros((2*N, 9))
    for i, ((x, y), (xp, yp)) in enumerate(zip(src_n, dst_n)):
        A[2*i]     = [0,  0,  0, -x, -y, -1,  yp*x,  yp*y,  yp]
        A[2*i+1]   = [x,  y,  1,  0,  0,  0, -xp*x, -xp*y, -xp]

    _, _, Vt = np.linalg.svd(A)
    H_n = Vt[-1].reshape(3, 3)

    # Denormalize: H = T_dst⁻¹ · H_n · T_src
    H = np.linalg.inv(T_dst) @ H_n @ T_src
    return H / H[2, 2]
```

### RANSAC — the probability analysis (§6.1.4)
The required number of iterations N to find an all-inlier sample with probability p:
```
N = log(1-p) / log(1 - ε^m)
```
where ε is inlier ratio and m is the minimum sample size (4 for homography). For ε=0.5 (50% inliers) and p=0.99:
- N = log(0.01) / log(1 - 0.5⁴) = log(0.01)/log(0.9375) ≈ **72 iterations**

This is why RANSAC is practical: even with 50% outliers, 72 iterations with 4 random points each is negligible cost.

```python
import cv2
import numpy as np

def ransac_homography(src_pts, dst_pts, reproj_threshold=3.0, confidence=0.995):
    """
    RANSAC homography following Szeliski §6.1.4.
    reproj_threshold: max pixel error for inlier (3 pixels is typical)
    confidence: probability that at least one sample is all-inliers
    """
    src = src_pts.reshape(-1, 1, 2).astype(np.float32)
    dst = dst_pts.reshape(-1, 1, 2).astype(np.float32)

    H, mask = cv2.findHomography(src, dst,
                                  method=cv2.RANSAC,
                                  ransacReprojThreshold=reproj_threshold,
                                  confidence=confidence,
                                  maxIters=2000)
    inlier_ratio = mask.ravel().sum() / len(mask)
    return H, mask.ravel().astype(bool), inlier_ratio

def warp_and_blend(img_src, img_dst, H):
    """Apply homography and blend (panorama stitching step)."""
    h, w = img_dst.shape[:2]
    warped = cv2.warpPerspective(img_src, H, (w*2, h),
                                  flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT)
    # Simple blend: paste dst over warped
    warped[:h, :w] = img_dst
    return warped
```

### When homography fails — the planarity constraint (§6.1.3)
A homography is valid between two views **only if**:
1. The scene is planar (all points on one plane), OR
2. The camera undergoes **pure rotation** (no translation)

For non-planar scenes with camera translation, different depth planes map to different homographies. In this case, use the **fundamental matrix** F (7 DOF) or **essential matrix** E (5 DOF with calibrated cameras) instead.

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Skipping Hartley normalization before DLT | Condition number ~10⁶ causes catastrophic numerical error; H is wrong | Always normalize; DLT without normalization is broken in practice |
| Using homography for 3D scenes with translation | Different depths require different H; the result is a compromise that works for none (§6.1.3) | Use fundamental matrix or stereo pipeline for 3D scenes |
| RANSAC reproj_threshold too tight | Too few inliers found; RANSAC fails even with a good H | Start with 5 pixels; tighten only after initial estimation |
| Forward warping (direct mapping) | Holes appear at sub-pixel boundaries | Always use inverse warp: for each output pixel, map backward to find source pixel, then interpolate |

## Connections
- **feature_detection.md** — RANSAC requires matched keypoints as input; quality of H depends on keypoint accuracy
- **image_formation.md** — H = K₂·R·K₁⁻¹ for pure rotation; decomposing H into R, t requires known K (Szeliski §6.3)
