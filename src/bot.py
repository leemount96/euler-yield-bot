import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

from uuid import uuid4

from processor.processor import Processor

load_dotenv()

processor = Processor(chain_id_list=[8453, 1923, 1], minimum_tvl=1_000_000)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Type /euler_yields to get the top Euler yield opportunities, or /merkl_yields to get the top Merkl yield opportunities.")

async def merkl_yields(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = processor.generate_merkl_opportunities_message()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def euler_yields(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = processor.generate_euler_opportunities_message()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    merkl_yields_handler = CommandHandler('merkl_yields', merkl_yields)
    application.add_handler(merkl_yields_handler)

    euler_yields_handler = CommandHandler('euler_yields', euler_yields)
    application.add_handler(euler_yields_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()
