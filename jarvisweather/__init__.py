import json

import datetime
import requests

import config
from context import BaseContext


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