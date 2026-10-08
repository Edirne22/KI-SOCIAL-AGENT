"""Pinned CPU-only CLIP scene classification. All inference is offline.

Scores are relative similarities among the declared candidates, not calibrated
probabilities or proof of a person's identity. No faces/identities are inferred.
"""
from io import BytesIO
from pathlib import Path
import math

MODEL_ID = "openai/clip-vit-base-patch32"
MODEL_REVISION = "b527df4b30e5cc18bde1cc712833a741d2d8c362"
MODEL_PATH = "/opt/private-vision-model"
# Distractors prevent every arbitrary input becoming a birthday scene.
CANDIDATES = (
    ("trampoline_action", "action", "a photo of people jumping on trampolines in an indoor trampoline park"),
    ("group_moment", "highlights", "a photo of a group of friends posing together and smiling"),
    ("birthday_party", "home", "a photo of a birthday party with balloons and decorations"),
    ("birthday_cake", "home", "a photo of a birthday cake with candles on a table"),
    ("portrait_memory", "highlights", "a photo of a person smiling at the camera"),
    ("venue_arrival", "build", "a photo of the entrance or interior of an indoor recreation venue"),
    ("unknown", "build", "a photo of an unrelated object, document, screenshot or scenery"),
    ("unknown", "build", "a blank, dark or blurry unrecognizable image"),
)


def classify_scores(scores):
    if len(scores) != len(CANDIDATES) or any(not math.isfinite(float(x)) for x in scores):
        raise RuntimeError("PRIVATE_VISION_INVALID_SCORES")
    ranking = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    best, second = ranking[:2]
    score, margin = float(scores[best]), float(scores[best] - scores[second])
    role, beat, _ = CANDIDATES[best]
    accepted = role != "unknown" and score >= 0.30 and margin >= 0.06
    return {"story_beat": beat, "asset_role": role, "accepted": accepted,
            "model": MODEL_ID, "model_revision": MODEL_REVISION,
            "score": round(score, 6), "margin": round(margin, 6),
            "scores": {str(i): round(float(x), 6) for i, x in enumerate(scores)},
            "observations": [f"Local CLIP candidate: {role}; relative score={score:.4f}; margin={margin:.4f}"]}


class LocalSceneVision:
    def __init__(self, model_path=MODEL_PATH):
        import torch
        from transformers import CLIPModel, CLIPProcessor
        path = Path(model_path)
        if not path.is_dir() or not (path / "model.safetensors").is_file():
            raise RuntimeError("PRIVATE_LOCAL_VISION_MODEL_MISSING")
        torch.set_num_threads(1)
        self.torch = torch
        self.processor = CLIPProcessor.from_pretrained(str(path), local_files_only=True)
        self.model = CLIPModel.from_pretrained(str(path), local_files_only=True,
                                             use_safetensors=True).eval().to("cpu")
        tokens = self.processor(text=[x[2] for x in CANDIDATES], return_tensors="pt", padding=True)
        with torch.inference_mode():
            features = self.model.get_text_features(**tokens)
            self.text = features / features.norm(dim=-1, keepdim=True)

    def __call__(self, jpeg):
        from PIL import Image, ImageStat
        with Image.open(BytesIO(jpeg)) as image:
            rgb=image.convert("RGB")
            stats=ImageStat.Stat(rgb.convert("L"))
            if stats.stddev[0]<5 or stats.mean[0]<5:
                scores=[0.0]*len(CANDIDATES);scores[-1]=1.0
                verdict=classify_scores(scores)
                verdict["observations"]=["Pixel quality rejection: blank/dark/low-variance frame"]
                verdict["model"]="pixel-quality-gate"
                return verdict
            inputs = self.processor(images=rgb, return_tensors="pt")
        with self.torch.inference_mode():
            features = self.model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
            scores = (self.model.logit_scale.exp() * features @ self.text.T).softmax(dim=-1)[0]
        return classify_scores(scores.tolist())
