# Recognition
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a
**Read more:** https://szeliski.org/Book — Chapter 6: Feature-Based Alignment and Chapter 14: Recognition

## What this book adds
Szeliski traces recognition from the bag-of-visual-words pipeline through deep CNNs, explaining *why* the BoVW pipeline works (Fisher's linear discriminant, vector quantization theory) and *why* CNNs superseded it (learned, task-specific features vs. hand-crafted ones). He also covers the **sliding window detector** as the conceptual predecessor to anchor-based detectors — making the transition from BoVW to Faster R-CNN intellectually coherent rather than arbitrary.

## Core Concept
Recognition maps an image or image region to a discrete label. The core challenge is **intra-class variability** (same object, different appearance) vs. **inter-class similarity** (different objects, similar appearance). The evolution of solutions reflects increasing ability to learn the right feature representation from data.

## Key Definitions
- **Bag of Visual Words (BoVW):** cluster SIFT descriptors into a K-word visual vocabulary; represent an image as a K-dimensional histogram of word counts; classify with SVM
- **Fisher Vector:** alternative to BoVW; encodes the mean and variance offset from a Gaussian mixture model — richer representation, often 10× better accuracy than BoVW
- **IDF weighting:** tf-idf adapted for visual words; rare words (discriminative) get higher weight; common words (background) get lower weight
- **Hard negative mining:** iteratively add false positives from the detector to the negative training set; key to training SVMs for detection without needing all negative windows
- **Sliding window:** exhaustively apply a classifier at every position and scale; O(W·H·S) evaluations; conceptual basis for anchor-based detection

## Deep Dive

### Why BoVW works — the vector quantization argument (§14.2.1)
A SIFT descriptor lives in ℝ¹²⁸. K-means with K=1000–10000 clusters partitions this space into Voronoi cells (visual words). Each cell corresponds to a visual pattern (edge direction, texture, color histogram type). The bag-of-words assumption — **spatial position is discarded** — is both the strength (viewpoint invariance) and the weakness (no spatial relations).

```python
from sklearn.cluster import MiniBatchKMeans
import numpy as np

def build_visual_vocabulary(all_descriptors, K=1000):
    """
    BoVW vocabulary from SIFT descriptors (Szeliski §14.2.1).
    MiniBatchKMeans is essential — regular KMeans is too slow for 10M+ descriptors.
    """
    kmeans = MiniBatchKMeans(n_clusters=K, batch_size=10000, n_init=3, random_state=42)
    kmeans.fit(all_descriptors)
    return kmeans

def image_to_bovw_histogram(descriptors, vocabulary, K):
    """Convert image descriptors to normalized BoVW histogram."""
    if len(descriptors) == 0:
        return np.zeros(K)
    words = vocabulary.predict(descriptors)
    histogram, _ = np.histogram(words, bins=K, range=(0, K))
    # L1 normalize — makes histogram comparable across images with different keypoint counts
    return histogram.astype(float) / (histogram.sum() + 1e-8)

def apply_idf_weighting(histograms, epsilon=1e-8):
    """
    TF-IDF: down-weight visual words that appear in many images.
    idf[k] = log(N / df[k]) where df[k] = number of images containing word k.
    """
    N = len(histograms)
    df = (np.array(histograms) > 0).sum(axis=0)
    idf = np.log((N + epsilon) / (df + epsilon))
    return [h * idf for h in histograms]
```

### Fisher Vector — why it outperforms BoVW (§14.2.2)
BoVW only encodes which words appear. Fisher Vector encodes **how** each descriptor deviates from its assigned Gaussian component — capturing first-order (mean) and second-order (variance) statistics. For a GMM with K components:

```
FV(x) = [μ_gradient_1, σ_gradient_1, ..., μ_gradient_K, σ_gradient_K]
       dimension = 2 × K × D   (D = descriptor dimension)
```

With K=64 GMM components and D=64 (PCA-reduced SIFT), FV gives an 8192-dimensional vector that typically outperforms BoVW with K=10000 words at lower dimension.

### Hard negative mining — why it is necessary for detection SVMs (§14.4.1)
In object detection, negative windows (background patches) outnumber positives by 100,000:1. Training on all negatives is infeasible. Random negatives are too easy — the SVM margin is determined by hard examples (false positives). The mining loop:

```python
def hard_negative_mining(detector, negative_images, max_per_image=200):
    """
    Szeliski §14.4.1: mine the hardest false positives to add to SVM training.
    Run the current detector on negative images; high-confidence false positives
    become the new hard negatives for the next SVM training iteration.
    """
    hard_negatives = []
    for img in negative_images:
        # Run sliding window at all scales
        detections = detector.detect(img, score_threshold=0.0)
        # Sort by confidence descending; take top hits as hard negatives
        detections.sort(key=lambda d: d.score, reverse=True)
        hard_negatives.extend([d.feature_vector for d in detections[:max_per_image]])
    return hard_negatives
```

### Transfer learning — the layer-by-layer feature hierarchy (§14.7)
The book explains that deep networks learn a **compositional feature hierarchy**: early layers detect edges and colors, middle layers detect textures and parts, late layers detect class-specific patterns. This means:
- **Freeze early layers** for small target datasets (they contain generic, reusable features)
- **Fine-tune all layers** for large target datasets with distribution shift from ImageNet
- **Replace only the head** when the domain is similar (ImageNet → medical X-ray: fine-tune; ImageNet → satellite: fine-tune all)

```python
import torch.nn as nn
from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights

def build_transfer_model(num_classes, freeze_until_layer='features.5'):
    """
    Layer-selective freezing following Szeliski §14.7 analysis.
    EfficientNet_B3: features.0-8 are the MBConv blocks;
    freeze up to block 5, fine-tune 6-8 + classifier.
    """
    model = efficientnet_b3(weights=EfficientNet_B3_Weights.IMAGENET1K_V1)
    freezing = True
    for name, param in model.named_parameters():
        if freeze_until_layer in name:
            freezing = False
        param.requires_grad = not freezing

    # Replace classification head
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, num_classes)
    )
    return model
```

## Common Pitfalls
| Pitfall | Why (per the book) | Fix |
|---------|-------------------|-----|
| Skipping IDF weighting in BoVW | Common background words dominate the histogram and drown out discriminative words | Always apply TF-IDF; it typically gives 5–10% accuracy improvement |
| Fine-tuning all layers on tiny datasets (<1000 images) | Early layer gradients corrupt generic low-level features | Freeze all but the last 1–2 blocks; use aggressive augmentation |
| L2 normalizing features before SVM | SVM with RBF kernel already handles scaling internally; L2 norm can hurt for sparse histograms | Use L1 norm for histogram features; L2 for dense CNN features |
| Using top-1 accuracy on imbalanced test sets | A single dominant class inflates accuracy | Report per-class accuracy and macro-average F1 |

## Connections
- **feature_detection.md** — SIFT descriptors are the input to BoVW vocabulary building
- **segmentation.md** — recognition backbone is reused as the encoder in FCN/DeepLab segmentation models
