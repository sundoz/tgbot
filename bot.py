#!/usr/bin/env python
"""Telegram bot for collecting peoples problems"""

import os
import logging
import traceback
import html
import json
import datetime
import pytz 


from dotenv import load_dotenv
from pymongo import MongoClient, errors
from telegram import (
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove,
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    KeyboardButton,
    Update,
    WebAppInfo,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    
)

# Enable logging
logging.basicConfig(
    encoding='utf-8',
    filename="py_log.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO, 
)


logger = logging.getLogger(__name__)
load_dotenv()
TOKEN = os.getenv("TOKEN")
DEVELOPER_CHAT_ID = os.getenv("DEVELOPERS_CHAT")

URL = os.getenv('WEB_URL')
# Enable logging


logger = logging.getLogger(__name__)

MONGO = os.getenv('MONGO')
# Connect to db
client = MongoClient(MONGO, 27017)
db = client['delegations']
wishs_collection = db['wishs_collection']

CATEGORY, DESCRIPTION, CONTACT_INFO, CONTACT_NUMBER, SKIP, ADDRESS, PHONE, AGREEMENT = range(8)

END = ConversationHandler.END

def safe_to_db(user_data):
    """Safe data into database"""
    try:
        wishs_collection.insert_one({'time':datetime.datetime.now(pytz.timezone('Europe/Moscow')),
                                    'category':user_data['category'], 
                                    'user_nickname':user_data['nickname'],
                                    'full_name':user_data['full_name'],
                                    'contact_data':user_data['contact_data'],
                                    'phone_number':user_data['phone_number'],
                                    'address': user_data['address'],
                                    'description':user_data['description'],
                                    'is_agree':user_data['is_agree']
                                    })  
    except errors.PyMongoError: 
        logger.info('Something is wrong with the database')
        raise 'Something is wrong with the database'
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts conversetion and asks problem category"""
    reply_keyboard = [
                    ['ЖКХ', 'Благоустройство', 'Дороги и транспорт', 'Трудоустройство'],
                    ['Соцобеспечение', 'Здравоохранение', 'Образование', 'Правопорядок'],
                    ['Экология', 'Местная власть', 'Другое']
                    ]

    await update.message.reply_text(
        "Выберите тему для вашего обращения:\n\n",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,\
                  input_field_placeholder='Выберете что вас беспокоит'
        ),
    )

    return CATEGORY


async def problem_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected category and ask to write info about situation"""
    user = update.message.from_user
    user_data = context.user_data
    text = update.message.text
    user_data['category'] = text
    logger.info("Problem of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "Напишите, в чём именно заключается проблема или волнующий вас вопрос:",
        reply_markup=ReplyKeyboardRemove(),
    )

    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores description and ask for contact data """
    user = update.message.from_user
    user_data = context.user_data
    text = update.message.text
    
    user_data['description'] = text
    logger.info("Propblem description of %s: %s", user.name, update.message.text)
    keyboard = [[InlineKeyboardButton('Пропустить', callback_data=str(SKIP))],]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Спасибо за Ваше обращение!\n"
        "Заполните поля для обратной связи,"
        "чтобы Вас смогли проинформировать о принимаемых мерах:\n\n"
        "Введите Ваше полное имя",      
        reply_markup=reply_markup,
        
        
    )

    return CONTACT_INFO




async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the data about user and end the conversation"""
    user = update.message.from_user
    user_data = context.user_data
    text = update.message.text 
    user_data['contact_data'] = text
    user_data['nickname'] = user.name
    user_data['full_name'] = user.full_name
    logger.info("Contact data of %s tg nick %s: %s", user.full_name, user.name, update.message.text)
    keyboard = [[InlineKeyboardButton('Пропустить', callback_data=str(SKIP))],]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        
        "Введите адрес проживания:",
        reply_markup=reply_markup
    )
    
    return ADDRESS

async def address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    
    user = update.message.from_user
    user_data = context.user_data
    text = update.message.text 
    user_data['address'] = text
    logger.info("Contact data of %s tg nick %s: %s", user.full_name, user.name, update.message.text)
    keyboard = [[InlineKeyboardButton('Пропустить', callback_data=str(SKIP))],]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Введите номер телефона:",
        reply_markup=reply_markup
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_data = context.user_data
    text = update.message.text 
    user_data['phone_number'] = text
    logger.info("Contact data of %s tg nick %s: %s", user.full_name, user.name, update.message.text)
    
    await update.message.reply_text(
            "Предоставьте согласие на обработку персональных данных",
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton(
                    text="Открыть соглашение",
                    web_app=WebAppInfo(url=URL),
                )
            ),
        )
     
    return AGREEMENT

