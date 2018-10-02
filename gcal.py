"""
A tool for interacting with the Google calendar.
"""
from __future__ import print_function

# For command-line arguments
import argparse

# For handling time
from datetime import datetime, timedelta
import dateutil.parser
import arrow

from credentials import get_service


# Dates to access the next month.
NOW_DATE = datetime.utcnow()

NOW = NOW_DATE.isoformat() + "Z"  # right now
IN30 = (NOW_DATE + timedelta(days=30)).isoformat() + "Z"  # in 30 days

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("command", help="list | agenda | available")
parser.add_argument("--start", default=NOW, help="start of timespan in ISO 8601 format")
parser.add_argument("--end", default=IN30, help="end of timespan in ISO 8601 format")
parser.add_argument(
    "--output-timezone", default="US/Central", help="timezone to use for output"
)
parser.add_argument(
    "--query-timezone", default="US/Central", help="timezone to use for output"
)
parser.add_argument(
    "--busy-calendars",
    metavar="calendar-id",
    default=["primary"],
    nargs="+",
    help="calendar ids to use for busy information",
)
parser.add_argument(
    "--free-calendars",
    metavar="calendar-id",
    default=[],
    nargs="+",
    help="calendar ids to use for free information",
)
args = parser.parse_args()
QUERY_TIMEZONE = args.query_timezone
OUTPUT_TIMEZONE = args.output_timezone


# Time helpers
def isoformat_to_datetime(s):
    d = dateutil.parser.parse(s)
    return d


# A cal_event represents a single event with a start and end time.
# Note: all times have type arrow.
class cal_event:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __str__(self):
        return "(" + str(self.start) + "," + str(self.end) + ")"

    # is self entirely lesser than the other event?
    def __lt__(self, other):
        return self.end < other.start

    # creates the smallest event that contains both events:
    def join(self, other):
        return cal_event(min(self.start, other.start), max(self.end, other.end))

    # does this event overlap with another event?
    def intersects(self, other):
        # check to see if neither is entirely lesser than the other
        # corner case: returns True if they are adjacent
        return not ((self < other) or (other < self))

    # print a human readable string:
    def human_str(self, tz):

        left = self.start.to(tz)
        right = self.end.to(tz)

        left_date = left.format("YYYY-MM-DD")
        right_date = right.format("YYYY-MM-DD")
        if left_date == right_date:
            return (
                left.format("MMMM DD @ hh:mma")
                + "-"
                + right.format("hh:mma")
                + " "
                + tz
            )
        else:
            return (
                left.format("MMMM DD @ hh:mma")
                + "-"
                + right.format("MMMM DD @ hh:mma" + " " + tz)
            )


# Compute the complement of a sequence events between start and end.
#
# For example, if:
#   the start is 4pm
#   the end is 10pm
#   events is [(5pm,7pm)]
#  then the complement is:
#   [(4pm,5pm), (7pm,10pm)]
#
# This converts between "busy" and "available."
def events_complement(start, events, end):
    if events == []:
        if start >= end:
            return []
        else:
            return [cal_event(start, end)]
    elif events[0].start <= start:
        return events_complement(events[0].end, events[1:], end)
    else:
        head = events[0]
        tail = events[1:]
        return [cal_event(start, head.start)] + events_complement(head.end, tail, end)


# Merge in order two ordered sequence of events.
def events_union(eventsA, eventsB):
    if not eventsA:
        return eventsB
    elif not eventsB:
        return eventsA
    elif eventsA[0] < eventsB[0]:
        return [eventsA[0]] + events_union(eventsA[1:], eventsB)
    elif eventsB[0] < eventsA[0]:
        return [eventsB[0]] + events_union(eventsA, eventsB[1:])
    else:
        joined_event = eventsA[0].join(eventsB[0])
        return events_union([joined_event] + eventsA[1:], eventsB[1:])


# Combines all overlapping events in an ordered sequence of events:
def events_flatten(events):
    if len(events) <= 1:
        return events
    else:
        a = events[0]
        b = events[1]
        if a.intersects(b):
            return events_flatten([a.join(b)] + events[2:])
        else:
            return [a] + events_flatten(events[1:])


# A cal_interval represents an interval of time on a calendar
# within the interval are events at specific times.
class cal_interval:
    def __init__(self, start, events, end):
        self.start = start
        self.events = events  # list of (start : arrow,end : arrow)
        self.end = end

    def __invert__(self):
        return cal_interval(
            self.start, events_complement(self.start, self.events, self.end), self.end
        )

    def __or__(self, other):
        if self.start != other.start or self.end != other.end:
            raise Exception("won't combine calendars with different intervals")

        events_new = events_flatten(events_union(self.events, other.events))

        return cal_interval(self.start, events_new, self.end)

    def __and__(self, other):
        if self.start != other.start or self.end != other.end:
            raise Exception("won't combine calendars with different intervals")

        return ~(~self | ~other)

    def __str__(self):
        return "\n".join([str(x) for x in self.events])


