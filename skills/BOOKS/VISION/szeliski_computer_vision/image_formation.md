# Image Formation
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a
**Read more:** https://szeliski.org/Book — Chapter 2: Image Formation

## What this book adds
Szeliski derives the **full projective camera model from first principles** — from the thin lens equation through the intrinsic matrix to the projection of 3D points. He explains why **radial distortion is well-modeled by a polynomial in r²** (not r), why the pinhole model is a limiting case of the thin lens, and gives the geometric interpretation of the intrinsic matrix K that makes it possible to reason about calibration without memorizing formulas.

## Core Concept
A camera maps 3D world coordinates to 2D pixel coordinates through two transformations: (1) **extrinsic** — rigid body transform from world to camera frame; (2) **intrinsic** — projection from camera frame to image plane, including focal length, sensor geometry, and lens distortion.

## Key Definitions
- **Homogeneous coordinates:** represent a 2D point (x,y) as (x, y, 1) or (λx, λy, λ); all points on a ray from the origin map to the same 2D point — this is why projection is linear in homogeneous coords
- **Intrinsic matrix K:** `[[fx, s, cx], [0, fy, cy], [0, 0, 1]]` where fx, fy are focal lengths in pixels, (cx, cy) is the principal point, s is skew (usually 0 for digital cameras)
- **Extrinsic [R|t]:** rotation matrix R ∈ SO(3) and translation t ∈ ℝ³; transforms world point X to camera frame: `Xc = RX + t`
- **Projection:** `x̃ = K[R|t]X̃` in homogeneous coords; pixel coords: `(u, v) = (x̃₁/x̃₃, x̃₂/x̃₃)`
- **Radial distortion:** barrel (k1 < 0) or pincushion (k1 > 0) distortion; model: `xd = x(1 + k1r² + k2r⁴ + k3r⁶)` where r² = x² + y²
- **FOV:** `α = 2·arctan(W / (2·fx))` where W is image width in pixels

## Deep Dive

### Why focal length is measured in pixels (§2.1.3)
The focal length f (meters) and pixel size Δ (meters/pixel) combine to give fx = f/Δ (pixels). This is the quantity you get from `cv2.calibrateCamera` — it encodes both the physical focal length and the sensor pixel density. This means:
- fx = 1000 pixels with a 4mm lens means sensor pixel size ≈ 4µm (typical smartphone)
- fx is *not* the same for the same lens on a crop vs full-frame sensor

### The thin lens model and depth of field (§2.2)
The thin lens equation: `1/f = 1/do + 1/di` where do is object distance and di is image distance. A point at distance do ≠ f creates a **circle of confusion** (CoC) on the sensor. The depth of field (DoF) is the range of do for which CoC < sensor pixel size.

```python
def depth_of_field(f_mm, aperture_n, focus_dist_m, pixel_size_um=4.0):
    """
    Compute near/far DoF limits using the thin lens model (Szeliski §2.2).
    f_mm: focal length in mm
    aperture_n: f-number (e.g., 2.8 for f/2.8)
    focus_dist_m: focused distance in meters
    pixel_size_um: sensor pixel size in micrometers
    """
    f = f_mm * 1e-3           # meters
    c = pixel_size_um * 1e-6  # circle of confusion limit = 1 pixel
    D = f / aperture_n        # aperture diameter

    # Hyperfocal distance: beyond this, everything to infinity is in focus
    H = D * f / c

    near = focus_dist_m * H / (H + focus_dist_m)
    far  = focus_dist_m * H / (H - focus_dist_m) if focus_dist_m < H else float('inf')
    return near, far
```

### Deriving the projection equations (§2.1.1)
```
World point  →  Camera frame  →  Normalized coords  →  Pixel coords
    X              Xc = RX+t        (xn, yn) = Xc/Zc     (u,v) = K·(xn,yn,1)

In matrix form:
    [u]           [fx  0  cx] [r11 r12 r13 t1] [X]
    [v]  = (1/Zc) [ 0 fy  cy] [r21 r22 r23 t2] [Y]
    [1]           [ 0  0   1] [r31 r32 r33 t3] [Z]
                                                [1]
```

The division by Zc (the "perspective divide") is the non-linear step — it projects a 3D ray onto a 2D point.

### Camera calibration — what cv2.calibrateCamera actually computes (§6.1)
The checkerboard calibration solves for K and distortion coefficients by:
1. Detecting known 3D grid points in multiple images
2. Setting up a system of linear equations from the homography between the pattern plane and image plane (DLT)
3. Refining K, R, t, k1, k2, p1, p2 jointly via non-linear least squares (Levenberg-Marquardt)

```python
import cv2, numpy as np, glob

def calibrate_camera(image_dir, board_size=(9, 6), square_size_mm=25.0):
    """
    Full calibration pipeline following Szeliski §6.1.
    board_size: interior corners (cols, rows)
    Returns K (3×3), dist (1×5), mean reprojection error.
    """
    objp = np.zeros((board_size[0]*board_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)
    objp *= square_size_mm

    obj_points, img_points = [], []
    for fname in glob.glob(f'{image_dir}/*.jpg'):
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, board_size)
        if ret:
            corners_refined = cv2.cornerSubPix(
                gray, corners, (11,11), (-1,-1),
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )
            obj_points.append(objp)
            img_points.append(corners_refined)

    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
        obj_points, img_points, gray.shape[::-1], None, None
    )
    # Compute mean reprojection error (should be < 1 pixel for good calibration)
    errors = []
    for op, ip, rv, tv in zip(obj_points, img_points, rvecs, tvecs):
        proj, _ = cv2.projectPoints(op, rv, tv, K, dist)
        errors.append(cv2.norm(ip, proj, cv2.NORM_L2) / len(proj))

    return K, dist, np.mean(errors)
```

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Mixing pixel and normalized coordinates | K⁻¹x gives normalized coords; using pixel coords in epipolar geometry gives wrong results (§6.1) | Always track which space you are in; normalize with K⁻¹ before fundamental matrix computations |
| Undistorting only at the end | Distortion affects feature positions; features detected on distorted images have wrong positions | Undistort the image first, then detect features |
| Reprojection error > 1 pixel | Calibration is unreliable; likely too few images or motion blur | Use ≥20 images, varied angles; check corner sub-pixel refinement |
| Assuming fx = fy | True for square pixels; not always true for non-standard sensors | Always use separate fx, fy unless confirmed equal by calibration |

## Connections
- **geometric_transforms.md** — calibrated K is required to decompose homography into R, t for metric reconstruction
- **feature_detection.md** — feature matching is meaningless in metric space without undistortion and calibration
