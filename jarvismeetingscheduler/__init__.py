import os
from time import sleep

import config
import jarvismailer
import nlphelpers
from context import BaseContext


class MeetingProposal(object):
    who = []
    when = None
    why = None
    length = None

    def get_message(self):
        # load template
        dir = os.path.dirname(__file__)
        filename = os.path.join(dir, 'meeting-proposal-email.txt')
        with open(filename, 'r') as file:
            template = file.read()

        # fill template
        data = {
            'why': self.why,
            'length': self.length,
            'list_of_dates': '\n'.join(['- %s' % when for when in self.when]),
            'owner': config.OWNER_NAME,
            'bot': config.BOT_NAME,
        }
        message = template % data

        return message

    def __str__(self):
        return 'MeetingProposal: ' + str(self.__dict__)


class ScheduleMeetingContext(BaseContext):
    jarvis = None

    meeting_proposal = None

    entities = {
        'participants': {
            'question': 'Who should attend the meeting? (list of emails of participants)'
        },
        'proposed_time': {
            'question': 'When should the meeting take place?'
        },
        'occasion': {
            'question': 'What\'s the occasion?'
        },
        'length': {
            'question': 'How much time should participants block? (in minutes)'
        },
    }
    processed_entities = []
    current_entity = None

    def __init__(self, jarvis):
        self.jarvis = jarvis
        self.meeting_proposal = MeetingProposal()

    def process(self, bot, update):
        if self.current_entity is not None:
            # process entity
            self.process_entity(self.current_entity, update)
            self.processed_entities.append(self.current_entity)

        # get next entity to process
        self.current_entity = self.get_next_entity()

        if self.current_entity is not None:
            # ask question for next entity
            self.send_message(self.current_entity, bot, update)
        else:
            # use context to send mail
            # todo: actually integrate context
            print(self.meeting_proposal)
            email = jarvismailer.Email()
            email.subject = self.meeting_proposal.why
            email.message = self.meeting_proposal.get_message()
            email.to = self.meeting_proposal.who

            jm = jarvismailer.MailerContext(email)
            jm.process(bot, update)

    def is_done(self):
        return len(self.get_unprocessed_entities()) == 0

    def get_next_entity(self):
        unprocessed_entities = self.get_unprocessed_entities()
        return next(iter(unprocessed_entities), None)

    def get_unprocessed_entities(self):
        return [entity for entity in self.entities if entity not in self.processed_entities]

    def send_message(self, entity, bot, update):
        question = self.entities[entity]['question']
        bot.send_message(chat_id=update.message.chat_id, text=question)

    def process_entity(self, entity, update):
        if entity == 'participants':
            participants = nlphelpers.extract_list(update.message.text)
            self.meeting_proposal.who = participants
        elif entity == 'proposed_time':
            self.meeting_proposal.when = nlphelpers.extract_list(update.message.text)
        elif entity == 'occasion':
            self.meeting_proposal.why = update.message.text
        elif entity == 'length':
            self.meeting_proposal.length = int(update.message.text)
        else:
            raise RuntimeError('unknown entity: %s' % entity)
