import logging

import telegram

import config
from context import BaseContext
from main import Jarvis


class MeetingNotesContext(BaseContext):
    jarvis = None
    event = None

    state = None
    is_done_ = False

    def __init__(self, event, jarvis: Jarvis):
        self.event = event
        self.jarvis = jarvis

    def start(self, bot):
        # used if context is started by external trigger: has no update that was received
        self.state = 'asking'
        self.ask_if_desired(bot)

    def process(self, bot, update):
        if self.state is None:
            # start was not used. try to start nonetheless but issue an error
            self.state = 'asking'
            self.ask_if_desired(bot)
            logging.error('start was not used, incoming message is ignored.')
            return

        if self.state == 'asking':
            self.process_asking(bot, update)
        elif self.state == 'memo':
            self.process_memo(bot, update)
        else:
            raise RuntimeError('unknown state: %s' % self.state)

    def process_memo(self, bot, update):
        notes = update.message.text
        bot.send_message(chat_id=update.message.chat_id, text='Your message has been saved. I will remind you later.')
        print('Notes for %s: %s' % (self.event.get_summary(), notes))

        # add reminder
        reminder_text = 'Your notes for %s:\n' % self.event.get_summary()
        reminder_text += notes
        self.jarvis.add_reminder(reminder_text, 60)

    def process_asking(self, bot, update):
        if update.message.text == 'Yes':
            bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text='Starting to record notes for this meeting:',
                             reply_markup=telegram.ReplyKeyboardRemove())
            self.state = 'memo'
        elif update.message.text in ['No', 'Later']:
            bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text='Okay.', reply_markup=telegram.ReplyKeyboardRemove())
            self.state = 'memo'
            self.is_done_ = True
        else:
            self.ask_if_desired(bot)

    def ask_if_desired(self, bot):
        keyboard = [['Yes', 'No'], ['Later']]
        reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text='Would you like to take notes?',
                         reply_markup=reply_markup)

    def is_done(self):
        return self.is_done_
