""" Bot for collecting info from mongodb in xlsx format """
import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import ReplyKeyboardMarkup, Update

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()
TOKEN = os.getenv('TOKEN2')
new_field_name = ['id','Дата', 'Категория', 'Контактные данные', 'Описание проблемы или наказа']
field_name = [ '_id', 'time','category', 'contact_data', 'description' ]

client = MongoClient('localhost', 27017)
db = client['delegations']
reply_keyboard = [["Скачать таблицу"], ["Стоп"]]

def db_select_data() -> str:
    wishs_collection = db['wishs_collection']
    data = wishs_collection.find()
    df = pd.DataFrame(data=data)
    table_name = 'table.xlsx'
    with open(table_name, 'w') as excelFile:
        df.to_excel(table_name)
    return table_name


async def send_table(update: Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    """Send xlsx table to user"""
    chat_id = update.message.chat_id
    table_name = db_select_data()
    document = open(table_name, 'rb')
    await context.bot.send_document(chat_id, document)
    document.close()
    os.remove(table_name)
    await update.message.reply_text(
        'Отправляю файл',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,
                  input_field_placeholder = 'Действие'
        ),
    )
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Entry point'''
    

    await update.message.reply_text(
        'Выберете действие',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,
                  input_field_placeholder = 'Действие'
        ),
    )

def main():
    '''Bots main function'''
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler('start', start)
    send_handler = MessageHandler(filters.Regex('^Скачать таблицу$'), send_table)
    
    application.add_handler(start_handler)
    application.add_handler(send_handler)
    application.run_polling()

if __name__ == '__main__':
    main()