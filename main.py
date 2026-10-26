#!/usr/bin/env python3
"""
AI Vibe (@ai.vibe.1.0) Telegram Bot - Clean Photo Card Edition
Renders large photo and copyable prompt together in one single card bubble.
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

# ==============================================================================
# ⚙️ CONFIGURATION
# ==============================================================================
BOT_TOKEN = "8989393835:AAFRJoHZC5d3NcH02rPGgwilVJ9fsjxHA1A"
BOT_USERNAME = "amin_aivibe_bot"
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1P6ygQ1ApaqnEH4ZnqY2L9b4PFsN8eV_oBJbcZgPDzR8/export?format=csv"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

cached_prompts = {}

# Health check server for Render.com
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"AI Vibe Telegram Bot is Alive & Running 24/7! \xf0\x9f\x9a\x80")
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

def sync_sheets():
    """Fetch live prompts and image URLs from Google Sheets."""
    global cached_prompts
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
                image_idx = headers.index("image") if "image" in headers else -1

                new_dict = {}
                for r in rows[1:]:
                    if len(r) > max(id_idx, prompt_idx):
                        item_id = str(r[id_idx]).strip()
                        prompt_val = str(r[prompt_idx]).strip()
                        model_val = str(r[model_idx]).strip() if len(r) > model_idx else ""
                        image_val = str(r[image_idx]).strip() if image_idx != -1 and len(r) > image_idx else ""
                        
                        if item_id and prompt_val:
                            new_dict[item_id] = {
                                "id": item_id,
                                "model": model_val,
                                "prompt": prompt_val,
                                "image": image_val
                            }
                if new_dict:
                    cached_prompts = new_dict
                    print(f"🔄 Google Sheet Synced: {len(cached_prompts)} prompts ready.", flush=True)
    except Exception as e:
        print(f"Sheet fetch error: {e}", flush=True)

def background_sync_worker():
    while True:
        sync_sheets()
        time.sleep(30)

def get_inline_keyboard(prompt_id):
    return {
        "inline_keyboard": [
            [
                {"text": "🌐 مشاهده در وب‌سایت", "url": f"https://aivibe10.netlify.app/?id={prompt_id}"},
                {"text": "📸 اینستاگرام ما", "url": "https://instagram.com/ai.vibe.1.0"}
            ]
        ]
    }

def deliver_prompt(chat_id, prompt_data):
    """
    Renders photo and copyable prompt text together in ONE single card bubble.
    Removes all unwanted text clutter.
    """
    item_id = prompt_data["id"]
    model = prompt_data.get("model", "")
    prompt = prompt_data["prompt"]
    photo_url = prompt_data.get("image", "").strip()

    model_label = f" ({model})" if model else ""
    header = f"🎨 *پرامپت اختصاصی عکس #{item_id}*{model_label}"
    body = f"```\n{prompt}\n```"

    keyboard = get_inline_keyboard(item_id)

    # If photo exists, embed it seamlessly into the same message card bubble
    if photo_url.startswith("http"):
        text = f"[\u200c]({photo_url}){header}\n\n{body}"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "link_preview_options": {
                "is_disabled": False,
                "prefer_large_media": True,
                "show_above_text": True
            },
            "reply_markup": keyboard
        }
    else:
        text = f"{header}\n\n{body}"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
            "reply_markup": keyboard
        }

    try:
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=8)
    except Exception as e:
        print(f"❌ Delivery error: {e}", flush=True)

def send_simple_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=8)
    except Exception as e:
        print(f"❌ Send simple error: {e}", flush=True)

def handle_update(update):
    if "message" not in update or "text" not in update["message"]:
        return
    
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_text = msg["text"].strip()
    user_name = msg.get("from", {}).get("first_name", "عزیز")

    print(f"📩 [{user_name}] ({chat_id}): {user_text}", flush=True)

    # 1. /start command
    if user_text.startswith("/start"):
        parts = user_text.split()
        if len(parts) > 1 and parts[1].isdigit():
            req_id = parts[1]
            if req_id in cached_prompts:
                deliver_prompt(chat_id, cached_prompts[req_id])
                return

        welcome_msg = (
            f"سلام {user_name} عزیز! به ربات *AI Vibe* خوش آمدید ✨\n\n"
            f"کافیست فقط *شمارهٔ عکس* را بفرستید (مثلاً: `1`، `4` یا `5`) تا پرامپت دقیق را دریافت کنید 👇"
        )
        send_simple_message(chat_id, welcome_msg)
        return

    # 2. Number extracted from input (e.g. "4", "#4", "44")
    digits = re.findall(r'\d+', user_text)
    if digits:
        req_id = digits[0]
        if req_id in cached_prompts:
            deliver_prompt(chat_id, cached_prompts[req_id])
            print(f"⚡ Delivered prompt #{req_id} to {chat_id}", flush=True)
            return
        else:
            available = ", ".join(list(cached_prompts.keys())[:10])
            send_simple_message(
                chat_id, 
                f"❌ پرامپت شماره #{req_id} در آرشیو پیدا نشد.\nشماره‌های فعال: {available}"
            )
            return

    # 3. Keyword fallback
    q = user_text.lower()
    matches = [p for p in cached_prompts.values() if q in p["prompt"].lower() or q in p["model"].lower()]
    if matches:
        deliver_prompt(chat_id, matches[0])
    else:
        send_simple_message(chat_id, "❓ لطفاً فقط *شمارهٔ عکس* را به صورت عدد بفرستید (مثلاً `4` یا `5`).")

def main():
    print(f"🚀 AI Vibe Telegram Bot (@{BOT_USERNAME}) running...", flush=True)
    sync_sheets()
    
    threading.Thread(target=run_health_server, daemon=True).start()
    threading.Thread(target=background_sync_worker, daemon=True).start()

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
        except Exception:
            pass
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()
