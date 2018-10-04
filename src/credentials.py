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
import settings


# Credentials should be stored in settings.CREDENTIALS_DIR
def get_service():
    """
    This is straight out of the tutorial at:
    https://developers.google.com/calendar/quickstart/python
    """
    SCOPES = "https://www.googleapis.com/auth/calendar"
    cred = os.path.join(settings.CREDENTIALS_DIR, "credentials.json")
    store = file.Storage("token.json")
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(cred, SCOPES)
        creds = tools.run_flow(flow, store)
    service = build("calendar", "v3", http=creds.authorize(Http()))
    return service
