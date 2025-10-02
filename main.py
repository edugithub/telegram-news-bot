import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import trafilatura  # usando trafilatura para evitar problemas de lxml/newspaper3k en Python 3.13

# Token desde variables de entorno en Render
BOT_TOKEN = os.environ["BOT_TOKEN"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ----------- Análisis del contenido -----------
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

# ----------- Extracción de URLs de los mensajes -----------
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

# ----------- Handler principal -----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    urls = extract_urls(update)
    if not urls:
        return

    url = urls[0]
    await update.message.reply_text(f"🔎 Leyendo noticia...\n{url}")

    try:
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded) if downloaded else ""
        trigger, impact, suggestion = analyze_content(content or "")
        resumen = f"""⚡ Trigger: {trigger}
📊 Impacto esperado: {impact}
✅ Sugerencia: {suggestion}
📰 URL: {url}"""
        await update.message.reply_text(resumen)
    except Exception as e:
        await update.message.reply_text(f"⚠️ No pude analizar la noticia: {e}")

# ----------- Entry point -----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
