import datetime
import os
import icalendar
import arrow


def get_ics_calendar_events(calendar: os.path):
    events_list = []
    with open(calendar, "r") as cal:
        ics_cal = icalendar.Calendar.from_ical(cal.read())
        for i in ics_cal.walk():
            if i.name == "VEVENT":
                start = i["DTSTART"].dt
                event_dict = {"start": {}, "end": {}, "summary": ""}
                if type(start) == datetime.datetime:
                    event_dict["start"]["dateTime"] = arrow.Arrow.fromdatetime(
                        start, start.tzinfo
                    )
                    try:
                        end = i["DTEND"].dt
                        event_dict["end"]["dateTime"] = arrow.Arrow.fromdatetime(
                            end, end.tzinfo
                        )
                    except KeyError:
                        pass
                else:
                    event_dict["start"]["date"] = arrow.Arrow.fromdate(start)
                event_dict["summary"] = i["summary"].to_ical().decode("utf8")
                events_list.append(event_dict)
        return events_list
