import datetime
import json
import logging

import requests
import telegram
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import Job
from telegram.ext import MessageHandler
from telegram.ext import Updater

import config
import jarviscalendar

EVENT_TRIGGER_INTERVAL_IN_SECONDS = 60 * 5


class Jarvis(object):
    name = 'Jarvis'
    contexts = []
    default_context = None

    updater = None

    def __init__(self, updater: Updater):
        self.default_context = DefaultContext(self)
        self.updater = updater

    def hello(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="I'm totally not %s! Talk to me nonetheless." % self.name)

    def receive(self, bot, update):
        # decide what to do with update
        print('received: %s' % update.message.text)

        # get context
        if len(self.contexts) > 0:
            applicable_context = self.contexts[-1]
        else:
            # use default context
            applicable_context = self.default_context

        applicable_context.process(bot, update)

        # remove completed contexts
        for context in self.contexts:
            if context.is_done():
                self.contexts.remove(context)

    def events(self, bot, job):
        # avoid interrupting running context
        if len(self.contexts) > 0:
            return

        next_event = jarviscalendar.get_next_event()
        time_to_event = next_event.get_start() - datetime.datetime.now(tz=datetime.timezone.utc)
        if time_to_event.total_seconds() <= EVENT_TRIGGER_INTERVAL_IN_SECONDS or True:
            # send event message
            msg = 'Next event: %s\n' % next_event.get_summary()
            msg += next_event.get_description()
            bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=msg)

            # start notes context
            notes_context = MeetingNotesContext(next_event, self)
            notes_context.start(bot)
            self.contexts.append(notes_context)

    def add_reminder(self, text, after_minutes):
        after_seconds = after_minutes * 60

        job = Job(self.send_reminder_callback, after_seconds, repeat=False, context=text)
        self.updater.job_queue.put(job)

    def send_reminder_callback(self, bot, job):
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=job.context)


class BaseContext(object):
    def is_done(self):
        raise Exception('implementation missing')

    def process(self, bot, update):
        raise Exception('implementation missing')


class DefaultContext(BaseContext):
    jarvis = None

    def __init__(self, jarvis):
        self.jarvis = jarvis

    def process(self, bot, update):
        if update.message is not None and update.message.text.startswith('/weather'):
            context = WeatherContext()
            self.jarvis.contexts.append(context)
            context.process(bot, update)
        else:
            bot.send_message(chat_id=update.message.chat_id, text="I don't understand")


class WeatherContext(BaseContext):
    def process(self, bot, update):
        message = self.fetch_weather()
        bot.send_message(chat_id=update.message.chat_id, text=message)

    def fetch_weather(self):
        url_template = 'http://api.openweathermap.org/data/2.5/forecast?lat=%f&lon=%f&APPID=%s'
        url = url_template % (config.POSITION['lat'], config.POSITION['lon'], config.OPENWEATHERMAP_API_KEY)
        response = requests.get(url)
        json_plain = response.content.decode('utf-8')
        data = json.loads(json_plain)
        # print(json.dumps(data, indent=2))

        msg = 'The weather forecast for %s:\n' % data['city']['name']
        for forecast in data['list'][0:8]:
            time = datetime.datetime.fromtimestamp(forecast['dt']).strftime('%H:%M')
            description = forecast['weather'][0]['description']
            temperature_celsius = forecast['main']['temp'] - 273.15
            humidity = forecast['main']['humidity']

            msg += '%s: %s (%d°C, %d%%)\n' % (time, description, temperature_celsius, humidity)

        return msg

    def is_done(self):
        return True


class MeetingNotesContext(BaseContext):
    jarvis = None
    event = None
    is_done_ = False

    def __init__(self, event, jarvis: Jarvis):
        self.event = event
        self.jarvis = jarvis

    def start(self, bot):
        keyboard = [['Yes', 'No'], ['Later']]
        reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text='Would you like to take notes?',
                         reply_markup=reply_markup)

    def process(self, bot, update):
        if update.message.text == 'Yes':
            bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text='Starting to record notes for this meeting:', reply_markup=telegram.ReplyKeyboardRemove())
        elif update.message.text in ['No', 'Later']:
            bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text='Okay.', reply_markup=telegram.ReplyKeyboardRemove())
            self.is_done_ = True
        else:
            notes = update.message.text
            print('Notes for %s: %s' % (self.event.get_summary(), notes))
            bot.send_message(chat_id=update.message.chat_id, text='Your message has been saved. I will remind you later.')

            reminder_text = 'Your notes for %s:\n' % self.event.get_summary()
            reminder_text += notes
            self.jarvis.add_reminder(reminder_text, 60)

    def is_done(self):
        return self.is_done_


def main():
    updater = Updater(token=config.TELEGRAM_TOKEN)
    print(updater.bot.get_me())

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    jarvis = Jarvis(updater)

    event_infos = Job(jarvis.events, EVENT_TRIGGER_INTERVAL_IN_SECONDS)
    updater.job_queue.put(event_infos, next_t=0)

    handlers = [
        CommandHandler('start', jarvis.hello),
        MessageHandler(Filters.all, jarvis.receive)
    ]

    dispatcher = updater.dispatcher
    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
