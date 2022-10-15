import telebot
from telebot.util import quick_markup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from leistungsdb import LeistungsDB
from google_place import Places
import yaml
import random
from enum import IntEnum
import json
from datetime import datetime, timedelta
import tempfile
import os
import pickle
import random


class LeistungsTyp(IntEnum):
    NORMAL = 1
    KONKURENZ = 2
    ZUSATZ = 3


class Helper(object):
    def __init__(self, bot: telebot.TeleBot) -> None:
        self.bot = bot
        self.config = yaml.safe_load(open("BotConfig.yml"))
        self.db = LeistungsDB()
        self.temp_dir = tempfile.gettempdir()
        self.google = Places()

    def get_full_temp_file(self, file_id: str):
        return os.path.join(self.temp_dir, str(file_id) + '_leistung')

    def get_full_temp_file_handle(self, file_id: str, rw=False):
        path = self.get_full_temp_file(file_id)
        if rw:
            return open(path, 'wb')
        else:
            return open(path, 'rb')

    def store_to_rand_file(self, data):
        rand_id = random.randint(10000, 100000)
        with self.get_full_temp_file_handle(rand_id, True) as handle:
            pickle.dump(data, handle)
        return rand_id

    def peak_from_rand_file(self, rand_id):
        with self.get_full_temp_file_handle(rand_id) as handle:
            return pickle.load(handle)

    def load_from_rand_file(self, rand_id):
        with self.get_full_temp_file_handle(rand_id) as handle:
            data = pickle.load(handle)
        os.remove(self.get_full_temp_file(rand_id))
        return data

    def location_keyboard(self):
        markup = ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
        for location in self.db.getVirgineLocations():
            markup.add(KeyboardButton(location[0]))
        return markup

    def location_button(self):
        markup = InlineKeyboardMarkup(row_width=1)
        for location in self.db.getVirgineLocations():
            markup.add(InlineKeyboardButton(
                location[0], callback_data=json.dumps({'location': location[1]})))
        return markup

    def search_location_button(self, query):
        markup = InlineKeyboardMarkup(row_width=1)
        g = self.google.findPlace(query)
        rand_id = self.store_to_rand_file(g)
        for i in range(len(g)):
            markup.add(InlineKeyboardButton(
                g[i]['name'], callback_data=json.dumps({'search': (rand_id, i)})))
        return markup

    def restore_search_location_button(self, rand_id):
        markup = InlineKeyboardMarkup(row_width=1)
        g = self.peak_from_rand_file(rand_id)
        for i in range(len(g)):
            markup.add(InlineKeyboardButton(
                g[i]['name'], callback_data=json.dumps({'search': (rand_id, i)})))
        return markup

    def approve_location_button(self, rand_id, index):
        markup = InlineKeyboardMarkup(row_width=1, )
        markup.add(
            InlineKeyboardButton(
                'Ned mei location', callback_data=json.dumps({'select': (rand_id, -1)})),
            InlineKeyboardButton('Des is mei location', callback_data=json.dumps(
                {'select': (rand_id, index)})))
        return markup

    def unkown_location_button(self, location):
        markup = InlineKeyboardMarkup(row_width=2, )
        markup.add(
            InlineKeyboardButton(
                'Na', callback_data=json.dumps({'cancle': None})),
            InlineKeyboardButton('Jo', callback_data=json.dumps(
                {'q': location})))
        return markup

    def dry_run_button(self, rand_id):
        markup = InlineKeyboardMarkup(row_width=2, )
        markup.add(
            InlineKeyboardButton(
                'Na', callback_data=json.dumps({'cancle': None})),
            InlineKeyboardButton('Jo', callback_data=json.dumps(
                {'publish': rand_id})))
        return markup

    def sender_has_permission(self, msg):
        sender = self.bot.get_chat_member(
            self.config['leistungschat_id'], msg.from_user.id)
        return sender.status == 'administrator' or sender.status == 'creator'

    def send_nude(self, chat_id):
        gif = 'https://cdn.porngifs.com/img/%s' % (random.randint(1, 39239))
        self.bot.send_animation(
            chat_id, gif, caption='brought to you by Maxmaier')

    def send_leistungstag(self, chat_id, location: str, type: LeistungsTyp = LeistungsTyp.NORMAL, date: datetime = None, dry_run: bool = True):
        if not date:
            date = (datetime.now() + timedelta(
                days=(8 - datetime.now().weekday())))
        date_str = date.strftime('%d.%m.%Y')
        close_date = date - timedelta(hours=12)
        info = self.db.getLocationInfo(location)
        venue_id = self.bot.send_venue(chat_id, latitude=info['location'][0],
                                       longitude=info['location'][1], title=info['name'], address=info['address'])
        count = self.db.getHistoryCount(type)
        count = count + 1 if count else 1
        if (type == LeistungsTyp.NORMAL):
            question = f'Leistungstag {count}: am {date_str} in "{location}"'
        elif (type == LeistungsTyp.KONKURENZ):
            question = f'Konkurrenz Leistungstag {count}: am {date_str} in "{location}"'
        elif (type == LeistungsTyp.ZUSATZ):
            question = f'Leistungstag Zusatztermin {count}: am {date_str} in "{location}"'
        else:
            question = f'Keine Ahnung wos wia grad polln...'
        poll_id = self.bot.send_poll(
            chat_id,
            question,
            ["Bin dabei", "Keine Zeit"],
            allows_multiple_answers=False,
            explanation="Soi i da jez a nu erklährn wie ma obstimmt?",
            type='quiz',
            correct_option_id=0,
            is_anonymous=False
        )
        if dry_run:
            rand_id = self.store_to_rand_file((location, type, date))
            self.bot.send_message(
                chat_id, 'Woin ma des so veröffentlichen?', reply_markup=self.dry_run_button(rand_id))
        else:
            self.db.addLeistungsTag(
                date, location, poll_id.message_id, venue_id.message_id, int(type))

    def send_location_info(self, chat_id, place_id, reply_markup=None):
        info = self.google.getPlaceInfo(place_id)
        self.bot.send_venue(chat_id, info['geometry']['location']['lat'], info['geometry']
                            ['location']['lng'], info['name'], info['formatted_address'],
                            google_place_id=place_id, reply_markup=reply_markup)

    def approve_location(self, chat_id, rand_id, index):
        data = self.peak_from_rand_file(rand_id)
        self.send_location_info(
            chat_id, data[index]['place_id'], self.approve_location_button(rand_id, index))

    def add_location(self, rand_id, index):
        data = self.load_from_rand_file(rand_id)
        self.db.addLocation(data[index]['place_id'], data[index]['name'])

    def publish_leistungstag(self, rand_id):
        vals = self.load_from_rand_file(rand_id)
        # TODO Change chat-id
        self.send_leistungstag(
            self.config['leistungsadmin_id'], vals[0], vals[1], vals[2], False)

    def excep(self, msg, error):
        self.bot.send_message(self.config['chat_id'], f'''Error From Poll Bot!

Error  :: {error}

--------------------------------

Command:: {msg.text}

--------------------------------

UserDetails: {msg.from_user}

--------------------------------

Date   :: {msg.date}

--------------------------------

The Complete Detail:
{msg}


''')

        return self.bot.reply_to(self.message, f'''An Unexpected Error Occured!
Error::  {error}
The error was informed to @eckphi''')
