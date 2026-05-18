import requests
import logging
import time
import os

logger = logging.getLogger("ai_client")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"

def ask_ai(model, prompt, retries=2):
    """Ask AI via OpenRouter with error handling and retries."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    for attempt in range(retries):
        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=120)
            data = response.json()

            # Check for API errors
            if "error" in data:
                error_msg = data.get("error", {}).get("message", str(data["error"]))
                logger.error(f"OpenRouter API error: {error_msg}")
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return f"ขออภัย ระบบ AI มีปัญหา: {error_msg}"

            # Check for choices
            if "choices" not in data or not data["choices"]:
                logger.error(f"No choices in response: {data}")
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return "ขออภัย ไม่ได้รับคำตอบจาก AI ลองใหม่อีกครั้ง"

            return data["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            logger.error(f"Timeout on attempt {attempt + 1}")
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return "⏰ AI ใช้เวลานานเกินไป ลองใหม่อีกครั้ง"

        except Exception as e:
            logger.error(f"Error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return f"❌ เกิดข้อผิดพลาด: {str(e)}"

    return "❌ ไม่สามารถติดต่อ AI ได้ ลองใหม่อีกครั้ง"


def ask_ai_vision(model, prompt, image_b64, mime_type="image/jpeg"):
    """Ask AI with image via OpenRouter (vision-capable models)."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}"
                        }
                    }
                ]
            }
        ]
    }

    for attempt in range(2):
        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=120)
            data = response.json()

            if "error" in data:
                error_msg = data.get("error", {}).get("message", str(data["error"]))
                logger.error(f"OpenRouter vision API error: {error_msg}")
                if attempt < 1:
                    time.sleep(2)
                    continue
                return f"ขออภัย ระบบ AI มีปัญหา: {error_msg}"

            if "choices" not in data or not data["choices"]:
                if attempt < 1:
                    time.sleep(2)
                    continue
                return "ขออภัย ไม่ได้รับคำตอบจาก AI"

            return data["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            if attempt < 1:
                time.sleep(2)
                continue
            return "⏰ AI ใช้เวลานานเกินไป ลองใหม่อีกครั้ง"
        except Exception as e:
            logger.error(f"Vision error: {e}")
            if attempt < 1:
                time.sleep(2)
                continue
            return f"❌ เกิดข้อผิดพลาด: {str(e)}"

    return "❌ ไม่สามารถวิเคราะห์รูปภาพได้"
