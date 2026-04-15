# Image Formation
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a

## Core Concept
Image formation models how 3D world points project onto a 2D sensor. The **pinhole camera model** is the foundation; real cameras add lens distortion and radiometric effects.

## Key Definitions
- **Intrinsic matrix K:** encodes focal length (fx, fy) and principal point (cx, cy): K = [[fx,0,cx],[0,fy,cy],[0,0,1]]
- **Extrinsic [R|t]:** rotation + translation from world to camera frame
- **Projection:** x̃ = K[R|t]X̃ (homogeneous); divide by z for pixel coordinates
- **Radial distortion:** barrel/pincushion; correct with: xc = x(1 + k1r² + k2r⁴)
- **FOV:** field of view; fov = 2·arctan(sensor_size / (2·f))
- **Depth of field:** range in focus; controlled by aperture (f-number)

## Pattern

```python
import cv2
import numpy as np

# Project 3D points to 2D
def project(points_3d, K, R, t):
    # points_3d: (N, 3)
    pts_cam = (R @ points_3d.T + t[:, None]).T  # (N, 3) in camera frame
    pts_2d = (K @ pts_cam.T).T                   # (N, 3) homogeneous
    return pts_2d[:, :2] / pts_2d[:, 2:]         # (N, 2) pixel coords

# Camera calibration from checkerboard
ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
    obj_points, img_points, img_size, None, None
)
# Undistort
undistorted = cv2.undistort(img, K, dist)
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Ignoring lens distortion | Always undistort before metric computations |
| Mixing pixel vs. normalized coords | Normalize with K⁻¹ before epipolar geometry |
| Wrong axis convention (OpenCV vs. OpenGL) | OpenCV: z forward, y down; OpenGL: z back, y up |
| Assuming square pixels | Separate fx, fy unless confirmed equal |

## Connections
- **geometric_transforms.md** — homography relates two views of a planar scene via K, R, t
- **feature_detection.md** — calibrated K needed for metric matching and reconstruction
