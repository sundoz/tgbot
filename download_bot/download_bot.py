""" Bot for collecting info from mongodb in xlsx format """
import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, errors
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
TABLE1, TABLE2, TABLE3 = 'wishs_collection', '', ''

field_name = [ '_id', 'time','nickname', 'category', 'contact_data', 'description' ]

client = MongoClient('localhost', 27017)
db = client['delegations']
reply_keyboard = [["Скачать таблицу 1"], ["Скачать таблицу 2"], ["Скачать таблицу 3"], ["Стоп"]]

def db_select_data(collection) -> str:
    
    wishs_collection = db[collection]
    data = wishs_collection.find()
    df = pd.DataFrame(data=data)
    table_name = 'table.xlsx'
    df.rename(columns = {'time': "Время",
                    'category': 'Категория',
                    'user_nickname':'Ник в телеграме',
                    'contact_data':'Имя пользователя',
                    'description':'Описание проблемы'}, inplace = True)
    df = df.iloc[:, 1:]
    with open(table_name, 'w') as excelFile:
        df.to_excel(table_name)


    return table_name


async def send_table(update: Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    """Send xlsx table to user"""
    chat_id = update.message.chat_id
    message = update.message.text
    if message == 'Скачать таблицу 1':
        table_name = db_select_data(TABLE1)
    elif message == 'Скачать таблицу 2':
        table_name = db_select_data(TABLE2)
    elif message == 'Скачать таблицу 3':
        table_name = db_select_data(TABLE3)

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
    send_handler = MessageHandler(filters.Regex('^Скачать таблицу 1$|^Скачать таблицу 2$|^Скачать таблицу 3$'), send_table)
    
    application.add_handler(start_handler)
    application.add_handler(send_handler)
    application.run_polling()

if __name__ == '__main__':
    main()