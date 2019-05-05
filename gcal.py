"""
A tool for interacting with the Google calendar.
"""
# Python Version Compatibility
from __future__ import print_function

# For command-line arguments
import argparse

# Module functions
import src.credentials
from src.utils import *
from src.utils import safe_input as input
from src.ics import get_ics_calendar_events


# Dates to access the next month.
NOW_DATE = arrow.utcnow().date()
NOW = arrow.utcnow()  # right now
IN30 = NOW.replace(days=+30)  # in 30 days

start_work = arrow.get(settings.START_WORK, "H:mm A").replace(tzinfo=settings.TIMEZONE)
end_work = arrow.get(settings.END_WORK, "H:mm A").replace(tzinfo=settings.TIMEZONE)

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("command", help="list | agenda | available | import")
parser.add_argument("--start", default=NOW, help="start of timespan")
parser.add_argument("--end", default=IN30, help="end of timespan")
parser.add_argument(
    "--query-timezone", default=settings.TIMEZONE, help="timezone to use for output"
)
parser.add_argument(
    "--output-timezone", default=settings.TIMEZONE, help="timezone to use for output"
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
parser.add_argument(
    "-i", "--input", default=[], nargs="+", help="paths to .ics calendars to import"
)
parser.add_argument("-a", "--all", action="store_true")
args = parser.parse_args()
QUERY_TIMEZONE = args.query_timezone or args.output_timezone
START = arrow.get(args.start)
END = arrow.get(args.end)
BUSY = get_calendars_from_imported(args.busy_calendars)
FREE = get_calendars_from_imported(args.free_calendars)
INPUT = args.input

gcal_service = src.credentials.get_service()


# Get the next several events:
def get_calendar_events(calendarId="primary", maxResults=10):
    if ".ics" in calendarId:
        return get_ics_calendar_events(calendarId)
    else:
        events_result = (
            gcal_service.events()
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
    freebusy_result = gcal_service.freebusy().query(body=fb_q).execute()
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
        return cal_daily_event(
            START,
            END,
            start_work.hour,
            start_work.minute,
            end_work.hour,
            end_work.minute,
        )
    else:
        return cal_index[cal_id]


def list_cals():
    if settings.calendars_imported and not args.all:
        settings.list_imported_calendars()
    else:
        imported = settings.list_imported_calendars()
        imported_names = [cal[0] for cal in imported]
        cals_result = gcal_service.calendarList().list().execute()
        cals = cals_result.get("items", [])
        for cal in cals:
            if cal["summary"].lower() not in imported_names:
                print(cal["summary"] + ": " + cal["id"])
        user_response = input(
            "Would you like to import these into your settings for future use? "
        )
        if "y" in user_response.lower():
            for cal in cals:
                settings.set_calendar(cal["summary"], cal["id"])


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
    calidx = get_freebusy(calendarIds=BUSY)
    my_busy = Interval(START, [], END)
    my_free = Interval(START, [Event(START, END)], END)
    for cal_id in BUSY:
        my_busy = my_busy | get_cal(calidx, cal_id)
    for cal_id in FREE:
        my_free = my_free & get_cal(calidx, cal_id)
    available = ~my_busy & my_free
    # print out availability:
    for ev in available.events:
        print(ev.human_str())


def import_cal():
    if not INPUT:
        print("Import command requires -i or --input !")
    else:
        for path in INPUT:
            name = input("What would you like to name this calendar? ")
            settings.set_calendar(name, path)
    list_cals()


if __name__ == "__main__":
    if args.command.lower() == "list":
        list_cals()
    elif args.command.lower() == "agenda":
        agenda()
    elif args.command.lower() == "available":
        available()
    elif args.command.lower() == "import":
        import_cal()
    else:
        print("unknown command: " + args.command)
