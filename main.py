import datetime
import json
import logging

import requests
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

import config


class Jarvis(object):
    name = 'Jarvis'
    contexts = []
    default_context = None

    def __init__(self):
        self.default_context = DefaultContext(self)

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


class DefaultContext(object):
    jarvis = None

    def __init__(self, jarvis):
        self.jarvis = jarvis

    def can_handle(self, bot, update):
        return True

    def process(self, bot, update):
        if update.message is not None and update.message.text.startswith('/weather'):
            context = WeatherContext()
            self.jarvis.contexts.append(context)
            context.process(bot, update)
        else:
            bot.send_message(chat_id=update.message.chat_id, text="I don't understand")


class WeatherContext(object):

    def can_handle(self, bot, update):
        return True

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


def main():
    # jarviscalendar.print_events()
    # exit()

    updater = Updater(token=config.TELEGRAM_TOKEN)
    print(updater.bot.get_me())

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    jarvis = Jarvis()

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
