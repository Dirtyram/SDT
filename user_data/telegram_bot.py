from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from .models import User, CalorieEntry
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
import datetime
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("TOKEN")

if not TOKEN:
        raise ValueError("No TELEGRAM_BOT_TOKEN environment variable found")

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Use sync_to_async to handle ORM calls
    user, created = await sync_to_async(User.objects.get_or_create)(
        telegram_id=chat_id, 
        defaults={'name': update.effective_user.first_name}
    )
    
    await update.message.reply_text(
        f"Welcome {user.name}! Use /add to log your meals and /summary to see your daily calories."
    )

async def set_limit(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /set_limit <calories>")
        return

    calorie_limit = int(context.args[0])

    user = await sync_to_async(lambda: User.objects.filter(telegram_id=chat_id).first())()
    if not user:
        await update.message.reply_text("Please use /start first.")
        return

    user.calorie_limit = calorie_limit
    await sync_to_async(user.save)()

    await update.message.reply_text(f"Calorie limit set to {calorie_limit} kcal.")

async def add(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Fetch user synchronously using sync_to_async
    user = await sync_to_async(lambda: User.objects.filter(telegram_id=chat_id).first())()
    if not user:
        await update.message.reply_text("Please use /start first.")
        return

    try:
        # Parse food and calories from the message
        food, calories = ' '.join(context.args).rsplit(' ', 1)

        # Create the CalorieEntry synchronously
        await sync_to_async(CalorieEntry.objects.create)(
            user=user, food=food, calories=int(calories)
        )
        await update.message.reply_text(f"Added: {food} with {calories} calories.")
    except ValueError:
        await update.message.reply_text("Usage: /add <food> <calories>")

async def summary(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    today = datetime.date.today()

    user = await sync_to_async(lambda: User.objects.filter(telegram_id=chat_id).first())()
    if not user:
        await update.message.reply_text("Please use /start first.")
        return

    entries = await sync_to_async(lambda: list(CalorieEntry.objects.filter(user=user, date=datetime.date.today())))()
    total_calories = sum(entry.calories for entry in entries)

    if entries:
        entry_details = "\n".join([f"{entry.food}: {entry.calories} kcal" for entry in entries])
    else:
        entry_details = "No entries for today."

    remaining_calories = user.calorie_limit - total_calories if user.calorie_limit else "No limit set"
    await update.message.reply_text(
        f"Summary for {today}:\n\n"
        f"Entries:\n{entry_details}\n\n"
        f"Today's total calories: {total_calories} kcal\n"
        f"Your current limit is {user.calorie_limit} kcal\n"
        f"Remaining calories: {remaining_calories} kcal"
    )

def main():
    # Create the application instance
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CommandHandler("set_limit", set_limit))
    # Start the bot
    application.run_polling()
