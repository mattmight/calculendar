import arrow


# A cal_event represents a single event with a start and end time.
# NOTE: all times have type arrow.
import settings


class Event:
    def __init__(self, start, end):
        self.start = arrow.get(start)
        self.end = arrow.get(end)

    def __str__(self):
        return "(" + str(self.start) + "," + str(self.end) + ")"

    # is self entirely lesser than the other event?
    def __lt__(self, other):
        return self.end < other.start

    # creates the smallest event that contains both events:
    def join(self, other):
        return Event(min(self.start, other.start), max(self.end, other.end))

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
                left.format("MMMM DD @ h:mma") + "-" + right.format("h:mma") + " " + tz
            )
        else:
            return (
                left.format("MMMM DD @ h:mma")
                + "-"
                + right.format("MMMM DD @ h:mma" + " " + tz)
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
    if not events:
        if start >= end:
            return []
        else:
            return [Event(start, end)]
    elif events[0].start <= start:
        return events_complement(events[0].end, events[1:], end)
    else:
        head = events[0]
        tail = events[1:]
        return [Event(start, head.start)] + events_complement(head.end, tail, end)


# Merge in order two ordered sequence of events.
def events_union(first_event, second_event):
    if not first_event:
        return second_event
    elif not second_event:
        return first_event
    elif first_event[0] < second_event[0]:
        return [first_event[0]] + events_union(first_event[1:], second_event)
    elif second_event[0] < first_event[0]:
        return [second_event[0]] + events_union(first_event, second_event[1:])
    else:
        joined_event = first_event[0].join(second_event[0])
        return events_union([joined_event] + first_event[1:], second_event[1:])


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
class Interval:
    def __init__(self, start, events, end):
        self.start = start
        self.events = events  # list of (start : arrow,end : arrow)
        self.end = end

    def __invert__(self):
        return Interval(
            self.start, events_complement(self.start, self.events, self.end), self.end
        )

    def __or__(self, other):
        if self.start != other.start or self.end != other.end:
            raise Exception("won't combine calendars with different intervals")
        events_new = events_flatten(events_union(self.events, other.events))
        return Interval(self.start, events_new, self.end)

    def __and__(self, other):
        if self.start != other.start or self.end != other.end:
            raise Exception("won't combine calendars with different intervals")
        return ~(~self | ~other)

    def __str__(self):
        return "\n".join([str(x) for x in self.events])


# A cal_interval with a single event every day:
def cal_daily_event(start, end, start_hour, start_min, end_hour, end_min):
    new_start = start.floor("day")
    new_end = end.replace(days=+1).floor("day")

    def events_daily_event(start, end, start_hour, start_min, end_hour, end_min):
        # reset start date to start of day; end date to end of day
        if end < start:
            return []
        else:
            ev = Event(
                start.replace(hour=start_hour, minute=start_min),
                start.replace(hour=end_hour, minute=end_min),
            )
            evs = events_daily_event(
                start.replace(days=+1), end, start_hour, start_min, end_hour, end_min
            )
            return [ev] + evs

    return Interval(
        start,
        events_daily_event(
            new_start, new_end, start_hour, start_min, end_hour, end_min
        ),
        end,
    )


# A cal_interval where the weekends are a single event:
def cal_weekends(start, end):
    new_start = start.floor("day")
    new_end = end.replace(days=+1).floor("day")

    def events_weekends(start, end):
        # TODO: abstract this to handle different conventions for weekends
        if end < start:
            return []
        elif start.weekday() in settings.weekend_num:
            return [
                Event(start, start.replace(days=+1).floor("day"))
            ] + events_weekends(start.replace(days=+1), end)
        else:
            return events_weekends(start.replace(days=+1), end)

    return Interval(start, events_flatten(events_weekends(new_start, new_end)), end)
