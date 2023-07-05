import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import base64
from email.message import EmailMessage

import google.auth.exceptions
import oauthlib.oauth2.rfc6749.errors
from socket import gaierror
import httplib2.error
import traceback

import lib.logging as Logging

Log = Logging.Log("logs/phludd_log.log")

class Gmail:

    def __init__(self):
        self._lasterror = None
        self.authorized = False
        self.service = None
        self.sender = ""
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.metadata']
        self.creds = self.authorize()
        if self.authorized:
            self.build_service()
        

    def isReady(self):
        return self.authorized and not (self.service == None)

    def getLastError(self):
        e = self._lasterror
        self._lasterror = None
        return e
    
    def authorize(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        try:
            if os.path.exists('credentials/token.json'):
                creds = Credentials.from_authorized_user_file('credentials/token.json', self.SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials/credentials.json', self.SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('credentials/token.json', 'w') as token:
                    token.write(creds.to_json())
            self.authorized = True
            return creds
        except (google.auth.exceptions.TransportError, oauthlib.oauth2.rfc6749.errors.AccessDeniedError) as error:
            Log.log(Log.ERROR, f"An error occured in gmail_handle.py: {type(error)} | {error}")
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            self._lasterror = error
            

    def build_service(self):
        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
            if self.sender == "":
                profile = self.service.users().getProfile(userId="me").execute()
                self.sender = profile.get("emailAddress")
                
        except (HttpError, httplib2.error.ServerNotFoundError, socket.gaierror) as error:
            Log.log(Log.ERROR, F'An error occurred: {type(error)} | {error}')
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            send_message = None
            self._lasterror = error
            
    def send_message(self, content, recipient):
        """Create and send an email message
        Print the returned  message id
        Returns: Message object, including message id

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """

        try:
            message = EmailMessage()
                
            message.set_content(content)

            message['To'] = recipient
            message['From'] = self.sender
            message['Subject'] = 'Automated Email Alert, Do not reply'

            # encoded message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
                .decode()

            create_message = {
                'raw': encoded_message
            }
            # pylint: disable=E1101
            send_message = (self.service.users().messages().send
                            (userId="me", body=create_message).execute())
            Log.log(Log.INFO, F'Gmail Message sent! - Message Id: {send_message["id"]}')
            
        except (HttpError, ConnectionResetError)  as error:
            Log.log(Log.ERROR, F'An error occurred: {type(error)} | {error}')
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            send_message = None
            self._lasterror = error
            
        return send_message
