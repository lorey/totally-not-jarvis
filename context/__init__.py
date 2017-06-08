class BaseContext(object):
    def is_done(self):
        raise Exception('implementation missing')

    def process(self, bot, update):
        raise Exception('implementation missing')
