import os
from time import sleep

import config
import jarvismailer
import nlphelpers
from context import BaseContext, StateContext, QuestionAnswerContext


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


class ScheduleMeetingContext(StateContext):
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
        super().__init__()
        self.jarvis = jarvis
        self.meeting_proposal = MeetingProposal()

    def start(self, bot):
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text='Okay, let\'s schedule a meeting.')
        self.current_context.start(bot)

    def decide_next_context(self, last_context=None):
        # process last context
        if last_context is not None:
            self.process_finished_context(last_context)
            self.processed_entities.append(last_context.name)

        # instantiate next context
        next_context = None

        next_entity_key = self.get_next_entity()
        if next_entity_key is not None:
            question = self.entities[next_entity_key]['question']

            next_context = QuestionAnswerContext(question)
            next_context.name = next_entity_key
        elif 'email' not in self.processed_entities:
            # mail has not been sent.
            next_context = self.create_email_context()
            next_context.name = 'email'

        return next_context

    def create_email_context(self):
        email = jarvismailer.Email()
        email.subject = self.meeting_proposal.why
        email.message = self.meeting_proposal.get_message()
        email.to = self.meeting_proposal.who
        next_context = jarvismailer.MailerContext(email)
        return next_context

    def get_next_entity(self):
        unprocessed_entities = self.get_unprocessed_entities()
        return next(iter(unprocessed_entities), None)

    def get_unprocessed_entities(self):
        return [entity for entity in self.entities if entity not in self.processed_entities]

    def process_finished_context(self, context):
        if context.name == 'participants':
            participants = nlphelpers.extract_list(context.answer)
            self.meeting_proposal.who = participants
        elif context.name == 'proposed_time':
            self.meeting_proposal.when = nlphelpers.extract_list(context.answer)
        elif context.name == 'occasion':
            self.meeting_proposal.why = context.answer
        elif context.name == 'length':
            self.meeting_proposal.length = int(context.answer)
