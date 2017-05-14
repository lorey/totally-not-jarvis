import datetime
import json
import logging

import requests
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

import config


def main():
    updater = Updater(token=config.TELEGRAM_TOKEN)
    print(updater.bot.get_me())

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    dispatcher = updater.dispatcher

    handlers = [
        CommandHandler('start', start_callback),
        CommandHandler('whereami', whereami_callback),
        CommandHandler('weather', weather_callback),
        MessageHandler(Filters.text, plaintext_callback)
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()


def start_callback(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm totally not Jarvis! Talk to me nonetheless.")


def weather_callback(bot, update):
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

    bot.send_message(chat_id=update.message.chat_id, text=msg)


def whereami_callback(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='I have no idea.')


def plaintext_callback(bot, update):
    print('could not understand: %s' % update.message.text)
    reply = 'I cannot understand "%s", sorry.' % update.message.text
    bot.send_message(chat_id=update.message.chat_id, text=reply)


if __name__ == '__main__':
    main()
