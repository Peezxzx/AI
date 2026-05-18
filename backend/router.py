from typing import Dict

MODELS = {
    "cheap": "z-ai/glm-4.5-air:free",
    "reasoning": "deepseek/deepseek-chat-v3",
    "planning": "tencent/hunyuan",
    "coding": "openrouter/owl-alpha",
    "vision": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "vision_alt": "qwen/qwen-2-vl-7b-instruct:free",
    "vision_mini": "google/gemini-2.0-flash-lite-001:free"
}

# Vision-related keywords for routing
VISION_KEYWORDS = [
    "image", "photo", "picture", "รูป", "ภาพ", "vision",
    "see", "look", "scan", "screenshot", "camera", "หน้าจอ",
    "diagram", "chart", "graph", "ใบหน้า", "วิเคราะห์รูป",
    "อธิบายรูป", "บนรูป", "ในรูป"
]

def select_model(task: str) -> Dict:
    task = task.lower()

    # Vision/image analysis tasks
    if any(kw in task for kw in VISION_KEYWORDS):
        return {
            "type": "vision",
            "model": MODELS["vision"]
        }

    if "code" in task:
        return {
            "type": "coding",
            "model": MODELS["coding"]
        }

    elif "plan" in task:
        return {
            "type": "planning",
            "model": MODELS["planning"]
        }

    elif "analyze" in task:
        return {
            "type": "reasoning",
            "model": MODELS["reasoning"]
        }

    return {
        "type": "cheap",
        "model": MODELS["cheap"]
    }

def get_vision_model(prefer: str = "primary") -> str:
    """Get a vision-capable model.
    
    prefer: 'primary' (best), 'alt' (lighter), 'mini' (fastest)
    """
    if prefer == "alt":
        return MODELS["vision_alt"]
    elif prefer == "mini":
        return MODELS["vision_mini"]
    return MODELS["vision"]

def list_models() -> Dict:
    """List all available models grouped by type."""
    return MODELS.copy()
