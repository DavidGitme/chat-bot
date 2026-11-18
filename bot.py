import os
import asyncio
from html import escape
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)

from musica import recomendar_por_cancion, recomendar_por_artista

# ─── Configuración ──────────────────────────────────────

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ ERROR: Variable TELEGRAM_TOKEN no configurada")
    print("📌 En PowerShell: $env:TELEGRAM_TOKEN='tu_token_aqui'")
    exit(1)

MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎵 Recomendar por canción", callback_data="cancion")],
    [InlineKeyboardButton("🎤 Recomendar por artista", callback_data="artista")],
])

MENSAJE_AYUDA = (
    "🎧 <b>Bot de recomendaciones musicales</b>\n\n"
    "<b>🎵 Por canción:</b> dime una canción que te guste y te recomiendo "
    "5 parecidas, en el mismo idioma y de la misma época.\n"
    "Ejemplo: <code>/cancion Tusa Karol G</code>\n\n"
    "<b>🎤 Por artista:</b> dime un artista y te doy 5 canciones de sus mejores álbumes.\n"
    "Ejemplo: <code>/artista Soda Stereo</code>\n\n"
    "También puedes elegir una opción en los botones y luego escribir el nombre."
)

# ─── Formato de las respuestas ──────────────────────────

def texto_por_cancion(r):
    o = r["original"]
    lineas = [
        f"🎵 Canción encontrada: <b>{escape(o['titulo'])}</b> - {escape(o['artista'])} ({o['año'] or '?'})",
        f"🌍 Idioma: {escape(r['idioma'])}",
        "━━━━━━━━━━━━━━━━━━━━",
        "🎧 <b>Te recomiendo:</b>",
    ]
    for i, c in enumerate(r["recomendaciones"], start=1):
        lineas.append(
            f"{i}. <a href=\"{c['link']}\">{escape(c['titulo'])}</a> - "
            f"{escape(c['artista'])} ({c['año'] or '?'})"
        )
    return "\n".join(lineas)


def texto_por_artista(r):
    lineas = [
        f"🎤 <b>{escape(r['artista'])}</b> - canciones de sus mejores álbumes",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    for i, c in enumerate(r["canciones"], start=1):
        lineas.append(
            f"{i}. <a href=\"{c['link']}\">{escape(c['titulo'])}</a>\n"
            f"    💿 {escape(c['album'])} {('(' + c['año'] + ')') if c['año'] else ''}"
        )
    return "\n".join(lineas)

# ─── Lógica compartida ──────────────────────────────────

async def procesar(update: Update, modo: str, texto: str):
    texto = texto.strip()
    if not texto:
        await update.message.reply_text("✏️ Escribe un nombre después del comando.")
        return

    await update.message.reply_text("🔎 Buscando, dame unos segundos...")

    try:
        # Las consultas a Deezer se hacen en otro hilo para no congelar el bot
        if modo == "artista":
            r = await asyncio.to_thread(recomendar_por_artista, texto)
            if not r or not r["canciones"]:
                await update.message.reply_text("😕 No encontré ese artista. Revisa el nombre.")
                return
            respuesta = texto_por_artista(r)
        else:
            r = await asyncio.to_thread(recomendar_por_cancion, texto)
            if not r:
                await update.message.reply_text("😕 No encontré esa canción. Prueba con el nombre y el artista.")
                return
            if not r["recomendaciones"]:
                await update.message.reply_text("😕 No encontré canciones parecidas con esos filtros.")
                return
            respuesta = texto_por_cancion(r)

        await update.message.reply_text(
            respuesta, parse_mode="HTML", disable_web_page_preview=True
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text("⚠️ Ocurrió un error al buscar. Intenta de nuevo.")

# ─── Comandos ───────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MENSAJE_AYUDA, parse_mode="HTML", reply_markup=MENU)


async def cancion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await procesar(update, "cancion", " ".join(context.args))


async def artista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await procesar(update, "artista", " ".join(context.args))


async def boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    consulta = update.callback_query
    await consulta.answer()
    context.user_data["modo"] = consulta.data
    if consulta.data == "artista":
        await consulta.message.reply_text("🎤 Escribe el nombre del artista:")
    else:
        await consulta.message.reply_text("🎵 Escribe el nombre de la canción (y si quieres, el artista):")


async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Si no eligió modo, se toma como canción
    modo = context.user_data.get("modo", "cancion")
    await procesar(update, modo, update.message.text)

# ─── Inicialización ─────────────────────────────────────

def main():
    print("🎧 Bot de recomendaciones musicales activo...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", start))
    app.add_handler(CommandHandler("cancion", cancion))
    app.add_handler(CommandHandler("artista", artista))
    app.add_handler(CallbackQueryHandler(boton))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))

    print("🟢 Bot corriendo... Esperando mensajes")
    app.run_polling()


if __name__ == "__main__":
    main()
