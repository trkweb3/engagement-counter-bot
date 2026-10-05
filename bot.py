import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Stores the configured engagement topic for each group
engagement_topics = {}

# Stores unique users who submitted an X/Twitter link
participants = {}

X_LINK_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|twitter\.com)/[^\s]+",
    re.IGNORECASE
)


def get_group_key(chat_id):
    return chat_id


def get_participants(chat_id):
    if chat_id not in participants:
        participants[chat_id] = set()
    return participants[chat_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Engagement Counter is online.\n\n"
        "Use /settopic inside the Engagement topic to configure it."
    )


async def settopic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.is_topic_message:
        await update.message.reply_text(
            "Please use /settopic inside the Engagement topic."
        )
        return

    chat_id = update.effective_chat.id
    topic_id = update.message.message_thread_id

    engagement_topics[chat_id] = topic_id

    participants[chat_id] = set()

    await update.message.reply_text(
        "✅ Engagement topic configured.\n"
        "👥 Count reset to 0.\n\n"
        "Now I will count unique users who submit X/Twitter links here."
    )


async def startsession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not update.message.is_topic_message:
        await update.message.reply_text(
            "Please use /startsession inside the Engagement topic."
        )
        return

    configured_topic = engagement_topics.get(chat_id)

    if configured_topic != update.message.message_thread_id:
        await update.message.reply_text(
            "This is not the configured Engagement topic."
        )
        return

    participants[chat_id] = set()

    await update.message.reply_text(
        "🟢 Session started!\n"
        "👥 Participants: 0"
    )


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not update.message.is_topic_message:
        await update.message.reply_text(
            "Please use /count inside the Engagement topic."
        )
        return

    configured_topic = engagement_topics.get(chat_id)

    if configured_topic != update.message.message_thread_id:
        await update.message.reply_text(
            "This is not the configured Engagement topic."
        )
        return

    total = len(get_participants(chat_id))

    await update.message.reply_text(
        f"👥 Unique participants: {total}"
    )


async def endsession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not update.message.is_topic_message:
        await update.message.reply_text(
            "Please use /endsession inside the Engagement topic."
        )
        return

    configured_topic = engagement_topics.get(chat_id)

    if configured_topic != update.message.message_thread_id:
        await update.message.reply_text(
            "This is not the configured Engagement topic."
        )
        return

    total = len(get_participants(chat_id))

    await update.message.reply_text(
        f"🔴 Session ended.\n\n"
        f"👥 Total unique participants: {total}"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    participants[chat_id] = set()

    await update.message.reply_text(
        "♻️ Engagement count reset to 0."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Only count messages inside a topic
    if not update.message.is_topic_message:
        return

    chat_id = update.effective_chat.id
    topic_id = update.message.message_thread_id

    # Only count the configured Engagement topic
    if engagement_topics.get(chat_id) != topic_id:
        return

    # Ignore bot messages
    if update.effective_user and update.effective_user.is_bot:
        return

    text = update.message.text or update.message.caption or ""

    # Check for X/Twitter link
    if not X_LINK_PATTERN.search(text):
        return

    user_id = update.effective_user.id
    user_set = get_participants(chat_id)

    # Count each user only once
    if user_id not in user_set:
        user_set.add(user_id)

        await update.message.reply_text(
            f"✅ Counted!\n👥 Participants: {len(user_set)}"
        )


def main():
    import os

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
            filters.TEXT | filters.CAPTION,
            handle_message
        )
    )

    print("Engagement Counter is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
