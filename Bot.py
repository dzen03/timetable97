import datetime
import sqlite3
import subprocess
import sys
import time
import traceback
import variables
from os import listdir, getcwd

import telebot
from telebot import types

from misc_functions import next_day

bot = telebot.TeleBot(variables.token)

admins = []  # add nicknames (without @) for ability to do "/refresh" (e.g. 'durov')

splitter = '|'  # split pages

users_subscribed_to_titles = set()


def is_this_file(file, is_today: bool, pages=''):  # blank page if you need all pages
    answer = False
    pages = pages.split(splitter)
    for page in pages:
        answer |= file.startswith(str((datetime.datetime.now() + datetime.timedelta(
            days=next_day(is_today))).isoweekday())) \
                  and file.endswith(page + '.jpg')
    return answer


def write_to_all_users(text, force_notification=False):
    try:
        if datetime.datetime.now().hour == 0 and datetime.datetime.now().minute == 0 \
                and datetime.datetime.now().isoweekday() == 1:
            return
        users_id = []
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute(f"SELECT id FROM user WHERE notification = 1 OR notification = {int(not force_notification)}")
            # select all users
            users_id = c.fetchall()
        except Exception as ex:
            print(ex)
        finally:
            c.close()
            conn.close()

        for user_id in users_id:
            try:
                if datetime.datetime.now().hour <= 6 or datetime.datetime.now().hour >= 0:  # night time
                    bot.send_message(chat_id=user_id[0], text=text, disable_notification=True)
                else:
                    bot.send_message(chat_id=user_id[0], text=text)
            except Exception:
                pass
    except Exception as ex:
        print(ex)


def send_schedule(received_message, is_today: bool):
    page = ''
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute(f"SELECT page FROM user WHERE id={received_message.chat.id}")
        answer = c.fetchone()
    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)
    finally:
        c.close()
        conn.close()

    if answer is not None:
        page = str(answer[0])
    is_schedule_exists = False

    only_files = listdir(getcwd())
    list.sort(only_files)

    page = str(int(page) - 1)
    if page == '-2':
        page = ''
    if page == '2':  # sometimes there are more than 3 pages
        page = f'2{splitter}3'

    for file in only_files:
        if is_this_file(file, is_today, page):
            is_schedule_exists = True
            page_num = file.split('.')[0][-1:]  # only page
            date = file.split('-')[1]  # only date
            if date[1].isdigit():
                day = date[:2]
                month = date[2:]
            else:
                day = date[:1]
                month = date[1:]
            title = f"Дата: {day} {month}.\tCтраница №{int(page_num) + 1}"  # beautify
            if received_message.chat.id not in users_subscribed_to_titles:
                title = ''
            bot.send_photo(chat_id=received_message.chat.id, photo=(open(file, 'rb')), caption=title)

    if not is_schedule_exists:
        bot.send_message(chat_id=received_message.chat.id, text="У меня нет расписания на этот день",
                         reply_to_message_id=received_message.json['message_id'])


@bot.message_handler(commands=['today'])
def today(message):
    try:
        send_schedule(message, True)
    except Exception as ex:
        bot.send_message(chat_id=message.chat.id, text="Ошибка. Попробуйте позже")
        print(ex)


@bot.message_handler(commands=['tomorrow'])
def today(message):
    try:
        send_schedule(message, False)
    except Exception as ex:
        bot.send_message(chat_id=message.chat.id, text="Ошибка. Попробуйте позже")
        print(ex)


@bot.message_handler(commands=['refresh'])
def sett(message):  # only for admins
    if message.from_user.username in admins:
        subprocess.call(['python3', 'Main.py'])
        bot.reply_to(message, "Обновлено!")
    else:
        bot.reply_to(message, "Вы не администратор")


@bot.message_handler(commands=['start'])
def start(message):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute(f"INSERT OR IGNORE INTO user(id) VALUES ({message.chat.id})")  # add new user
        conn.commit()
    except Exception as ex:
        print(ex)
    finally:
        c.close()
        conn.close()

    main_menu_keyboard = ['/today', '/tomorrow', '/settings']

    menu_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for menus in main_menu_keyboard:
        menu_markup.add(menus)
    bot.send_message(chat_id=message.chat.id, text="""Привет!

Я умею кидать расписание на сегодня: /today
Или на следующий учебный день: /tomorrow

Но для этого нужно выбрать лист: /settings""", reply_markup=menu_markup)


