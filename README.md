![Not a picture of Jarvis](.github/robot.jpg)

# Totally not Jarvis - a personal assistant bot

This is a personal assistant bot built with [Telegram](https://github.com/python-telegram-bot/python-telegram-bot). I've attempted to lay the foundations for a framework that allows you to switch intents by issuing new commands while not forgetting about old intents. An example:

```
Jarvis: Karl, what are you planning to do today?
Karl: I have no idea. How is the weather?
Jarvis: The weather is fine.
Jarvis: So what are you planning to do today?
Karl: I'm going to the beach.
Jarvis: Oh, a very good idea.
```

Note: Most other bots would forget about their initial question (plans for the day) if you issue a new command. But not mine :)

Current skills:
- Ask me to take memos during meetings and remind me later (based on iCAL calendar entries)
- Send emails that propose dates for a meeting
- Check the weather (based on [OpenWeatherMap](https://openweathermap.org/api))
- Check the next calendar entry (iCal integration that works with Google Calendar)

Features:
- Context classes that encapsulate dialogs, e.g. checking the weather.
- no hard dependency on Telegram, so I can use a voice interface like Alexa or Google Home later

Skills I'd love to implement:
- smart scheduling: automatically derive possible timeslots when scheduling a meeting or use something like doodle
- get recommendations to keep in touch with people you have not contacted for a while (hubspot integration)
- send meeting reminders via email or sms (based on calendar and hubspot contacts)
- log current position on demand
- save reminders
- let others talk to the bot and play with it
- send contacts your current phone number, etc.
- delay tasks (e.g. meeting memos: delay so that the dialog reappears after 10 minutes)
- email meeting memos to participants
- create drafts of emails via smtp


## Example of meeting time proposals
The command `/schedule` triggers the creation of an meeting proposal that is sent to all participants after you have answered all necessary questions. It looks like this:

> Hello,
>
> this is Jarvis, personal assistant of Karl Lorey. For your appointment ('Learning more about Jarvis, my personal
> assistant') I propose a time slot of 60 minutes on one of the following dates:
> - Tomorrow
> - Friday
>
> Currently, I just send the proposals, so please hit 'reply all' to get Karl Lorey back into the loop.
> __________
> Jarvis
> Personal Assistant of Karl Lorey
>
> You can find my code at https://github.com/lorey/totally-not-jarvis


## The config file: config.py

The config file should look like this (not included for obvious reasons):

```python
# names
BOT_NAME = 'Jarvis'
OWNER_NAME = 'Karl Lorey'
POSITION = {'lat': 49.01, 'lon': 8.4}

# telegram
TELEGRAM_TOKEN = ''
TELEGRAM_CHAT_ID = ''

# weather
OPENWEATHERMAP_API_KEY = ''

# calendar (name: url)
ICAL_URLS = {
    "private": "https://calendar.google.com/calendar/ical/exampleexampleexample/basic.ics",
    "work": "https://calendar.google.com/calendar/ical/justanexample/public/basic.ics",
}

# email
EMAIL_ADDRESS_JARVIS = 'jarvis@mail.com'
EMAIL_ADDRESS_CC = 'your@mail.com'
EMAIL_SMTP_HOST = 'www.server.com'
EMAIL_SMTP_PORT = 465
EMAIL_IMAP_USER = 'jarvis'
EMAIL_IMAP_PASSWORD = 'captainwho?'


```


## Implement own functionality

To implement own skills, you just have to extend the base class and make sure a command puts the context on top of the contexts stack. We'll start with a `RepeatContext` that just repeats your input:

```python
class RepeatContext(BaseContext):
    def is_done(self):
        return True  # executed only once

    def process(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text=update.message.text.replace('/repeat ', '')
```

The base class only has two methods that you need to implement:
- `process` receives all user input while the context is active (`is_done() == False`). You can basically do whatever you want as long as you want. Messages can be accessed with `update.message.text`.
- `is_done` ist self-explanatory. If true, the context will be removed and the context before that will start again.

Afterwards, you just have to check for the command and open the context:

```python
class DefaultContext(BaseContext):
    # ...

    def process(self, bot, update):
        if update.message is not None and update.message.text.startswith('/repeat '):
            # starts the repeat context
            context = RepeatContext()  # crate context
            self.jarvis.contexts.append(context)  # put it on the stack
            context.process(bot, update)  # start by processing for the first time
        else:
            bot.send_message(chat_id=update.message.chat_id, text="I don't understand")
```
