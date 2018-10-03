# Calculendar

A command line tool for computing availability.

It currently supports the Google Calendar API.

(If you want simple Google Calendar manipulation through the command line, you may want [gcalcli](https://pypi.org/project/gcalcli/).)

Internally, the tool implements a Boolean calculus over calendar intervals to
compute availability.  This allows you to define availability as a function of
several calendars.

For instance, you might have a primary calendar personal calendar, but also a
shared team calendar, and you will need to consider both for conflicts.

You might also want to define a calendar that specifies that there are
certain times of the day and days the week where you are available for
appointments.  Or, if a meeting must be held in a certain room, you can pull in
the in-use calendar for that room and invert it to obtain its available times.

For example:

```python
office_availability = ~(primary_calendar | out_of_town) & workhours & weekdays

phone_availability = ~primary_calendar & workhours & weekdays

joint_availability = my_availability & your_availability
```




## TODO

 + Extract the Boolean calculus of calendars logic into a seperate module.
 + Allow filtering of calendar events with `lambda` filter over events.
 + Implement a reasonable agenda mode output for upcoming events.
 + Add support for converting .ics files into calendar intervals.
 + Add support for Office 365 API.
 + Add support for computing joint availability of multiple users.

## Warnings

This code needs clean-up.

I'm releasing it under the principles of [the CRAPL](http://matt.might.net/articles/crapl/).


## Requirements

You will need to create an API key to access the Google Calendar API.

You can copy the steps in the [Python Google Calendar API quickstart tutorial](https://developers.google.com/calendar/quickstart/python) to obtain this.

It expects that `$HOME/etc/keys/google-api` exists and is read-writeable.

The `client_secret.json` provided by the Google Calendar API belongs here, and
it will place the generated `credentials.json` file here after the first run
and authentication.


## Usage

```
usage: gcal.py [--start START] [--end END]
               [--output-timezone OUTPUT_TIMEZONE]
               [--query-timezone QUERY_TIMEZONE]
               [--busy-calendars calendar-id [calendar-id ...]]
               [--free-calendars calendar-id [calendar-id ...]]
               <command> 
```

The `command` can be `list_cals` or `agenda` or `available`.


## Examples

```bash
echo "Availability at office: "
python gcal.py available \
 --busy-calendars primary \
                  <id-of-out-of-town-calendar> \
 --free-calendars workhours weekday


echo "Availability on phone: "
python gcal.py available \
 --busy-calendars primary \
 --free-calendars workhours weekday
```

This might output:

```
Availability at office:
May 07 @ 10:00am-11:00am
May 07 @ 02:00pm-02:30pm
May 15 @ 11:00am-02:00pm
May 15 @ 02:30pm-05:00pm
May 16 @ 09:30am-11:30am
May 16 @ 12:30pm-05:00pm
May 17 @ 11:00am-03:00pm

Availability on phone:
May 07 @ 10:00am-11:00am
May 07 @ 02:00pm-02:30pm
May 08 @ 11:45am-12:00pm
May 08 @ 03:00pm-04:30pm
May 15 @ 11:00am-02:00pm
May 15 @ 02:30pm-05:00pm
May 16 @ 09:30am-11:30am
May 16 @ 12:30pm-05:00pm
May 17 @ 11:00am-03:00pm
May 21 @ 04:00pm-05:00pm
May 22 @ 02:00pm-05:00pm
May 23 @ 04:00pm-05:00pm
May 24 @ 04:00pm-05:00pm
May 25 @ 09:30am-05:00pm
May 28 @ 09:30am-05:00pm
May 29 @ 10:00am-05:00pm
May 30 @ 09:30am-05:00pm
May 31 @ 10:00am-05:00pm
June 01 @ 09:30am-05:00pm
June 04 @ 02:00pm-05:00pm
June 05 @ 02:00pm-05:00pm
```

