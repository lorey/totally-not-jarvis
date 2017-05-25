# Totally not Jarvis

This is a personal assistant bot built with Telegram. I've attempted to lay the foundations for a context-sensitive framework that allows you to switch contexts by issuing new commands while not forgetting about old commands. An example:

```
Jarvis: Karl, what are you planning to do today?
Karl: I have no idea. How is the weather?
Jarvis: The weather is fine.
Jarvis: So what are you planning to do today?
Karl: I'm going to the beach.
Jarvis: Oh, a very good idea.
```

Note: Most other assistants would forget about their initial question (plans for the day) if you issue a new command. But not mine :)

Current features:
- Checking the weather
- Check the next calendar entry
- Ask me to take memos during meetings (based on calendar meetings) and remind me later

Features I'd love to implement:
- get recommendations to keep in touch with people you have not contacted for a while (hubspot integration)
- send meeting reminders via email or sms (based on calendar and hubspot contacts)
- log current position on demand
- save reminders
- let others talk to the bot and play with it