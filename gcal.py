"""
A tool for interacting with the Google calendar.
"""
from __future__ import print_function
# For command-line arguments
import argparse
from src.credentials import get_service
from src.utils import *

# Dates to access the next month.
NOW_DATE = arrow.utcnow().date()
NOW = arrow.utcnow()  # right now
IN30 = NOW.replace(days=+30) # in 30 days

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("command", help="list | agenda | available")
parser.add_argument("--start", default=NOW, help="start of timespan in ISO 8601 format")
parser.add_argument("--end", default=IN30, help="end of timespan in ISO 8601 format")
parser.add_argument(
    "--output-timezone", default="US/Eastern", help="timezone to use for output"
)
parser.add_argument(
    "--query-timezone", default="US/Eastern", help="timezone to use for output"
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
args.start = arrow.get(args.start)
args.end = arrow.get(args.end)
QUERY_TIMEZONE = args.query_timezone
OUTPUT_TIMEZONE = args.output_timezone

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

SPANSTART = args.start
SPANEND = args.end


# Returns a dict containing a cal_interval for each requested calendar:
def get_freebusy(calendarIds=["primary"], timeZone=QUERY_TIMEZONE, start=SPANSTART, end=SPANEND):
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


def list_cals():
    for cal in get_calendars():
        print(cal["summary"] + ": " + cal["id"])


def agenda():
    events = get_calendar_events()
    if not events:
        print("No upcoming events found.")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        a_start = arrow.get(start).format('YYYY-MM-DD h:mm A')
        # print(event)
        print(a_start, event["summary"])


def available():
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


if args.command == "list":
    list_cals()
elif args.command == "agenda":
    agenda()
elif args.command == "available":
    available()
else:
    print("unknown command: " + args.command)

