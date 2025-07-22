import time
import os
from telegram import Bot

# Lee las variables del entorno desde Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

def enviar_picks():
    mensaje = (
        "🔥 *PICKS SERPICKS DEL DÍA* 🔥\n\n"
        "✅ *Pick 1:* Real Madrid gana\n"
        "✅ *Pick 2:* Menos de 2.5 goles en el partido\n"
        "✅ *Pick 3:* Ambos anotan: NO en el juego\n"
        "📊 Análisis completo en camino.\n\n"
        "💵 *Parlay del día:* +350\n"
        "🕒 Enviado automáticamente por SERPICKS\n"
        "#Confianza #Análisis #Ganancias"
    )
    bot.send_message(chat_id=CHAT_ID, text=mensaje, parse_mode="Markdown")

if __name__ == "__main__":
    enviar_picks()