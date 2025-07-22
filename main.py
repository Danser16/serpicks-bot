import time
from telegram import Bot

# CONFIGURA TU TOKEN Y CHAT_ID AQUI
BOT_TOKEN = "AQUI_TU_TOKEN"
CHAT_ID = "AQUI_TU_CHAT_ID"

bot = Bot(token=BOT_TOKEN)

def enviar_picks():
    mensaje = (
        "🔥 *PICKS SERPICKS DEL DÍA* 🔥\n\n"
        "✅ *Pick 1:* Real Madrid gana\n"
        "✅ *Pick 2:* Menos de 2.5 goles en el Napoli vs Juventus\n"
        "✅ *Pick 3:* Ambos anotan: NO en el PSG vs Nice\n\n"
        "📊 Análisis completo en camino.\n\n"
        "💵 *Parlay del día:* +350\n"
        "🕘 Enviado automáticamente por SERPICKS a las 9 PM.\n"
        "#Confianza #Análisis #Ganancias"
    )
    bot.send_message(chat_id=CHAT_ID, text=mensaje, parse_mode='Markdown')

if __name__ == "__main__":
    enviar_picks()
