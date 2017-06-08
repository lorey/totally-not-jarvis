import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging

import config
from context import BaseContext

SIGNATURE_FILE = 'signature.txt'


class Email(object):
    subject = None
    message = None
    to = []


class MailerContext(BaseContext):
    email = None

    def __init__(self, email: Email):
        self.email = email

    def is_done(self):
        return True

    def process(self, bot, update):
        print('Trying to send a mail')
        print(self.email.__dict__)
        send_email(self.email)
        bot.send_message(chat_id=update.message.chat_id, text='Okay, I have sent the mail successfully.')


def send_email(email):
    from_address = config.EMAIL_ADDRESS_JARVIS
    to_addresses = email.to
    cc_addresses = [config.EMAIL_ADDRESS_CC]

    # compose message
    msg = MIMEMultipart()

    msg['From'] = from_address
    msg['To'] = ','.join(to_addresses)
    msg['Cc'] = ','.join(cc_addresses)
    msg['Subject'] = email.subject

    message_content = '\n'.join([email.message, get_signature()])
    mime_text = MIMEText(message_content, 'plain')
    msg.attach(mime_text)

    with smtplib.SMTP_SSL(config.EMAIL_SMTP_HOST, config.EMAIL_SMTP_PORT) as s:
        # todo works for me but not for everyone
        s.ehlo()
        s.login(config.EMAIL_IMAP_USER, config.EMAIL_IMAP_PASSWORD)

        s.send_message(msg)


def get_signature():
    dir = os.path.dirname(__file__)
    filename = os.path.join(dir, SIGNATURE_FILE)
    with open(filename, 'r') as file:
        signature = file.read()
    return signature % {'bot': config.BOT_NAME, 'owner': config.OWNER_NAME}