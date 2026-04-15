---
source: "Computer Vision: Algorithms and Applications, 2nd ed. — Szeliski"
source_slug: szeliski_computer_vision
topic: recognition
quality_score: 0.83
agent_version: "1.1"
---

# Recognition (Szeliski Ch. 14)

## Key Definitions

- **Image classification**: Assign a single label to an entire image (e.g. "cat", "car").
- **Object detection**: Localise and classify one or more object instances; output = (class, bounding box, score) per instance.
- **Instance segmentation**: Per-pixel labelling that separates different *instances* of the same class (Mask R-CNN).
- **Visual vocabulary / Bag of Words (BoW)**: Cluster descriptor space into `k` visual words; represent an image as a histogram of visual-word frequencies.
- **Fisher vector**: Soft-assignment encoding of descriptors using GMM; first and second-order statistics → richer than BoW, fewer clusters needed.
- **Convolutional feature map**: Activation volume of a conv layer; spatially preserves location, abstracts appearance. Used as features for downstream tasks.
- **Transfer learning / fine-tuning**: Initialise with ImageNet-pretrained weights; retrain (all or final layers) on target dataset.
- **Precision / Recall / mAP**: For detection, sort predictions by confidence; AP = area under P-R curve per class; mAP = mean over classes.
- **IoU (Intersection over Union)**: `IoU = |pred ∩ gt| / |pred ∪ gt|`; standard threshold for true-positive detection = 0.5.
- **Non-maximum suppression (NMS)**: Remove overlapping detection boxes with lower score if `IoU > threshold`.

## Core Algorithms

### Bag-of-Words Pipeline
1. Extract dense or keypoint SIFT descriptors from training images.
2. K-means cluster to build vocabulary of `k` words (k ≈ 1000–100k).
3. Assign each descriptor to nearest word (hard) or soft-assign (Fisher/VLAD).
4. L2-normalise frequency histogram; apply TF-IDF weighting.
5. Classify with SVM (RBF or χ²-kernel for histograms).

### Sliding Window Detection (legacy; baseline understanding)
1. Resize image to multiple scales (image pyramid).
2. At each scale, slide a fixed-size window; extract features (HoG).
3. Classify window with linear SVM; record score.
4. NMS over all windows and scales.
- **HoG**: Histogram of Oriented Gradients, 8×8 cell, 2×2 block normalisation (L2-Hys), 9 orientation bins.

### Two-Stage CNN Detection (Faster R-CNN)
1. **Backbone CNN** (e.g. ResNet-50) produces feature map at 1/16 input resolution.
2. **Region Proposal Network (RPN)**: Predict objectness + bounding-box regression for `k` anchors per spatial location.
3. **RoI Pooling / Align**: Warp each proposal to fixed-size feature vector.
4. **Head**: Two FC layers → class logits + box regression.
- Loss: `L = L_cls + λ·L_reg` (cross-entropy + smooth-L1).

### One-Stage Detection (YOLO / SSD)
- No separate proposal stage; directly regress boxes and classes on a grid.
- YOLO v3+: FPN backbone; 3 scales; anchor-based; `σ(t_x), σ(t_y)` for centre, `p_w·e^{t_w}` for size.

## Python Code Example

