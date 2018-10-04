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

```
office_availability = ~(primary_calendar | out_of_town) & workhours & weekdays

phone_availability = ~primary_calendar & workhours & weekdays

joint_availability = my_availability & your_availability
```




## TODO

 + Extract the Boolean calculus of calendars logic into a seperate module. [Done]
 + Allow filtering of calendar events with `lambda` filter over events.
 + Implement a reasonable agenda mode output for upcoming events.
 + Add support for converting .ics files into calendar intervals. [Done]
 + Add support for Office 365 API.
 + Add support for computing joint availability of multiple users.

## Warnings

This code needs clean-up. [In progress...]

I'm releasing it under the principles of [the CRAPL](http://matt.might.net/articles/crapl/).


## Requirements

You will need to create a `credentials.json` to access the Google Calendar API.

You can copy the steps in the [Python Google Calendar API quickstart tutorial](https://developers.google.com/calendar/quickstart/python) to obtain this.

When you save the credentials, ensure you remember the location, as it will be required. 



## Usage

```
usage: gcal.py <command>
               [--start START] [--end END]
               [--output-timezone OUTPUT_TIMEZONE]
               [--query-timezone QUERY_TIMEZONE]
               [--busy-calendars calendar-id [calendar-id ...]]
               [--free-calendars calendar-id [calendar-id ...]]
               [--input [Paths to .ics files...]]
               [--all]
```

The `command` can be `list_cals` or `agenda` or `available` or `import`.


## Examples

###Availability
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


Availability on phone:
May 07 @ 10:00am-11:00am
May 07 @ 02:00pm-02:30pm
May 08 @ 11:45am-12:00pm
May 08 @ 03:00pm-04:30pm
May 15 @ 11:00am-02:00pm

```

###Agenda
Get easy agendas:
```bash
echo "Green Bay Packers Agenda: "
python gcal.py agenda \
 --busy-calendars nfl_9_%47reen+%42ay+%50ackers#sports@group.v.calendar.google.com

```
This would output:
```bash
Green Bay Packers Agenda:
2018-10-07 1:00 PM Packers @ Lions
2018-10-15 8:15 PM 49ers @ Packers
2018-10-28 4:25 PM Packers @ Rams
2018-11-04 8:20 PM Packers @ Patriots
2018-11-11 1:00 PM Dolphins @ Packers
2018-11-15 8:20 PM Packers @ Seahawks
```

###List
The default is to only list Calendars imported into your `settings.ini` file

List Out Calendars
```bash
echo "My Calendars: "
python gcal.py list 
 ```
 
 Would produce something like this:
 ```bash
 My Calendars:
 my_gmail@gmail.com: my_gmail@gmail.com
 green bay packers : nfl_9_%47reen+%42ay+%50ackers#sports@group.v.calendar.google.com
 contacts : #contacts@group.v.calendar.google.com
 ```
 
 To ensure all google and imported calendars are listed, use `-a`:
 
 ```bash
echo "My Calendars: "
python gcal.py list -a 
 ```
 
This would list all calendars, imported of otherwise, and then prompt you to save them
 ```bash
 My Calendars:
 my_gmail@gmail.com: my_gmail@gmail.com
 green bay packers : nfl_9_%47reen+%42ay+%50ackers#sports@group.v.calendar.google.com
 contacts : #contacts@group.v.calendar.google.com
 Would you like to import these into your settings for future use?
 ```
 
 ###Importing .ICS Calendars
You can now import .ics files like so:

```bash
python gcal import -i ./calendar.ics
```
This would prompt you to name the file for future use, and then list it as it appears in your settings.ini
```bash
What would you like to name this calendar? my_cal
 my_gmail@gmail.com: my_gmail@gmail.com
 green bay packers : nfl_9_%47reen+%42ay+%50ackers#sports@group.v.calendar.google.com
 contacts : #contacts@group.v.calendar.google.com
 my_cal : ./calendar.ics
```