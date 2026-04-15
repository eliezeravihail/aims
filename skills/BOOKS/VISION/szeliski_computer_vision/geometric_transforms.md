# Geometric Transforms
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a

## Core Concept
Geometric transforms model how image coordinates change between views or under spatial manipulation. They form a hierarchy of increasing generality: translation → rigid → similarity → affine → projective (homography).

## Key Definitions
- **Affine:** preserves parallel lines; 6 DOF; maps: [x′; y′] = A[x; y] + t (A is 2×2)
- **Homography (projective):** 8 DOF; maps planar scenes between views or corrects perspective; x′ = Hx (in homogeneous coords); divide by last coordinate
- **RANSAC:** robust estimation of H from noisy matches; iteratively samples minimal sets, counts inliers
- **DLT (Direct Linear Transform):** least-squares homography from ≥4 point correspondences
- **Warp:** apply transform to remap pixel coordinates; use inverse warp + bilinear interpolation to avoid holes

## Pattern

```python
import cv2
import numpy as np

# Estimate homography from matched keypoints
src_pts = np.float32([[x1,y1], ...])   # from image A
dst_pts = np.float32([[x2,y2], ...])   # from image B
H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransacReprojThreshold=5.0)
# mask: inlier flags

# Apply homography (warp perspective)
h, w = img_dst.shape[:2]
warped = cv2.warpPerspective(img_src, H, (w, h),
                              flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT)

# Affine transform (rotation + scale + translation)
M = cv2.getRotationMatrix2D(center=(w//2, h//2), angle=45, scale=1.0)
rotated = cv2.warpAffine(img, M, (w, h))
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Too few / noisy point matches for RANSAC | Need ≥10× more matches than minimum (4 for H) |
| Not normalizing points before DLT | Numerical instability; normalize to unit mean distance |
| Forward warp creating holes | Always use inverse warp with bilinear interpolation |
| Assuming affine when perspective is present | Affine fails for non-planar scenes or wide baselines |

## Connections
- **feature_detection.md** — RANSAC requires matched keypoints as input
- **image_formation.md** — homography between two views: H = K₂ · R · K₁⁻¹ for pure rotation
