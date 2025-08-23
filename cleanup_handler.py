from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from sheet_manager import log_cleanup_submission, get_user_data

# States for conversation
LOCATION, MEDIA, CONFIRMATION = range(3)

# Store user submissions in a dictionary
cleanup_submissions = {}

def register_cleanup_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == '🗑️ Community Cleanup')
    def start_cleanup(message):
        chat_id = message.chat.id
        description = (
            "♻️ Welcome to the Community Cleanup Initiative! ♻️\n\n"
            "Help us make our communities cleaner and earn rewards! "
            "Submit a photo or video of a cleaned-up area to participate.\n\n"
            "✨ Benefits for you: ✨\n"
            "• Earn bonus points for every valid submission.\n"
            "• Contribute to a cleaner environment.\n"
            "• Get featured in our community highlights.\n\n"
            "Ready to make a difference?"
        )
        bot.send_message(chat_id, description)
        cleanup_submissions[chat_id] = {}
        bot.send_message(chat_id, "Please provide the location of the cleanup. Type /cancel to abort.")
        bot.register_next_step_handler(message, location_handler, bot)

    def location_handler(message, bot):
        chat_id = message.chat.id
        if message.text == '/cancel':
            bot.send_message(chat_id, "Submission cancelled.")
            if chat_id in cleanup_submissions:
                del cleanup_submissions[chat_id]
            return
        
        cleanup_submissions[chat_id]['location'] = message.text
        bot.send_message(chat_id, "Great! Now, please upload a photo or video of the clean area. Type /cancel to abort.")
        bot.register_next_step_handler(message, media_handler, bot)

    def media_handler(message, bot):
        chat_id = message.chat.id
        if message.text == '/cancel':
            bot.send_message(chat_id, "Submission cancelled.")
            if chat_id in cleanup_submissions:
                del cleanup_submissions[chat_id]
            return

        media_id = None
        if message.photo:
            media_id = message.photo[-1].file_id
        elif message.video:
            media_id = message.video.file_id
        else:
            bot.send_message(chat_id, "That doesn't seem to be a photo or video. Please upload a valid file or type /cancel to abort.")
            bot.register_next_step_handler(message, media_handler, bot)
            return

        cleanup_submissions[chat_id]['media_id'] = media_id

        location = cleanup_submissions[chat_id]['location']
        confirmation_message = f"Please confirm your submission:\n\nLocation: {location}\nMedia: [Attached]"

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Confirm", callback_data="confirm_cleanup"),
                   InlineKeyboardButton("Cancel", callback_data="cancel_cleanup"))

        bot.send_message(chat_id, confirmation_message, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data in ['confirm_cleanup', 'cancel_cleanup'])
    def confirmation_handler(call):
        chat_id = call.message.chat.id
        if call.data == 'confirm_cleanup':
            user_data = get_user_data(chat_id)
            submission = cleanup_submissions[chat_id]
            log_cleanup_submission(
                user_id=chat_id,
                name=user_data['Name'],
                username=user_data['Username'],
                location=submission['location'],
                media_url=submission['media_id']
            )
            bot.send_message(chat_id, "Thank you! Your submission has been recorded.")
            # Notify admins
            # (You can add admin notification logic here)
        else:
            bot.send_message(chat_id, "Submission cancelled.")

        if chat_id in cleanup_submissions:
            del cleanup_submissions[chat_id]
        bot.answer_callback_query(call.id)