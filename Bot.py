import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext

BOT_TOKEN = os.getenv("7303792607:AAGZVHXBVVcXMN2KFtmy8buF42PnSWMwsx8")

# Dictionary to store user file and name state
user_data = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hi! Forward a file to me and I’ll help you rename it.")

def handle_file(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    file = update.message.document or update.message.video or update.message.audio

    if file is None:
        update.message.reply_text("Please forward a document, audio, or video file.")
        return

    file_id = file.file_id
    file_name = file.file_name
    file_ext = os.path.splitext(file_name)[1] if file_name else ""

    user_data[user_id] = {
        "file_id": file_id,
        "file_ext": file_ext
    }

    update.message.reply_text("Send me the new file name (without extension):")

def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id not in user_data or "file_id" not in user_data[user_id]:
        update.message.reply_text("Please forward a file first.")
        return

    new_name = update.message.text.strip()
    if not new_name:
        update.message.reply_text("Name cannot be empty. Try again.")
        return

    user_data[user_id]["new_name"] = new_name

    keyboard = [
        [
            InlineKeyboardButton("✅ Proceed", callback_data="proceed"),
            InlineKeyboardButton("✏️ Edit", callback_data="edit")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f"New filename will be:\n`{new_name + user_data[user_id]['file_ext']}`", parse_mode="Markdown", reply_markup=reply_markup)

def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    if user_id not in user_data:
        query.edit_message_text("Session expired. Please send the file again.")
        return

    if data == "edit":
        query.edit_message_text("Okay, send the new file name (without extension):")
    elif data == "proceed":
        file_id = user_data[user_id]["file_id"]
        new_name = user_data[user_id]["new_name"]
        file_ext = user_data[user_id]["file_ext"]
        new_filename = new_name + file_ext

        file = context.bot.get_file(file_id)
        file.download(custom_path=new_filename)

        with open(new_filename, 'rb') as f:
            query.message.reply_document(document=InputFile(f, filename=new_filename))

        os.remove(new_filename)
        query.edit_message_text(f"Here is your renamed file: `{new_filename}`", parse_mode="Markdown")
        del user_data[user_id]

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document | Filters.video | Filters.audio, handle_file))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(CallbackQueryHandler(handle_buttons))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()