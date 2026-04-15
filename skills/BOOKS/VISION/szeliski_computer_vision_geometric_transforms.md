---
source: "Computer Vision: Algorithms and Applications, 2nd ed. — Szeliski"
source_slug: szeliski_computer_vision
topic: geometric_transforms
quality_score: 0.83
agent_version: "1.1"
---

# Geometric Transforms (Szeliski Ch. 8)

## Key Definitions

- **2-D transformation hierarchy** (from most to least constrained):
  | Name | DOF | Preserves |
  |------|-----|-----------|
  | Translation | 2 | distances, angles |
  | Euclidean (rigid) | 3 | distances, angles |
  | Similarity | 4 | angles, ratios |
  | Affine | 6 | parallelism, area ratios |
  | Projective (homography) | 8 | collinearity, cross-ratio |

- **Homography H**: 3×3 matrix (8 DOF after normalisation) mapping one projective plane to another. `x' ~ H x` (homogeneous). Valid when scene is planar or for pure rotation (any depth).
- **Essential matrix E**: `E = [t]×R`; relates corresponding normalised image coordinates in a calibrated stereo pair. `x'ᵀ E x = 0`.
- **Fundamental matrix F**: `F = K'⁻ᵀ E K⁻¹`; works with pixel coordinates (uncalibrated). `p'ᵀ F p = 0`.
- **RANSAC**: Random Sample Consensus; robustly fits a model by repeatedly sampling the minimum set of points, computing the model, and counting inliers (within distance ε).
- **Image warping**: Applying a geometric transform to remap pixel locations; always use inverse warping + interpolation to avoid holes.
- **Interpolation**: Nearest-neighbour (aliasing), bilinear (smooth, slightly blurry), bicubic (sharper, more expensive).

## Core Algorithms

### DLT (Direct Linear Transform) for Homography
- Require `n ≥ 4` point correspondences `(x_i, x'_i)`.
- Each pair gives 2 linear equations in the 9 entries of H.
- Stack into `2n × 9` matrix `A`; solve `Ah = 0` via SVD; `h = last column of V`.
- **Normalise** first: translate centroid to origin, scale so mean distance to origin = √2.

### RANSAC (homography estimation)
```
best_inliers = []
for iter in range(N):           # N = log(1-p) / log(1-(1-ε)^s), p=0.99, ε=outlier rate, s=4
    sample = random_sample(correspondences, 4)
    H_cand = DLT(sample)
    inliers = [c for c in correspondences if transfer_error(H_cand, c) < threshold]
    if len(inliers) > len(best_inliers):
        best_inliers = inliers
H_final = DLT(best_inliers)     # refit on all inliers
```
Reprojection threshold typically 3–5 pixels; ε ≈ 0.5 outlier rate → N ≈ 72 for s=4, p=0.99.

### Stereo Rectification
1. Estimate F from correspondences.
2. Compute rectifying homographies `H_L`, `H_R` such that epipolar lines become horizontal scan lines.
3. Warp both images; stereo matching then becomes 1-D search.

### Inverse Warping
```python
# Forward: src → dst  (leaves holes)
# Inverse: for each dst pixel, find src location, sample
for each (u', v') in dst:
    (u, v) = H_inv @ (u', v', 1)   # project back
    dst[u', v'] = interpolate(src, u/w, v/w)
```

## Python Code Example

