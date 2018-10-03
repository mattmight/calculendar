import arrow
# A cal_event represents a single event with a start and end time.
# Note: all times have type arrow.
class cal_event:

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
                left.format("MMMM DD @ h:mma")
                + "-"
                + right.format("h:mma")
                + " "
                + tz
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
    new_end = end.replace(days=+1).floor("day")
    def events_weekends(start, end):
        # TODO: abstract this to handle different conventions for weekends
        if end < start:
            return []
        elif start.weekday() == 5 or start.weekday() == 6:
            return [
                cal_event(start, start.replace(days=+1).floor("day"))
            ] + events_weekends(start.replace(days=+1), end)
        else:
            return events_weekends(start.replace(days=+1), end)
    return cal_interval(start, events_flatten(events_weekends(new_start, new_end)), end)