import config


class BaseContext(object):
    name = None

    def is_done(self):
        raise Exception('implementation missing')

    def process(self, bot, update):
        """
        Processes a given input (update) from the user.
        """
        raise Exception('implementation missing')

    def start(self, bot):
        """
        This is how an external trigger starts a context. As such, there is no input.
        """
        raise Exception('implementation missing')


class StateContext(BaseContext):
    current_context = None

    def __init__(self):
        self.current_context = self.decide_next_context()

    def process(self, bot, update):
        # pass input and process
        self.current_context.process(bot, update)

        # check if done and load next state
        if self.current_context.is_done():
            self.current_context = self.decide_next_context(self.current_context)

            # start new context
            if self.current_context is not None:
                self.current_context.start(bot)

    def is_done(self):
        return self.current_context is None

    def decide_next_context(self, last_context=None):
        """
        Decide what context to open next.
        :param last_context: the previous context
        :return: the next context object to process
        """
        raise Exception('implementation missing')


class QuestionAnswerContext(BaseContext):
    """
    Ask a question and receive the user's answer.
    """

    question = None
    answer = None

    def __init__(self, question):
        self.question = question

    def process(self, bot, update):
        self.answer = update.message.text

    def start(self, bot):
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=self.question)

    def is_done(self):
        return self.answer is not None