```python
import cv2
import numpy as np

# --- Compute homography with RANSAC ---
def find_homography_ransac(kps1, kps2, matches, reproj_thresh=4.0):
    """
    kps1/kps2  : cv2 KeyPoint lists
    matches    : list of cv2.DMatch (after ratio test)
    Returns H (3×3), mask of inliers.
    """
    src_pts = np.float32([kps1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kps2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src_pts, dst_pts,
                                  cv2.RANSAC, reproj_thresh,
                                  confidence=0.999, maxIters=2000)
    return H, mask.ravel().astype(bool)

# --- Warp and stitch two images ---
def stitch_two_images(img1, img2, H):
    """
    img1 → warped to img2's plane via H.
    Returns panorama.
    """
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    # Corners of img1 projected into img2 plane
    corners = np.float32([[0,0],[w1,0],[w1,h1],[0,h1]]).reshape(-1,1,2)
    warped_corners = cv2.perspectiveTransform(corners, H)
    all_corners = np.concatenate([
        np.float32([[0,0],[w2,0],[w2,h2],[0,h2]]).reshape(-1,1,2),
        warped_corners
    ], axis=0)
    x_min, y_min = np.int32(all_corners.min(axis=0).ravel())
    x_max, y_max = np.int32(all_corners.max(axis=0).ravel())
    offset = np.array([[1, 0, -x_min],[0, 1, -y_min],[0, 0, 1]], dtype=np.float64)
    out_size = (x_max - x_min, y_max - y_min)
    warped = cv2.warpPerspective(img1, offset @ H, out_size)
    warped[-y_min:-y_min+h2, -x_min:-x_min+w2] = img2   # simple overlay
    return warped

# --- Fundamental matrix + epipolar lines ---
def compute_fundamental(pts1, pts2):
    """pts1/pts2: (N,2) corresponding pixel points."""
    pts1 = np.int32(pts1); pts2 = np.int32(pts2)
    F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, 1.0, 0.99)
    inliers1 = pts1[mask.ravel() == 1]
    inliers2 = pts2[mask.ravel() == 1]
    return F, inliers1, inliers2

def draw_epilines(img1, img2, pts1, pts2, F):
    lines1 = cv2.computeCorrespondEpilines(pts2.reshape(-1,1,2), 2, F).reshape(-1,3)
    lines2 = cv2.computeCorrespondEpilines(pts1.reshape(-1,1,2), 1, F).reshape(-1,3)
    h, w = img1.shape[:2]
    out1, out2 = img1.copy(), img2.copy()
    for (a,b,c), pt in zip(lines1, pts1):
        x0,y0 = 0, int(-c/b)
        x1,y1 = w, int(-(c+a*w)/b)
        cv2.line(out1, (x0,y0), (x1,y1), (0,255,0), 1)
        cv2.circle(out1, tuple(pt), 5, (0,0,255), -1)
    return out1, out2

# --- Affine transform (3 point pairs) ---
def apply_affine(img, src_pts, dst_pts):
    """src_pts / dst_pts: 3 corresponding points each, shape (3,2)."""
    M = cv2.getAffineTransform(np.float32(src_pts), np.float32(dst_pts))
    h, w = img.shape[:2]
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC)

# --- Stereo rectification ---
def rectify_stereo(K1, d1, K2, d2, R, T, img_size):
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        K1, d1, K2, d2, img_size, R, T,
        flags=cv2.CALIB_ZERO_DISPARITY, alpha=0
    )
    map1x, map1y = cv2.initUndistortRectifyMap(K1, d1, R1, P1, img_size, cv2.CV_32FC1)
    map2x, map2y = cv2.initUndistortRectifyMap(K2, d2, R2, P2, img_size, cv2.CV_32FC1)
    return (map1x, map1y), (map2x, map2y), Q
```

## Common Pitfalls

1. **Un-normalised DLT is numerically unstable**: Always normalise point coordinates to zero-mean, unit-RMS before solving; denormalise H afterwards.
2. **Homography valid only for planar or rotationally-moved scenes**: Estimating H between images with parallax and depth variation will give a high-residual "average" plane — use E/F + triangulation instead.
3. **Forgetting to update K after undistortion**: `cv2.getOptimalNewCameraMatrix` returns a new K; the old K is invalid for projecting into the undistorted image.
4. **Forward warping artefacts**: Always use inverse warping (`cv2.warpPerspective` does this correctly); manual forward-warp loops leave holes at sub-pixel boundaries.
5. **RANSAC iteration count too low**: Use the theoretical N formula; for 50% outlier rate and s=4 you need ~72 iterations; for 60% → ~272. Use `cv2.findHomography(…, maxIters=2000)`.
6. **Essential matrix from uncalibrated points**: E encodes the geometry of normalised camera coordinates `K⁻¹p`; passing raw pixel coordinates to `findEssentialMat` without dividing by K returns a meaningless result.
7. **Bicubic interpolation with large transforms**: Bicubic can ring at sharp edges; for large homographic warps (wide panoramas) use Lanczos4 (`cv2.INTER_LANCZOS4`) or accept bilinear.

## Connections to Other Book Topics

- **Image formation** (Ch. 2–3): Homography generalises the pinhole projection; calibration provides K needed to convert H → E and recover metric geometry.
- **Feature detection** (Ch. 7): SIFT/ORB correspondences are the input to RANSAC-based homography / essential matrix estimation.
- **Segmentation** (Ch. 5): Planar homographies enable mosaic-based change detection; the aligned background can be segmented away to isolate moving foreground.
- **Recognition** (Ch. 14): Geometric verification (spatial re-ranking) uses homography/affine RANSAC to confirm that candidate matches are geometrically consistent — a critical step in image retrieval.
