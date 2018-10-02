# On getting API access and access to your account:

# To figure out how to set up access to the Google API ('client_secret.json')
# I followed the quickstart guide here:

#  https://developers.google.com/calendar/quickstart/python

# The first time you run the script it will open a web authentication dialogue,
# and then it will store your credentials in 'credentials.json'

# If you want to run this script on a remote server, authenticate locally first and
# then copy the these files to that remote server.

import os
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


def get_credentials_directory(location='C:/Users/Camer/Desktop/credentials.json'):
    if not location:
        try:
            credentials = os.getenv("HOME") + "/etc/keys/google-api/"
            return credentials
        except TypeError:
            print("Your credentials.json does not seem to be in the expected location")
    elif os.path.exists(os.path.join(location + "credentials.json")):
        credentials = location
        return credentials
    elif "credentials.json" in location:
        credentials = os.path.dirname(location)
        return credentials
    loc = input("Path to credentials.json: ")
    return get_credentials_directory(location=loc)


# Setup access to the Calendar API:
# This may require an interactive web authentication the fist time.

# Credentials should be stored in API_KEYS_DIR.
def get_service():
    SCOPES = "https://www.googleapis.com/auth/calendar"
    cred = os.path.join(get_credentials_directory(), 'credentials.json')
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(cred, SCOPES)
        creds = tools.run_flow(flow, store)
    service = build("calendar", "v3", http=creds.authorize(Http()))
    return service

