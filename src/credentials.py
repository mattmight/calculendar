# On getting API access and access to your account:

# To figure out how to set up access to the Google API ('client_secret.json')
# I followed the quickstart guide here:

#  https://developers.google.com/calendar/quickstart/python

# The first time you run the script it will open a web authentication dialogue,
# and then it will store your credentials in 'credentials.json'

# If you want to run this script on a remote server, authenticate locally first and
# then copy the these files to that remote server.

# import os
# from googleapiclient.discovery import build
# from httplib2 import Http
# from oauth2client import file, client, tools
# import settings

from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import settings

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Credentials should be stored in settings.CREDENTIALS_DIR
def get_service():
    """
    This is straight out of the tutorial at:
    https://developers.google.com/calendar/quickstart/python
    """
    # SCOPES = "https://www.googleapis.com/auth/calendar"
    # cred = os.path.join(settings.CREDENTIALS_DIR, "credentials.json")
    # store = file.Storage("token.json")
    # creds = store.get()
    # if not creds or creds.invalid:
    #     flow = client.flow_from_clientsecrets(cred, SCOPES)
    #     creds = tools.run_flow(flow, store)
    # service = build("calendar", "v3", http=creds.authorize(Http()))
    # return service

   
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    # settings.ini contains the location of the credentials directory
    # It must contain credentials.json as acquired from the quickstart tutorial.
    # It will place token.pickle there after it has authenticated.

    token_pickle_file = os.path.join(settings.CREDENTIALS_DIR,'token.pickle')
    credentials_file = os.path.join(settings.CREDENTIALS_DIR,'credentials.json')

    if os.path.exists(token_pickle_file):
        with open(token_pickle_file, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(token_pickle_file, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds) 

    return service

def main():
    get_service()

if __name__  == "__main__":
    main()