def settings_markup(values: dict):  # keyboard for settings
    markup = types.InlineKeyboardMarkup()

    for key, value in values.items():
        markup.add(types.InlineKeyboardButton(text=value, callback_data=key))

    return markup


@bot.message_handler(commands=['settings'])
def settings(message):  # TODO fix freezes
    values = {f'{category_tag}{splitter}{notification_tag}': 'Уведомления', f'{category_tag}{splitter}{page_tag}': 'Страница',
              f'category{splitter}title': 'Подпись'}

    bot.send_message(chat_id=message.chat.id, text='Выберите нужные настройки:',
                     reply_to_message_id=message.message_id, reply_markup=settings_markup(values))


page_tag = 'page'  # pages setting
notification_tag = 'notification'  # notifications setting
category_tag = 'category'  # categories setting
title_tag = 'title'  # titles setting


@bot.callback_query_handler(func=lambda call: True)
def handle(call):  # response from keyboard
    replied_message = call.message

    answer = call.data.split(splitter)
    tag = answer[0]
    data = answer[1]

    values = {}
    text = 'Ошибка. Попробуйте позже'
    answer_to_user = ''

    if tag == category_tag:
        if data == notification_tag:
            values = {f'{notification_tag}{splitter}1': 'Да', f'{notification_tag}{splitter}0': 'Нет'}
            text = 'Нужно ли присылать уведомления?'
        elif data == page_tag:
            values = {f'{page_tag}{splitter}1': '1', f'{page_tag}{splitter}2': '2', f'{page_tag}{splitter}3': '3', f'{page_tag}{splitter}-1': 'Все'}
            text = 'Выберите нужную страницу:'
        elif data == title_tag:  # now cant go here
            values = {f'{title_tag}{splitter}1': 'Да', f'{title_tag}{splitter}0': 'Нет'}
            text = f'Нужно ли подписывать фотографии? Пример: "10 марта"'

        bot.send_message(chat_id=replied_message.chat.id, text=text,
                         reply_to_message_id=replied_message.reply_to_message.message_id,
                         reply_markup=settings_markup(values))

    else:
        new_state = int(data)
        if tag == page_tag:
            if new_state != -1:
                answer_to_user = f"Теперь у Вас выбрана страница {new_state}"
            else:
                answer_to_user = f"Теперь у Вас выбраны все страницы"

        elif tag == notification_tag:
            answer_to_user = f"Теперь у Вас {'включены' if new_state == 1 else 'выключены'} уведомления"

        elif tag == title_tag:
            answer_to_user = f"Теперь у Вас {'включены' if new_state == 1 else 'выключены'} подписи"
            if new_state == 0:
                users_subscribed_to_titles.remove(replied_message.chat.id)
            else:
                users_subscribed_to_titles.add(replied_message.chat.id)

        update_settings(tag, new_state, answer_to_user, replied_message)


def update_settings(field: str, new_state, answer_to_user: str, replied_message):
    is_done = True
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute(f"UPDATE user SET {field} = {new_state} WHERE id = {replied_message.chat.id}")
        conn.commit()
    except Exception as ex:
        is_done = False
        print(ex)
    finally:
        c.close()
        conn.close()
    if is_done:
        bot.send_message(chat_id=replied_message.chat.id, text=answer_to_user)
    else:
        bot.send_message(chat_id=replied_message.chat.id, text="Ошибка. Попробуйте позже")
    # TODO delete old messages


def main():
    users_id = []
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute(f"SELECT id FROM user WHERE title = 1")
        users_id = c.fetchall()
    except Exception as ex:
        print(ex)
    finally:
        c.close()
        conn.close()

    global users_subscribed_to_titles
    for user in users_id:
        users_subscribed_to_titles.add(user[0])

    poll()


def poll():
    while True:
        try:
            print(f"I am {bot.get_me().username}. And I'm alive!")
            bot.polling(timeout=10)
        except KeyboardInterrupt:
            bot.stop_bot()
            exit(0)
        except Exception as ex:
            print(ex)
            time.sleep(600)


if __name__ == '__main__':
    args = sys.argv
    if len(args) > 2:
        if args[1] == '--write':
            write_to_all_users(args[2], True)
    else:
        main()
