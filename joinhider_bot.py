#!/usr/bin/env python
from pprint import pprint
from collections import Counter
import json
import logging
from argparse import ArgumentParser
from datetime import datetime, timedelta
import re

import telebot

from database import connect_db

HELP = """*Join Hider Bot*

This bot removes messages about new user joined or left the chat.

*Commands*

/help - display this help message

*How to Use*

- Add bot as ADMIN to the chat group
- Allow bot to delete messages, any other admin permissions are not required

*Questions, Feedback*

Support group: [@tgrambots](https://t.me/tgrambots)

*Open Source*

The source code is available at [github.com/lorien/joinhider_bot](https://github.com/lorien/joinhider_bot)

*My Other Project*

[@daysandbox_bot](https://t.me/daysandbox_bot) - bot that fights with spam messages in chat groups
[@nosticker_bot](https://t.me/nosticker_bot) - bot to delete stickers posted to group
[@coinsignal_robot](https://t.me/coinsignal_robot) - bot to be notified when price of specific coin reaches the level you have set, also you can use this bot just to see price of coins.

*Donation*
Ethereum: 0x00D0c93B180452a7c7B70F463aD9D24d9C6d4d61
Litecoin: LKJ86NwUkoboZyFHQwKPx8X984g3m3MPjC
Dash: XtGpsphiR2n9Shx9JFAwnuwGmWzSEvmrtU
UFO coin: CAdfaUR3tqfumoN7vQMVZ98CakyywgwK1L
"""


class InvalidCommand(Exception):
    pass


def create_bot(api_token, db):
    bot = telebot.TeleBot(api_token)

    @bot.message_handler(commands=['start', 'help'])
    def handle_start_help(msg):
        if msg.chat.type == 'private':
            bot.send_message(msg.chat.id, HELP, parse_mode='Markdown', disable_web_page_preview=True)

    @bot.message_handler(content_types=['new_chat_members'])
    def handle_new_chat_member(msg):
        try:
            bot.delete_message(msg.chat.id, msg.message_id)
        except Exception as ex:
            if 'message to delete not found' in str(ex):
                logging.error('Failed to delete join message: %s' % ex)
            else:
                raise
        for user in msg.new_chat_members:
            db.chat.find_one_and_update(
                {'chat_id': msg.chat.id},
                {
                    '$set': {
                        'chat_username': msg.chat.username,
                    },
                    '$setOnInsert': {
                        'date': datetime.utcnow(),
                    },
                },
                upsert=True,
            )
            db.joined_user.find_one_and_update(
                {
                    'chat_id': msg.chat.id,
                    'user_id': user.id,
                },
                {'$set': {
                    'chat_username': msg.chat.username,
                    'user_username': user.username,
                    'date': datetime.utcnow(),
                }},
                upsert=True,
            )
            logging.debug('Removed join message for user %s at chat %d' % (
                user.username or '#%d' % user.id,
                msg.chat.id
            ))

    @bot.message_handler(content_types=['left_chat_member'])
    def handle_left_chat_member(msg):
        try:
            bot.delete_message(msg.chat.id, msg.message_id)
        except Exception as ex:
            if 'message to delete not found' in str(ex):
                logging.error('Failed to delete join message: %s' % ex)
            else:
                raise
        for user in [msg.left_chat_member]:
            db.chat.find_one_and_update(
                {'chat_id': msg.chat.id},
                {
                    '$set': {
                        'chat_username': msg.chat.username,
                    },
                    '$setOnInsert': {
                        'date': datetime.utcnow(),
                    },
                },
                upsert=True,
            )
            db.left_user.find_one_and_update(
                {
                    'chat_id': msg.chat.id,
                    'user_id': user.id,
                },
                {'$set': {
                    'chat_username': msg.chat.username,
                    'user_username': user.username,
                    'date': datetime.utcnow(),
                }},
                upsert=True,
            )
            logging.debug('Removed left message for user %s at chat %d' % (
                user.username or '#%d' % user.id,
                msg.chat.id
            ))

    return bot


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)


def init_bot_with_mode(mode):
    with open('var/config.json') as inp:
        config = json.load(inp)
    if mode == 'test':
        token = config['test_api_token']
    else:
        token = config['api_token']

    db = connect_db()
    bot = create_bot(token, db)

    return bot


def main():
    setup_logging()
    parser = ArgumentParser()
    parser.add_argument('--mode')
    opts = parser.parse_args()

    bot = init_bot_with_mode(opts.mode)

    bot.remove_webhook()
    bot.polling()


if __name__ == '__main__':
    main()
