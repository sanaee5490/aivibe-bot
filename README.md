# AI Vibe Telegram Bot 🤖🎨

Official Telegram Bot for `@ai.vibe.1.0` Instagram page.
Delivers AI prompts and reference photos directly from Google Sheets with 1-tap copy!

## Files
- `main.py`: Production bot script with live Google Sheets sync, photo card rendering, and Render.com health-check server.
- `requirements.txt`: Python dependencies (`requests`).

## Deployment on Render.com
1. Create a new **Web Service**.
2. Connect your GitHub repository.
3. Settings:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** Free
