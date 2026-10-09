import os
import re
from telegram import Update, LinkPreviewOptions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

engagement_topics = {}
participants = {}

X_LINK_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|twitter\.com)/[^\s]+",
    re.IGNORECASE,
)


def get_participants(chat_id):
    if chat_id not in participants:
        participants[chat_id] = set()
    return participants[chat_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Engagement Counter is online.\n"
        "Use /settopic inside the Engagement topic to configure it."
    )


async def settopic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.is_topic_message:
        await update.message.reply_text(
            "Please use /settopic inside the Engagement topic."
        )
        return

    chat_id = update.effective_chat.id
    engagement_topics[chat_id] = message.message_thread_id
    participants[chat_id] = set()

    await message.reply_text(
        "✅ Engagement topic configured.\n"
        "👥 Count reset to 0."
    )


async def startsession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = update.effective_chat.id

    if not message or not message.is_topic_message:
        await update.message.reply_text(
            "Please use /startsession inside the Engagement topic."
        )
        return

    if engagement_topics.get(chat_id) != message.message_thread_id:
        await message.reply_text(
            "This is not the configured Engagement topic."
        )
        return

    participants[chat_id] = set()
    await message.reply_text("🟢 Session started!\n👥 Participants: 0")


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = update.effective_chat.id

    if not message or not message.is_topic_message:
        await update.message.reply_text(
            "Please use /count inside the Engagement topic."
        )
        return

    if engagement_topics.get(chat_id) != message.message_thread_id:
        await message.reply_text(
            "This is not the configured Engagement topic."
        )
        return

    await message.reply_text(
        f"👥 Unique participants: {len(get_participants(chat_id))}"
    )


async def endsession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = update.effective_chat.id

    if not message or not message.is_topic_message:
        await update.message.reply_text(
            "Please use /endsession inside the Engagement topic."
        )
        return

    if engagement_topics.get(chat_id) != message.message_thread_id:
        await message.reply_text(
            "This is not the configured Engagement topic."
        )
        return

    await message.reply_text(
        f"🔴 Session ended.\n"
        f"👥 Total unique participants: "
        f"{len(get_participants(chat_id))}"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    participants[chat_id] = set()

    await update.message.reply_text(
        "♻️ Engagement count reset to 0."
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.message

    if not message or not message.is_topic_message:
        return

    user = update.effective_user
    if not user or user.is_bot:
        return

    chat_id = update.effective_chat.id
    topic_id = message.message_thread_id

    if engagement_topics.get(chat_id) != topic_id:
        return

    text = message.text or message.caption or ""

    if not X_LINK_PATTERN.search(text):
        return

    # Count this member only once.
    user_set = get_participants(chat_id)
    is_new_participant = user.id not in user_set
    user_set.add(user.id)

    try:
        # Delete the original message and repost without a preview.
        await message.delete()

        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=topic_id,
            text=text,
            link_preview_options=LinkPreviewOptions(
                is_disabled=True
            ),
        )

        if is_new_participant:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=topic_id,
                text=f"✅ Counted!\n👥 Participants: {len(user_set)}",
            )

    except Exception as error:
        print(f"Could not process link: {error}")


def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise RuntimeError("BOT_TOKEN is not configured.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settopic", settopic))
    app.add_handler(CommandHandler("startsession", startsession))
    app.add_handler(CommandHandler("count", count))
    app.add_handler(CommandHandler("endsession", endsession))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
            handle_message,
        )
    )

    print("Engagement Counter is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
