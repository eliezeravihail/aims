---
source: "Computer Vision: Algorithms and Applications, 2nd ed. — Szeliski"
source_slug: szeliski_computer_vision
topic: image_formation
quality_score: 0.83
agent_version: "1.1"
---

# Image Formation (Szeliski Ch. 2–3)

## Key Definitions

- **Pinhole camera**: Ideal perspective projection; all rays pass through a single centre of projection (CoP). Real lenses approximate this with finite aperture.
- **Intrinsic matrix K**: Maps 3-D camera-space point to 2-D pixel coordinates.
  `K = [[f·sx, s, cx],[0, f·sy, cy],[0, 0, 1]]`  
  (`f` focal length, `sx/sy` pixel scaling, `cx/cy` principal point, `s` skew ≈ 0 for modern sensors).
- **Extrinsic matrix [R|t]**: Rigid-body transform from world frame to camera frame. Full projection: `x̃ = K[R|t]X̃`.
- **Homogeneous coordinates**: Point `(X,Y,Z)` → `(X,Y,Z,1)ᵀ`; 2-D point `(u,v)` → `(u,v,1)ᵀ`. Projective arithmetic without special-casing infinity.
- **Radial distortion**: Barrel (`k < 0`) or pincushion (`k > 0`). Model: `r_d = r_u(1 + k₁r_u² + k₂r_u⁴ + …)`.
- **Chromatic aberration**: Wavelength-dependent focal length; lateral (colour fringe at edges) vs axial (focus shift between channels).
- **Bayer pattern / demosaicing**: Most sensors record one colour channel per pixel; interpolation reconstructs full-colour image (bilinear, VNG, AHD).
- **HDR / tone mapping**: Scene radiance spans 10⁵:1; sensors capture ~10³:1 dynamic range. Multiple exposures → merge → tone-map for display.
- **Camera response function (CRF)**: Non-linear sensor response `g(irradiance)` → pixel value; must be inverted for radiometrically correct processing.

## Core Models

### Perspective Projection
```
[u]   [fx  0  cx] [R | t] [X]
[v] = [0  fy  cy]         [Y]  (homogeneous division by Z after multiply)
[1]   [0   0   1]         [Z]
                           [1]
```
Compact: `λ p = K [R | t] P`  (λ is depth, p is pixel, P is world point).

### Lens Distortion (OpenCV model)
```
x' = x(1 + k1·r² + k2·r⁴ + k3·r⁶) + 2p1·xy + p2(r²+2x²)
y' = y(1 + k1·r² + k2·r⁴ + k3·r⁶) + p1(r²+2y²) + 2p2·xy
r² = x² + y²,  (x,y) are normalised camera coords
```

### Radiometric Model
`I(x,y) = g( ∫ L(p) · V(p,x,y) · cos(θ) dp )`  
where `L` is scene radiance, `V` is visibility, `g` is CRF.  
For a Lambertian surface: `L ∝ ρ · (n · l)` (albedo × dot(normal, light)).

## Python Code Example

```python
import cv2
import numpy as np

# --- Project 3-D points to image plane ---
def project_points(pts3d, K, R, t, dist_coeffs=None):
    """
    pts3d : (N,3) float64 world coords
    K     : (3,3) intrinsic matrix
    R     : (3,3) or Rodrigues (3,) rotation
    t     : (3,) translation
    Returns (N,2) pixel coordinates.
    """
    if dist_coeffs is None:
        dist_coeffs = np.zeros(5)
    rvec = cv2.Rodrigues(R)[0] if R.shape == (3, 3) else R
    pts2d, _ = cv2.projectPoints(pts3d, rvec, t, K, dist_coeffs)
    return pts2d.reshape(-1, 2)

# --- Undistort an image ---
def undistort_image(img, K, dist):
    h, w = img.shape[:2]
    new_K, roi = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), alpha=0)
    undist = cv2.undistort(img, K, dist, newCameraMatrix=new_K)
    x, y, w2, h2 = roi
    return undist[y:y+h2, x:x+w2], new_K

# --- Simple HDR merge (Debevec) ---
def merge_hdr(images_bgr, exposure_times):
    merge_debevec = cv2.createMergeDebevec()
    hdr = merge_debevec.process(images_bgr, times=np.array(exposure_times, dtype=np.float32))
    # Tone map with Reinhard
    tonemap = cv2.createTonemap(gamma=2.2)
    ldr = tonemap.process(hdr)
    ldr_8u = np.clip(ldr * 255, 0, 255).astype(np.uint8)
    return hdr, ldr_8u

# --- Calibration from chessboard ---
def calibrate_camera(image_files, board_shape=(9, 6), square_mm=25.0):
    obj_pts, img_pts = [], []
    objp = np.zeros((board_shape[0]*board_shape[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_shape[0], 0:board_shape[1]].T.reshape(-1,2) * square_mm

    for fname in image_files:
        gray = cv2.cvtColor(cv2.imread(fname), cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, board_shape, None)
        if ret:
            corners = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1),
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
            obj_pts.append(objp); img_pts.append(corners)

    _, K, dist, rvecs, tvecs = cv2.calibrateCamera(
        obj_pts, img_pts, gray.shape[::-1], None, None)
    return K, dist, rvecs, tvecs
```

## Common Pitfalls

1. **Forgetting to invert the CRF before photometric operations**: Operating on gamma-encoded pixel values (standard JPEG) as if they were linear radiance breaks any computation involving pixel sums (mosaicing, blending, HDR).
2. **Principal point ≠ image centre**: Never hardcode `cx = W/2, cy = H/2`; always calibrate or read from EXIF/metadata.
3. **Mixing distorted and undistorted coordinates**: Once you call `undistort`, homography/essential-matrix math must use the *new* `K`; mixing distorted points with the undistorted `K` produces subtle errors.
4. **Skew assumption**: Most modern cameras have `s ≈ 0`, but scanned documents and frame-grab devices may not; check the calibration residuals.
5. **Radial distortion sign convention**: OpenCV stores `(k1,k2,p1,p2,k3)`; other libraries use different orderings — always confirm before copy-pasting coefficients.
6. **Over-relying on `getOptimalNewCameraMatrix` alpha=1**: `alpha=1` keeps all pixels but introduces a border of black (undefined) pixels that break edge detectors; `alpha=0` crops but is geometrically clean.

## Connections to Other Book Topics

- **Feature detection** (Ch. 7): Intrinsic calibration ensures scale is consistent across the image; distortion correction prevents radial bias in keypoint distributions.
- **Geometric transforms** (Ch. 8): The full projection matrix `K[R|t]` is the foundation of homography, stereo rectification, and structure-from-motion.
- **Segmentation** (Ch. 5): Radiometric models (Lambertian, specular) inform colour-based clustering and active-contour energy terms.
- **Recognition** (Ch. 14): Normalised image coordinates (divide by K) decouple appearance from camera parameters, improving cross-domain generalisation.
