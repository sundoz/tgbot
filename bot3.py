#!/usr/bin/env python
"""Telegram bot for collecting peoples problems"""

import os
import logging
import traceback
import html
import json


from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
load_dotenv()
TOKEN = os.getenv("TOKEN")
DEVELOPER_CHAT_ID = os.getenv("DEVELOPERS_CHAT")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CATEGORY, DESCRIPTION, CONTACT_INFO, CONTACT_NUMBER = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts conversetion and asks problem category"""
    reply_keyboard = [["ЖКХ", "Дороги", "Личные долги", "Друге проблемы"]]

    await update.message.reply_text(
        "Выберете категорию проблемы или введите /cancel чтобы закончить диалог\n\n",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,\
                  input_field_placeholder='Выберете что вас беспокоит'
        ),
    )

    return CATEGORY


async def problem_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected category and ask to write info about situation"""
    user = update.message.from_user
    logger.info("Problem of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "Отлично! Опишите развернуто ситуацию с которой вы столкнулись",
        reply_markup=ReplyKeyboardRemove(),
    )

    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores """
    user = update.message.from_user
    # description_text = update.message.text
    logger.info("Propblem description of %s: %s", user.name, update.message.text)
    await update.message.reply_text(
        "Спасибо за развернутое объяснение, далее прошу вас заполнить\
              информацию о вас и предоставить контактные данные,"
        "чтобы кандидат мог с вами связаться\n"
        "Если вы не хотите давать контактные данные введите /skip\n"
        "Введите ваше полное имя и номер мобильного телефона"
    )

    return CONTACT_INFO




async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the data about user and end the conversation"""
    user = update.message.from_user
    logger.info("Contact data of %s tg nick %s: %s", user.full_name, user.name, update.message.text)
    await update.message.reply_text(
        "Спасибо большое за [чтото]"
    )

    return ConversationHandler.END

async def number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the data about user and end the conversation"""
    user = update.message.from_user
    # number = update.message.text
    logger.info("Contact data of %s tg nick %s: %s", user.full_name, user.name, update.message.text)
    await update.message.reply_text(
        "Спасибо большое за [чтото]"
    )

    return ConversationHandler.END


async def skip_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the location and asks for info about the user."""
    user = update.message.from_user
    logger.info("User %s did not send a info.", user.username)
    await update.message.reply_text(
        "Спасибо что сообщили о проблеме."
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Если хотите начать напишите /start", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END



async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )


def main() -> None:
    """Run the bot."""
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & \
                                       ~(filters.COMMAND | filters.Regex('^Cтоп$|^стоп$')),\
                                          problem_category)],
            DESCRIPTION: [MessageHandler(filters.TEXT & \
                                         ~(filters.COMMAND | filters.Regex('^Cтоп$|^стоп$')),\
                                              description)],
            CONTACT_INFO: [
                MessageHandler(filters.TEXT, contact_info),
                CommandHandler("skip", skip_contact_info),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.Regex('^Cтоп$|^стоп$'),cancel)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()