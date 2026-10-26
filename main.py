#!/usr/bin/env python3
"""
AI Vibe (@ai.vibe.1.0) Telegram Bot - Ultra Fast Non-blocking Poller
"""

import time
import csv
import io
import os
import re
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

# Simple HTTP health-check server for Render.com free tier
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"AI Vibe Telegram Bot is Alive & Running 24/7! \xf0\x9f\x9a\x80")
    
    def log_message(self, format, *args):
        pass  # Quiet logs

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"🌐 Health-check server listening on port {port} (Render ready)", flush=True)
    server.serve_forever()

# ==============================================================================
# ⚙️ CONFIGURATION
# ==============================================================================
BOT_TOKEN = "8989393835:AAFRJoHZC5d3NcH02rPGgwilVJ9fsjxHA1A"
BOT_USERNAME = "amin_aivibe_bot"
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1P6ygQ1ApaqnEH4ZnqY2L9b4PFsN8eV_oBJbcZgPDzR8/export?format=csv"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Built-in instant-response prompts (ensures 0.05s response time)
cached_prompts = {
    "1": {
        "id": "1",
        "model": "woman",
        "prompt": "100% exact facial structure and bone geometry, perfectly rendered symmetrical eyes, natural iris texture, crisp pupil definition, realistic corneal light reflections (catchlights), natural eyelids and micro-expressions. Close-up environmental portrait of the female subject, no hijab. Visible wardrobe includes the top of a black silk camisole and gold hoop earrings. She is leaning slightly against a glass storefront reflecting blurred neon lights. Direct eye contact with a soft, confident gaze. Lighting is dominated by a nearby warm yellow neon sign creating a natural Rembrandt light pattern on her face. Shot on Sony A7III, 85mm f/1.8 lens, shallow depth of field, Natural Kodak Portra 400 Color Science, visible skin pores and micro-imperfections, organic film grain, 4:5 aspect ratio.",
        "ar": "4:5"
    },
    "2": {
        "id": "2",
        "model": "woman",
        "prompt": "100% exact facial structure and bone geometry matching reference, perfectly rendered symmetrical eyes, natural iris texture, crisp pupil definition, realistic corneal light reflections (catchlights), natural eyelids and micro-expressions, zero distortion in gaze direction. The subject is a female lying gracefully in a meadow of infinite white daisies and baby's breath. She is wearing a premium saffron-yellow silk-chiffon midi dress with intricate pleated bodice details and delicate fluttering cap sleeves. Her wardrobe includes a thin 18k gold layered necklace with a tiny raw emerald pendant, gold minimalist hoop earrings, and a vintage brown leather-strap watch on her left wrist. On her fingers are thin hammered gold bands. Beside her on the grass lie hand-crafted tan leather flat sandals. The environment is a lush field of deep olive greens and rich brown earth visible between the flowers. Captured from a direct overhead bird's-eye view using a Smartphone Camera (Standard Android) lens, f/1.8 aperture, 4:5 aspect ratio. High-end editorial style with Earthy Organic Tones, olive greens, rich browns, and warm neutral ambient illumination. Natural volumetric light falloff, authentic light diffusion, visible skin texture, and micro-imperfections for masterpiece realism.",
        "ar": "4:5"
    },
    "3": {
        "id": "3",
        "model": "woman",
        "prompt": "100% facial similarity structure, intricate facial micro-features, natural pores, realistic skin texture, an extreme close-up macro portrait of a female, one eye visible peeking through thick wavy chestnut-brown hair cascading across the face, long eyelashes catching a warm golden sunlight glow, dusty rose matte lipstick on a visible corner of the mouth, tanned sun-kissed skin with visible freckles. She is wearing a vintage-washed oversized beige linen button-down shirt with a visible coarse weave and mother-of-pearl buttons, paired with high-waisted relaxed-fit raw denim jeans in faded indigo with double-stitched seams, and worn-in brown leather huarache sandals with hand-stitched details. Faded Film (Retro muted) color science, cinematic raw 35mm film texture, slight camera tilt, golden light leaks, nostalgic atmosphere. iPhone Latest Model computational photography, 4:5 aspect ratio, natural ambient environmental lighting, soft shadow diffusion, authentic lens refractions, no studio lighting, documentary-grade realism.",
        "ar": "4:5"
    },
    "4": {
        "id": "4",
        "model": "man",
        "prompt": "100% exact facial structure and bone geometry, perfectly rendered symmetrical eyes, natural iris texture, crisp pupil definition, realistic corneal light reflections (catchlights), natural eyelids and micro-expressions. Subject: Confident male in a low-angle worm's-eye view looking up, leaning casually against a matte-black custom-built motorcycle. Wardrobe: Oversized black heavy-cotton t-shirt with a bold white 'SHUT UP' graphic print, baggy distressed light-blue ripped denim jeans with frayed knee holes, crisp white leather Nike Air Force 1 sneakers, and matte black round metal-frame sunglasses. Accessories include a thin silver curb chain and a minimalist silver band on the right ring finger. Environment: A weathered vintage 1960s gas station with rusted pumps and olive green signage. Lighting: Soft global illumination, Earthy Organic Tones, rich browns, warm neutral ambient light with subtle lens flares. Technical: Shot on iPhone 15 Pro Max, 35mm film grain, Ilford HP5 Plus contrast, cinematic raw quality, 4:5 aspect ratio.",
        "ar": "4:5"
    },
    "5": {
        "id": "5",
        "model": "man",
        "prompt": "100% facial similarity to the reference image, high-fidelity facial features, calm and confident male subject looking directly up at the camera lens, top-down high-angle perspective from above a slammed custom Mercedes-Benz car. The subject is wearing a loose oversized black t-shirt, baggy charcoal grey washed distressed denim jeans, crisp white Air Force 1 sneakers, and matte black round sunglasses. Natural ambient light, subtle light leaks, realistic shadow transition, soft global illumination, shot on location. Micro-imperfections, authentic skin texture, realistic dust particles, imperfectly natural hair, unposed authentic environment. Shot on iPhone Latest Model (Computational Photography), (Ilford HP5 Plus contrast), Cinematic Raw, 35mm film grain, micro-texture, high-fidelity urban grit.",
        "ar": "4:5"
    }
}

