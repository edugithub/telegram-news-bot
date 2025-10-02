import os, logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from newspaper import Article, Config

BOT_TOKEN = os.environ["BOT_TOKEN"]

logging.basicConfig(level=logging.INFO)

UA = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)
cfg = Config()
cfg.browser_user_agent = UA
cfg.request_timeout = 15

def analyze_content(text: str):
    t = text.lower()
    trigger, impact, suggestion = "General", "Medio", "Observar"
    if "fda approval" in t:
        trigger, impact, suggestion = "FDA approval", "ALTO", "Posible entrada rápida"
    elif "merger" in t or "acquisition" in t:
        trigger, impact, suggestion = "M&A", "ALTO", "El adquirido sube; el comprador puede caer"
    elif "earnings beat" in t:
        trigger, impact, suggestion = "Earnings beat", "ALTO", "Posible subida en pre/after-market"
    elif "earnings miss" in t or "profit warning" in t:
        trigger, impact, suggestion = "Profit warning", "ALTO", "Posible caída fuerte"
    elif "crypto crash" in t:
        trigger, impact, suggestion = "Crypto crash", "ALTO", "Riesgo de desplome"
    return trigger, impact, suggestion

def extract_urls(update: Update):
    urls = []
    if update.message:
        text = update.message.text or ""
        entities = update.message.entities or []
        for e in entities:
            if e.type == "url":
                urls.append(text[e.offset:e.offset+e.length])
            elif e.type == "text_link" and getattr(e, "url", None):
                urls.append(e.url)
    return urls

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    urls = extract_urls(update)
    if not urls:
        return
    url = urls[0]
    await update.message.reply_text(f"🔎 Leyendo noticia...\n{url}")
    try:
        art = Article(url, config=cfg)
        art.download()
        art.parse()
        content = (art.text or "")[:2000]
        trigger, impact, suggestion = analyze_content(content)
        title = art.title or "Sin título"
        resumen = f"""⚡ Trigger: {trigger}
📊 Impacto esperado: {impact}
✅ Sugerencia: {suggestion}
📰 Título: {title}"""
        await update.message.reply_text(resumen)
    except Exception as e:
        await update.message.reply_text(f"⚠️ No pude analizar la noticia: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
