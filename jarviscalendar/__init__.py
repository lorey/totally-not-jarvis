import datetime
import requests
from icalendar import Calendar
from icalendar import Event

import config


def get_events():
    url = config.ICAL_URL
    response = requests.get(url)

    cal = Calendar.from_ical(response.content.decode('utf-8'))
    events = [IcalEvent(comp) for comp in cal.subcomponents if type(comp) == Event]
    return events


def get_next_event():
    next_event = None

    events = [e for e in get_events() if not e.is_full_day()]
    for event in events:
        if next_event is None or next_event.get_start() > event.get_start() > datetime.datetime.now(tz=datetime.timezone.utc):
            next_event = event

    return next_event


class IcalEvent(object):
    ical_event = None

    def __init__(self, ical):
        self.ical_event = ical

    def is_full_day(self):
        return type(self.ical_event['dtstart'].dt) == datetime.date

    def get_start(self):
        return self.ical_event['dtstart'].dt

    def get_end(self):
        return self.ical_event['dtend'].dt

    def get_summary(self):
        return self.ical_event['summary']

    def get_description(self):
        return self.ical_event['description']

    def get_attendee_emails(self):
        if 'attendee' in self.ical_event:
            return [str(attendee).replace('mailto:', '') for attendee in self.ical_event['attendee']]
        return []