def user_input_to_user_data(user_data, user):
    user_data['contact_data'] = user_data['contact_data'] if 'contact_data' in user_data else 'Не указано'
    user_data['address'] = user_data['address'] if 'address' in user_data else 'Не указано'
    user_data['phone_number'] =\
          user_data['phone_number'] if 'phone_number' in user_data else 'Не указано'
    user_data['nickname'] = user.name
    user_data['full_name'] = user.full_name 
    return user_data

async def skip_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the location and asks for info about the user."""
    user = update.message.from_user
    logger.info("User %s did not send a info.", user.username)
    user_data = context.user_data
    if 'contact_data' in user_data: 
        await update.message.reply_text(
            "Примите соглашение на обработку персональных данных",
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton(
                    text="Открыть соглашение",
                    web_app=WebAppInfo(url=URL),
                )
            ),
        )
        return AGREEMENT
    await update.message.reply_text(
        "Ваше обращение отправлено кандидату в "
        "депутаты Д.В. Бурыке. Благодарим за активную гражданскую позицию!"
    )
    user_data = user_input_to_user_data(user_data, user)
    user_data['is_agree'] = 'Нет' 
    safe_to_db(user_data) 
    user_data.clear()
    return END
 

async def skip_contact_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: 
    """Skip contact info then user push inline button""" 
    user = update.callback_query.from_user
    query = update.callback_query
    #await query.answer()
    logger.info("User %s did not send a info.", user.username)
    await query.answer()
    user_data = context.user_data
    if 'contact_data' in user_data:
       #await update.callback_query.edit_message_text(
        await context.bot.send_message(chat_id=update.effective_chat.id, text=\
            "Примите соглашение на обработку персональных данных",
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton(
                    text="Открыть соглашение",
                    web_app=WebAppInfo(url=URL),
                )
            ),
        )
        return AGREEMENT
    user_data = user_input_to_user_data(user_data, user)
    user_data['is_agree'] = 'Нет'
    await update.callback_query.edit_message_text(
        "Ваше обращение отправлено кандидату в "
        "депутаты Д.В. Бурыке. Благодарим за активную гражданскую позицию!"
    )
    safe_to_db(user_data)  
    user_data.clear() 
    return END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
   
    await update.message.reply_text(
        "Если хотите начать напишите /start", reply_markup=ReplyKeyboardRemove()
    )

    return END




# Handle incoming WebAppData
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Print the received data and remove the button."""
    user = update.message.from_user
    user_data = context.user_data
    user_data = user_input_to_user_data(user_data, user)
    data = json.loads(update.effective_message.web_app_data.data)
    user_data['is_agree'] = 'Да' if data['is_agree'] else 'Нет'
    await update.message.reply_text(
        "Ваше обращение отправлено кандидату в "
        "депутаты Д.В. Бурыке. Благодарим за активную гражданскую позицию!",
        reply_markup=ReplyKeyboardRemove(),
    )
    safe_to_db(user_data)  
    user_data.clear()
    return END

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
    
   
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & 
                                       ~(filters.COMMAND),
                                          problem_category)],
            DESCRIPTION: [MessageHandler(filters.TEXT & 
                                         ~(filters.COMMAND),
                                              description)],
            CONTACT_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_info),
                CommandHandler("skip", skip_contact_info),
                CallbackQueryHandler(skip_contact_info_callback, pattern='^' + str(SKIP) + '$')
            ],
            ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, address),
                CommandHandler("skip", skip_contact_info),
                CallbackQueryHandler(skip_contact_info_callback, pattern='^' + str(SKIP) + '$')
            ],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone),
                CommandHandler("skip", skip_contact_info),
                CallbackQueryHandler(skip_contact_info_callback, pattern='^' + str(SKIP) + '$')
            ],
            AGREEMENT:[
                MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data)
            ]


        },
        fallbacks=[CommandHandler("cancel", cancel),
                  MessageHandler(filters.Regex('^Cтоп$|^стоп$'), cancel) 
                   ],
    )
    # test_handler = CommandHandler('agreement', agreement)
    # application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.add_handler(conv_handler)
    #application.add_handler(test_handler)
    application.add_error_handler(error_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
