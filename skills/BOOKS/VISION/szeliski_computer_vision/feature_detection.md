# Feature Detection
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a

## Core Concept
Feature detection finds **repeatable**, **distinctive** locations in images that can be matched across viewpoints, scales, and lighting changes. The pipeline is: detect keypoints → compute descriptor → match descriptors.

## Key Definitions
- **Harris corner:** uses second-moment matrix M = Σ[Iₓ², IₓIᵧ; IₓIᵧ, Iᵧ²]; corner when both eigenvalues are large; response R = det(M) − k·trace(M)²
- **SIFT:** Scale-Invariant Feature Transform; detects DoG extrema across scale space; 128-dim gradient histogram descriptor; rotation-invariant
- **ORB:** binary descriptor (BRIEF + rotation compensation); 10× faster than SIFT; patent-free
- **NMS (Non-Maximum Suppression):** keep only local maxima of response map within a window
- **Scale space:** image convolved with Gaussians at increasing σ; DoG = difference of adjacent scales

## Pattern

```python
import cv2

# ORB — fast, good for real-time
orb = cv2.ORB_create(nfeatures=1000)
kp, des = orb.detectAndCompute(gray_img, None)

# SIFT — more robust, use when accuracy > speed
sift = cv2.SIFT_create()
kp, des = sift.detectAndCompute(gray_img, None)

# Match descriptors (brute-force + ratio test)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)  # NORM_L2 for SIFT
matches = bf.knnMatch(des1, des2, k=2)
good = [m for m, n in matches if m.distance < 0.75 * n.distance]  # Lowe ratio test
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Detecting too many/few keypoints | Tune `nfeatures` and response threshold |
| Skipping Lowe's ratio test | Many false matches; always apply ratio=0.7–0.8 |
| Using Hamming distance for SIFT | Use L2; Hamming is only for binary descriptors (ORB, BRIEF) |
| No image preprocessing | Normalize lighting with CLAHE before detection |

## Connections
- **geometric_transforms.md** — matched keypoints are input to homography estimation (RANSAC)
- **recognition.md** — bag-of-visual-words uses SIFT descriptors
