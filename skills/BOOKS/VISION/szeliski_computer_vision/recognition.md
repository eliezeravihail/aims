# Recognition
**Source:** Computer Vision: Algorithms and Applications — Szeliski (szeliski.org/Book) | tier_1a

## Core Concept
Recognition maps an image (or region) to a category. The evolution: hand-crafted features (SIFT + BoW + SVM) → deep CNN features → end-to-end trained classifiers. Transfer learning from ImageNet-pretrained models is the standard starting point.

## Key Definitions
- **Bag of Visual Words (BoVW):** cluster SIFT descriptors into a vocabulary; represent image as histogram of visual word counts; classify with SVM
- **Top-1 / Top-5 accuracy:** fraction of test images where correct label is the first / in the top-5 predictions
- **Transfer learning:** use pretrained CNN weights as feature extractor; fine-tune last N layers on target task
- **Data augmentation:** random crop, flip, color jitter, mixup — reduces overfitting without more data
- **Softmax cross-entropy:** standard loss for multi-class classification

## Pattern

```python
import torch
import torchvision.models as models
import torchvision.transforms as T

# Transfer learning — fine-tune ResNet50
model = models.resnet50(weights='IMAGENET1K_V2')
# Freeze all layers except the final classifier
for param in model.parameters():
    param.requires_grad = False
model.fc = torch.nn.Linear(model.fc.in_features, num_classes)  # replace head

optimizer = torch.optim.AdamW(model.fc.parameters(), lr=1e-3)

# Standard ImageNet preprocessing
transform = T.Compose([
    T.Resize(256), T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
```

## Common Pitfalls
| Pitfall | Fix |
|---------|-----|
| Fine-tuning all layers on tiny dataset | Freeze backbone; only train head |
| Forgetting ImageNet normalization | Model outputs garbage without correct mean/std |
| No data augmentation on small datasets | Add random flips, crops, color jitter |
| Evaluating on training distribution only | Always test on held-out set with same preprocessing |

## Connections
- **segmentation.md** — recognition backbones (ResNet, EfficientNet) are reused as segmentation encoders
- **feature_detection.md** — BoVW pipeline uses SIFT as feature extractor
