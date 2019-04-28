import configparser
import os

import arrow
import pytz
from arrow.parser import ParserError
from src.utils import safe_input as input


weekday_dict = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

zones = pytz.all_timezones  # list of usable timezones


def confirm_input(user_input):
    print("I got the following: ")
    if type(user_input) == list:
        for i in user_input:
            print(i)
    else:
        print(user_input)
    confirm = input("Is this accurate? ")
    if "y" in confirm.lower():
        return True
    else:
        return False


def get_credentials_directory(location=None):
    """
    Gets credentials directory from user input
    """
    if not location:
        try:
            credentials = os.getenv("HOME") + "/etc/keys/google-api/"
            return get_credentials_directory(credentials)
        except TypeError:
            pass
    elif os.path.exists(os.path.join(location + "/credentials.json")):
        credentials = location
        if confirm_input(credentials):
            return credentials
        else:
            return get_credentials_directory()
    elif "credentials.json" in location:
        credentials = os.path.dirname(location)
        if confirm_input(credentials):
            return credentials
        else:
            return get_credentials_directory()
    loc = input("Path to credentials.json: ")
    return get_credentials_directory(location=loc)


def get_timezone(zones: list):
    """
    Gets timezone from user input
    """
    user_input = input(
        'What timezone do you reside in? (Format: "US/Pacific", "US/Eastern", etc): '
    )
    smaller_zones = []
    if user_input not in zones:
        for zone in zones:
            if user_input.lower() in zone.lower():
                smaller_zones.append(zone)
        if len(smaller_zones):
            print("Zones that match that input are: ")
            for zone in smaller_zones:
                print(zone)
            return get_timezone(smaller_zones)
    else:
        if confirm_input(user_input):
            return user_input
        else:
            return get_timezone()


def get_work_hours():
    """
    Gets work hours from user input
    """
    user_reply = input("What are your work hours? (Format: 9:00 AM-5:00 PM) ")
    user_reply_list = user_reply.split("-")
    for i in user_reply_list:
        try:
            arrow.get(i, "H:mm A")
        except ParserError:
            print("Invalid Output")
            return get_work_hours()
    if confirm_input(user_reply_list):
        return user_reply_list
    else:
        return get_work_hours()


def get_weekends():
    """
    Gets weekends from user input
    """
    user_reply = input("What days of the week are your weekends? ")
    days = weekday_dict.keys()
    ret = []
    for day in days:
        if day.lower() in user_reply.lower():
            ret.append(day)
    if confirm_input(ret):
        return ret
    else:
        return get_weekends()


def set_weekend(parser, days: list):
    for day in days:
        parser.set("Weekend Days", day.lower(), "True")


def setup_settings():
    """
    Create settings.ini from user input
    """
    if not os.path.exists("settings.ini"):
        parser = configparser.ConfigParser(interpolation=None)
        parser.add_section("Settings")
        parser.add_section("Weekend Days")
        parser.add_section("Calendars")
        for k, v in weekday_dict.items():
            parser.set("Weekend Days", k, "False")
        parser.set("Settings", "credentials_dir", get_credentials_directory())
        weekend_days = get_weekends()
        set_weekend(parser, weekend_days)
        parser.set("Settings", "timezone", get_timezone(zones))
        work_hours = get_work_hours()
        parser.set("Settings", "start_work", work_hours[0])
        parser.set("Settings", "end_work", work_hours[1])

        with open("settings.ini", "w") as ini:
            parser.write(ini)


setup_settings()

parser = configparser.ConfigParser(interpolation=None)
parser.read("settings.ini")


CREDENTIALS_DIR = parser.get("Settings", "credentials_dir")
TIMEZONE = parser.get("Settings", "timezone")
START_WORK = parser.get("Settings", "start_work")
END_WORK = parser.get("Settings", "end_work")


def get_weekend_num():
    weekend = []
    for i in parser["Weekend Days"]:
        if parser.getboolean("Weekend Days", i):
            weekend.append(weekday_dict[i])
    return weekend


weekend_num = get_weekend_num()

calendars_imported = len(
    parser.options("Calendars")
)  # returns 0 (False) if calendars not imported


def set_calendar(cal_name, cal_id):
    parser.set("Calendars", cal_name, cal_id)
    with open("settings.ini", "w") as config:
        parser.write(config)


def list_imported_calendars():
    for cal, id in parser.items("Calendars"):
        print(cal, ":", id)
    return parser.items("Calendars")


def get_imported_calendar_by_name(name: str):
    for cal, id in parser.items("Calendars"):
        if name.lower() == cal.lower() and name.lower() != "primary":
            return id
    return print("Calendar with name " + name + " not found")