```python
import cv2
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.svm import LinearSVC
from sklearn.preprocessing import normalize

# --- Bag-of-Words: build vocabulary + encode images ---
def build_bow_vocabulary(descriptor_list, k=1000):
    """descriptor_list: list of (N_i, 128) SIFT descriptor arrays."""
    all_descs = np.vstack(descriptor_list).astype(np.float32)
    kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=4096)
    kmeans.fit(all_descs)
    return kmeans

def encode_bow(descs, kmeans):
    if descs is None or len(descs) == 0:
        return np.zeros(kmeans.n_clusters)
    words = kmeans.predict(descs.astype(np.float32))
    hist, _ = np.histogram(words, bins=np.arange(kmeans.n_clusters + 1))
    return normalize(hist.reshape(1, -1), norm='l2').ravel()

# --- HoG feature extraction ---
def extract_hog(img_bgr, win_size=(64, 128)):
    img_resized = cv2.resize(img_bgr, win_size)
    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    hog = cv2.HOGDescriptor(
        _winSize=win_size,
        _blockSize=(16, 16), _blockStride=(8, 8),
        _cellSize=(8, 8),    _nbins=9
    )
    return hog.compute(gray).ravel()

# --- NMS (Malisiewicz fast NMS) ---
def nms(boxes, scores, iou_threshold=0.5):
    """boxes: (N,4) [x1,y1,x2,y2]; scores: (N,). Returns kept indices."""
    if len(boxes) == 0:
        return []
    x1, y1, x2, y2 = boxes[:,0], boxes[:,1], boxes[:,2], boxes[:,3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]; keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        iou = (w * h) / (areas[i] + areas[order[1:]] - w * h)
        order = order[np.where(iou <= iou_threshold)[0] + 1]
    return keep

# --- Load a pretrained detector with OpenCV DNN (YOLO example) ---
def yolo_detect(img_bgr, weights, config, names, conf_thr=0.4, nms_thr=0.4):
    net = cv2.dnn.readNetFromDarknet(config, weights)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    h, w = img_bgr.shape[:2]
    blob = cv2.dnn.blobFromImage(img_bgr, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layer_names = [net.getLayerNames()[i - 1]
                   for i in net.getUnconnectedOutLayers().ravel()]
    outputs = net.forward(layer_names)

    boxes, confidences, class_ids = [], [], []
    for out in outputs:
        for det in out:
            scores = det[5:]
            cid = int(np.argmax(scores))
            conf = float(scores[cid])
            if conf > conf_thr:
                cx, cy, bw, bh = (det[:4] * np.array([w, h, w, h])).astype(int)
                x1, y1 = cx - bw // 2, cy - bh // 2
                boxes.append([x1, y1, bw, bh])
                confidences.append(conf)
                class_ids.append(cid)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_thr, nms_thr)
    results = []
    for i in indices.ravel():
        x, y, bw, bh = boxes[i]
        results.append({'class': names[class_ids[i]], 'conf': confidences[i],
                        'box': (x, y, x+bw, y+bh)})
    return results
```

## Common Pitfalls

1. **Data leakage through vocabulary construction**: The BoW vocabulary (K-means) must be built only on *training* images; including any test image descriptors inflates accuracy.
2. **Ignoring spatial information in BoW**: Pure BoW discards location; use Spatial Pyramid Matching (SPM) — divide into 1×1, 2×2, 4×4 grids and concatenate histograms.
3. **Anchor scale mismatch in RPN**: Anchors must cover the actual scale distribution of objects in your dataset; copy-pasting COCO anchors for a medical imaging dataset will under-detect small objects.
4. **IoU threshold inconsistency**: Training uses `IoU > 0.5` for positives but evaluation may use COCO's `0.5:0.05:0.95`; know which metric you're optimising.
5. **Not normalising HoG blocks**: Omitting L2-Hys block normalisation causes HoG to be sensitive to global illumination; always normalise.
6. **Fine-tuning all layers on small dataset**: If target dataset < 1000 images, fine-tune only the head (or last 2 blocks); full fine-tuning will overfit.
7. **Soft-NMS vs. hard NMS**: In dense scenes (pedestrians), hard NMS suppresses true second instances with high IoU; Soft-NMS decays scores instead of removing boxes.

## Connections to Other Book Topics

- **Feature detection** (Ch. 7): BoW is built on SIFT descriptors; CNN feature maps are learned replacements that obsolete hand-crafted detectors at scale.
- **Image formation** (Ch. 2–3): Camera calibration and colour normalisation reduce domain shift between training and deployment.
- **Segmentation** (Ch. 5): Semantic segmentation shares the per-pixel classification goal; Mask R-CNN unifies detection + instance segmentation; CRF post-processing sharpens boundaries.
- **Geometric transforms** (Ch. 8): Data augmentation via affine/homographic transforms is critical for robust recognition; test-time augmentation via multi-scale pyramids follows directly.
