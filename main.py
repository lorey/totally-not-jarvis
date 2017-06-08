import datetime
import logging

from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

import config
import jarviscalendar
import jarvismeetingnotes
import jarvismeetingscheduler
import jarvisweather
from context import BaseContext

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
        if time_to_event.total_seconds() < EVENT_TRIGGER_INTERVAL_IN_SECONDS:
            # send event message
            msg = 'Next event: %s\n' % next_event.get_summary()
            msg += next_event.get_description()
            bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=msg)

            # start notes context
            notes_context = jarvismeetingnotes.MeetingNotesContext(next_event, self)
            notes_context.start(bot)
            self.contexts.append(notes_context)

    def add_reminder(self, text, after_minutes):
        when = datetime.datetime.now() + datetime.timedelta(minutes=after_minutes)
        self.updater.job_queue.run_once(self.send_reminder_callback, when, context=text)

    def send_reminder_callback(self, bot, job):
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=job.context)


class DefaultContext(BaseContext):
    jarvis = None

    def __init__(self, jarvis):
        self.jarvis = jarvis

    def process(self, bot, update):
        if update.message is not None and update.message.text.startswith('/weather'):
            context = jarvisweather.WeatherContext()
            self.jarvis.contexts.append(context)
            context.start(bot)
        elif update.message is not None and update.message.text.startswith('/schedule'):
            context = jarvismeetingscheduler.ScheduleMeetingContext(self.jarvis)
            self.jarvis.contexts.append(context)
            context.start(bot)
        else:
            bot.send_message(chat_id=update.message.chat_id, text="I don't understand")


def main():
    updater = Updater(token=config.TELEGRAM_TOKEN)
    print(updater.bot.get_me())

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    jarvis = Jarvis(updater)

    interval = datetime.timedelta(seconds=EVENT_TRIGGER_INTERVAL_IN_SECONDS)
    updater.job_queue.run_repeating(jarvis.events, interval, first=0)

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