def sync_sheets_in_background():
    """Background worker to update prompts without freezing Telegram responses."""
    global cached_prompts
    while True:
        try:
            url = f"{GOOGLE_SHEET_CSV_URL}&_t={int(time.time())}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                f = io.StringIO(resp.text)
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:
                    headers = [h.strip().lower() for h in rows[0]]
                    id_idx = headers.index("id") if "id" in headers else 0
                    prompt_idx = headers.index("prompt") if "prompt" in headers else 2
                    model_idx = headers.index("model") if "model" in headers else 1

                    new_dict = {}
                    for r in rows[1:]:
                        if len(r) > max(id_idx, prompt_idx):
                            item_id = str(r[id_idx]).strip()
                            prompt_val = str(r[prompt_idx]).strip()
                            model_val = str(r[model_idx]).strip() if len(r) > model_idx else "AI Portrait"
                            if item_id and prompt_val:
                                new_dict[item_id] = {
                                    "id": item_id,
                                    "model": model_val,
                                    "prompt": prompt_val,
                                    "ar": "4:5" if "4:5" in prompt_val else "--ar 4:5"
                                }
                    if new_dict:
                        cached_prompts.update(new_dict)
        except Exception:
            pass
        
        time.sleep(60)

def send_message(chat_id, text, reply_markup=None):
    """Send text message with Telegram Markdown formatting."""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=8)
    except Exception as e:
        print(f"❌ Send error: {e}", flush=True)

def format_prompt_message(prompt_data):
    """Format prompt with 1-tap copyable code block in Telegram."""
    item_id = prompt_data["id"]
    model = prompt_data["model"]
    prompt = prompt_data["prompt"]
    ar = prompt_data["ar"]

    msg = (
        f"🎨 *پرامپت اختصاصی عکس شماره #{item_id}*\n"
        f"👤 *دسته:* {model} | 📐 *نسبت:* {ar}\n\n"
        f"👇 *برای کپی پرامپت، یک بار روی کادر زیر ضربه بزنید:*\n\n"
        f"```\n{prompt}\n```\n\n"
        f"💡 *راهنما:* متن کپی‌شده را مستقیماً در Midjourney یا ابزار AI خود پیست کنید.\n"
        f"برای دریافت پرامپت هر عکس دیگری، فقط شمارهٔ آن (مثلاً 1 تا 30) را بفرستید! ✨"
    )
    return msg

