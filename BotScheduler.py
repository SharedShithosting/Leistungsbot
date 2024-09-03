from datetime import datetime, timedelta
import telebot
import threading
import time
import schedule
import yaml
from leistungsdb import LeistungsDB, LeistungsTagState
from BotHelper import LeistungsTyp
import os


class Scheduler(object):
    def __init__(self, bot: telebot.TeleBot) -> None:
        self.bot = bot
        self.config = yaml.safe_load(
            open(os.environ.get("LEISTUNGSBOT_CONFIG_FILE", "BotConfig.yml")))
        self.db = LeistungsDB()
        self.schedule = schedule
        self.schedule.every().day.at('12:00').do(self.send_reminder)
        self.schedule.every().monday.at('12:00').do(self.send_reservation)
        self.schedule.every().day.at('19:00').do(self.close_previous)
        self.start()

    def run_continuously(self, interval=1):
        """Continuously run, while executing pending jobs at each
        elapsed time interval.
        @return cease_continuous_run: threading. Event which can
        be set to cease continuous run. Please note that it is
        *intended behavior that run_continuously() does not run
        missed jobs*. For example, if you've registered a job that
        should run every minute and you set a continuous run
        interval of one hour then your job won't be run 60 times
        at each interval but only once.
        """
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    self.schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        return cease_continuous_run

    def start(self):
        # Start the background thread
        self.stop_run_continuously = self.run_continuously()

    def stop(self):
        # Stop the background thread
        self.stop_run_continuously.set()

    def send_reminder(self, type: LeistungsTyp = None):
        polls = self.db.getOpenLeistungsTag(type)
        for poll in polls:
            if (datetime.now() + timedelta(days=2)).date() == poll['date']:
                self.bot.send_message(
                    self.config['leistungschat_id'], 'Reminder. Übermorgen ises so weit, daun is endlich wieder Leistungstag.', reply_to_message_id=poll['poll_id'])

    def send_reservation(self, type: LeistungsTyp = None):
        polls = self.db.getClosedLeistungsTag(type)
        for poll in polls:
            if (datetime.now() + timedelta(days=1)).date() == poll['date']:
                info = self.db.getLocationInfo(
                    self.db.getLocationName(poll['location']))
                self.bot.forward_message(
                    self.config['leistungsadmin_id'], self.config['leistungschat_id'], poll['poll_id'])
                self.bot.send_message(
                    self.config['leistungsadmin_id'], f'Host eam e scho für moagn schiach reserviert ({info["phone"]})? {info["url"]}')

    def close_previous(self, type: LeistungsTyp = None):
        previous = self.db.getLeistungsTags(
            type, LeistungsTagState.OPEN, before=datetime().now())
        for prev in previous:
            location = self.db.getLocationName(prev['location'])
            self.bot.send_message(
                self.config['leistungsadmin_id'], f'Schaut so aus ois ob do a alter Leistungstag nuned geclosed worden is...I schlias {location} fia eich.')
            self.helper.db.closeLeistungstag(leistungstag_key)
            self.bot.stop_poll(
                config['leistungschat_id'], leistungstag['poll_id'])


if __name__ == '__main__':
    config = yaml.safe_load(
        open(os.environ.get("LEISTUNGSBOT_CONFIG_FILE", "BotConfig.yml")))
    s = Scheduler(telebot.TeleBot(config['bot_token']))
    s.schedule.every().second.do(p)
    time.sleep(5)
    s.schedule.every().second.do(f)
    time.sleep(5)
    s.stop()
    s.send_reminder()
