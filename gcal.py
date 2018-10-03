"""
A tool for interacting with the Google calendar.
"""
# Python Version Compatibility
from __future__ import print_function
# For command-line arguments
import argparse
# Module functions
import settings
import src.credentials
from src.utils import *

# Dates to access the next month.
NOW_DATE = arrow.utcnow().date()
NOW = arrow.utcnow()  # right now
IN30 = NOW.replace(days=+30)  # in 30 days

start_work = arrow.get(settings.START_WORK, 'H:mm A')
end_work = arrow.get(settings.END_WORK, 'H:mm A')


# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("command", help="list | agenda | available")
parser.add_argument("--start", default=NOW, help="start of timespan")
parser.add_argument("--end", default=IN30, help="end of timespan")
parser.add_argument(
    "--query-timezone", default=settings.TIMEZONE, help="timezone to use for output"
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
START = arrow.get(args.start)
END = arrow.get(args.end)
BUSY = args.busy_calendars
FREE = args.free_calendars

service = src.credentials.get_service()


# Get the next several events:
def get_calendar_events(calendarId="primary", maxResults=10):
    events_result = (
        service.events()
        .list(
            calendarId=calendarId,
            timeMin=START.isoformat(),
            maxResults=maxResults,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])


# Returns a dict containing a cal_interval for each requested calendar:
def get_freebusy(
    calendarIds=["primary"], timeZone=QUERY_TIMEZONE, start=START, end=END
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
    for id, times in cals.items():
        busy_times = times["busy"]
        revs = []  # events in reverse order
        for t in busy_times:
            ev_start = arrow.get(t["start"])
            ev_end = arrow.get(t["end"])
            ev = Event(ev_start, ev_end)
            # accumulate events in reverse order:
            revs = [ev] + revs
        cal_index[id] = Interval(start, revs[::-1], end)
    return cal_index


# check to see if the calendar is synthetic;
# if synthentic, will be computed against query timezone.

# TODO: Add support for synthetic calendars in other timezones.


def get_cal(cal_index, cal_id):
    if cal_id == "weekend":
        return cal_weekends(START, END)
    if cal_id == "weekday":
        return ~cal_weekends(START, END)
    if cal_id == "workhours":
        return cal_daily_event(START, END, start_work.hour, start_work.minute, end_work.hour, end_work.minute)
    else:
        return cal_index[cal_id]


def list_cals():
    cals_result = service.calendarList().list().execute()
    cals = cals_result.get("items", [])
    for cal in cals:
        print(cal["summary"] + ": " + cal["id"])


def agenda():
    events = []
    for cal in BUSY:
        cal_events = get_calendar_events(calendarId=cal)
        events += cal_events
    if not events:
        print("No upcoming events found.")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        a_start = arrow.get(start).format("YYYY-MM-DD h:mm A")
        # print(event)
        print(a_start, event["summary"])


def available():
    calidx = get_freebusy(BUSY + FREE)
    my_busy = Interval(START, [], END)
    my_free = Interval(START, [Event(START, END)], END)
    for cal_id in BUSY:
        my_busy = my_busy | get_cal(calidx, cal_id)
    for cal_id in FREE:
        my_free = my_free & get_cal(calidx, cal_id)
    available = ~my_busy & my_free
    # print out availability:
    for ev in available.events:
        print(ev.human_str(QUERY_TIMEZONE))


if args.command == "list":
    list_cals()
elif args.command == "agenda":
    agenda()
elif args.command == "available":
    available()
else:
    print("unknown command: " + args.command)