def get_inline_keyboard(prompt_id):
    return {
        "inline_keyboard": [
            [
                {"text": "🌐 مشاهده در وب‌سایت", "url": f"https://aivibe10.netlify.app/?id={prompt_id}"},
                {"text": "📸 اینستاگرام ما", "url": "https://instagram.com/ai.vibe.1.0"}
            ]
        ]
    }

def handle_update(update):
    if "message" not in update or "text" not in update["message"]:
        return
    
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_text = msg["text"].strip()
    user_name = msg.get("from", {}).get("first_name", "عزیز")

    print(f"📩 [{user_name}] ({chat_id}): {user_text}", flush=True)

    # 1. /start command or Deep-links (e.g. /start 5)
    if user_text.startswith("/start"):
        parts = user_text.split()
        if len(parts) > 1 and parts[1].isdigit():
            req_id = parts[1]
            if req_id in cached_prompts:
                send_message(chat_id, format_prompt_message(cached_prompts[req_id]), get_inline_keyboard(req_id))
                print(f"⚡ Sent prompt #{req_id} to {chat_id}", flush=True)
                return

        welcome_msg = (
            f"سلام {user_name} عزیز! به ربات رسمی *AI Vibe* خوش آمدید ✨\n\n"
            f"❓ *پرامپت کدام عکس پیج را می‌خواهید؟*\n\n"
            f"کافیست فقط *شمارهٔ عکس* را برایم بفرستید (مثلاً: `1`، `5`، یا `20`).\n\n"
            f"📌 شماره عکس مورد نظرتان را همین الان ارسال کنید 👇"
        )
        send_message(chat_id, welcome_msg)
        print(f"⚡ Sent welcome to {chat_id}", flush=True)
        return

    # 2. Number extracted from input (e.g. "5", "#5", "عکس 5")
    digits = re.findall(r'\d+', user_text)
    if digits:
        req_id = digits[0]
        if req_id in cached_prompts:
            send_message(chat_id, format_prompt_message(cached_prompts[req_id]), get_inline_keyboard(req_id))
            print(f"⚡ Sent prompt #{req_id} to {chat_id}", flush=True)
            return
        else:
            available = ", ".join(list(cached_prompts.keys())[:10])
            send_message(
                chat_id, 
                f"❌ پرامپت شماره #{req_id} هنوز در آرشیو ثبت نشده است.\n"
                f"شماره‌های فعال در حال حاضر: {available}...\n"
                f"لطفاً شمارهٔ دیگری را امتحان کنید!"
            )
            print(f"⚡ Sent not-found for #{req_id} to {chat_id}", flush=True)
            return

    # 3. Keyword search (e.g. "mercedes", "sony", "gas station")
    q = user_text.lower()
    matches = [p for p in cached_prompts.values() if q in p["prompt"].lower() or q in p["model"].lower()]
    if matches:
        first = matches[0]
        send_message(
            chat_id, 
            f"🔎 پرامپت مرتبط با «{user_text}» (شماره #{first['id']}) پیدا شد:\n\n" + 
            format_prompt_message(first), 
            get_inline_keyboard(first["id"])
        )
        print(f"⚡ Sent keyword #{first['id']} to {chat_id}", flush=True)
    else:
        send_message(
            chat_id,
            "❓ متوجه نشدم! لطفاً فقط *شمارهٔ عکس* را بفرستید (مثلاً `1`، `3` یا `5`)."
        )

def main():
    print(f"🚀 AI Vibe Telegram Bot (@{BOT_USERNAME}) running...", flush=True)
    
    # Start Render health-check server thread
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Start background Google Sheets updater thread
    threading.Thread(target=sync_sheets_in_background, daemon=True).start()

    # Clear old webhook if any
    try:
        requests.get(f"{TELEGRAM_API_URL}/deleteWebhook", timeout=5)
    except Exception:
        pass

    offset = None
    while True:
        try:
            params = {"timeout": 0}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(f"{TELEGRAM_API_URL}/getUpdates", params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    handle_update(update)
            elif resp.status_code == 401:
                print("❌ Invalid BOT_TOKEN!", flush=True)
                time.sleep(10)
        except Exception as e:
            pass
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()