# A cal_interval with a single event every day:
def cal_daily_event(start, end, start_hour, start_min, end_hour, end_min):

    new_start = start.floor("day")
    new_end = end.shift(days=+1).floor("day")

    def events_daily_event(start, end, start_hour, start_min, end_hour, end_min):
        # reset start date to start of day; end date to end of day

        if end < start:
            return []
        else:
            ev = cal_event(
                start.replace(hour=start_hour, minute=start_min),
                start.replace(hour=end_hour, minute=end_min),
            )
            evs = events_daily_event(
                start.shift(days=+1), end, start_hour, start_min, end_hour, end_min
            )
            return [ev] + evs

    return cal_interval(
        start,
        events_daily_event(
            new_start, new_end, start_hour, start_min, end_hour, end_min
        ),
        end,
    )


# A cal_interval where the weekends are a single event:
def cal_weekends(start, end):

    new_start = start.floor("day")
    new_end = end.shift(days=+1).floor("day")

    def events_weekends(start, end):
        # TODO: abstract this to handle different conventions for weekends

        if end < start:
            return []
        elif start.weekday() == 5 or start.weekday() == 6:
            return [
                cal_event(start, start.shift(days=+1).floor("day"))
            ] + events_weekends(start.shift(days=+1), end)
        else:
            return events_weekends(start.shift(days=+1), end)

    return cal_interval(start, events_flatten(events_weekends(new_start, new_end)), end)


service = get_service()

# Get a list of all calendars:
def get_calendars():
    cals_result = service.calendarList().list().execute()
    cals = cals_result.get("items", [])
    return cals


# Get the next several events:
def get_calendar_events(calendarId="primary", maxResults=10):
    events_result = (
        service.events()
        .list(
            calendarId=calendarId,
            timeMin=SPANSTART.isoformat(),
            maxResults=maxResults,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])


# TODO: Abstract out the timezones

SPANSTART = arrow.get(isoformat_to_datetime(args.start)).to(QUERY_TIMEZONE)
SPANEND = arrow.get(isoformat_to_datetime(args.end)).to(QUERY_TIMEZONE)
# Returns a dict containing a cal_interval for each requested calendar:


def get_freebusy(
    calendarIds=["primary"], timeZone=QUERY_TIMEZONE, start=SPANSTART, end=SPANEND
):

    fb_q = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": timeZone,
        "items": [{"id": id} for id in calendarIds],
    }

    freebusy_result = service.freebusy().query(body=fb_q).execute()

    cals = freebusy_result["calendars"]

    cal_index = {}

    for id, times in list(cals.items()):
        busy_times = times["busy"]

        revs = []  # events in reverse order

        for t in busy_times:
            ev_start = arrow.get(isoformat_to_datetime(t["start"]))
            ev_end = arrow.get(isoformat_to_datetime(t["end"]))
            ev = cal_event(ev_start, ev_end)
            # accumulate events in reverse order:
            revs = [ev] + revs

        cal_index[id] = cal_interval(start, revs[::-1], end)

    return cal_index


# check to see if the calendar is synthetic;
# if synthentic, will be computed against query timezone.

# TODO: Add support for synthetic calendars in other timezones.


def get_cal(cal_index, cal_id):
    if cal_id == "weekend":
        return cal_weekends(SPANSTART, SPANEND)
    if cal_id == "weekday":
        return ~cal_weekends(SPANSTART, SPANEND)
    if cal_id == "workhours":
        return cal_daily_event(SPANSTART, SPANEND, 9, 00, 17, 00)
    else:
        return cal_index[cal_id]


if args.command == "list":
    for cal in get_calendars():
        print(cal["summary"] + ": " + cal["id"])
    exit()
elif args.command == "agenda":
    events = get_calendar_events()
    if not events:
        print("No upcoming events found.")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        print(event)
        print(start, event["summary"])
    exit()
elif args.command == "available":
    calidx = get_freebusy(args.busy_calendars + args.free_calendars)
    my_busy = cal_interval(SPANSTART, [], SPANEND)
    my_free = cal_interval(SPANSTART, [cal_event(SPANSTART, SPANEND)], SPANEND)
    for id in args.busy_calendars:
        my_busy = my_busy | get_cal(calidx, id)
    for id in args.free_calendars:
        my_free = my_free & get_cal(calidx, id)
    available = ~my_busy & my_free
    # print out availability:
    for ev in available.events:
        print(ev.human_str(OUTPUT_TIMEZONE))
else:
    print("unknown command: " + args.command)
