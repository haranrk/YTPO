#!/usr/bin/python

# This code sample creates a private playlist in the authorizing user's
# YouTube channel.
# Usage:
#   python playlist_updates.py --title=<TITLE> --description=<DESCRIPTION>

import argparse
import os
import json
import pprint as pp

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    
class YTPO:
    def __init__(self):
        self.CLIENT_SECRETS_FILE = 'secrets/client_secret.json'

        # This OAuth 2.0 access scope allows for full read/write access to the
        # authenticated user's account.
        self.get_authenticated_service()
    
    # Authorize the request and store authorization credentials.
    def get_authenticated_service(self):
        SCOPES = ['https://www.googleapis.com/auth/youtube']
        API_SERVICE_NAME = 'youtube'
        API_VERSION = 'v3'
        # credentials = flow.run_console()
        if not os.path.isfile('secrets/credentials.json'):
            print("Credentials file not found")
            flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(host='localhost',
            port=8080, 
            authorization_prompt_message='Please visit this URL: {url}', 
            success_message='The auth flow is complete; you may close this window.',
            open_browser=True)

            #SAVING CREDENTIALS DATA
            creds_data = {
              'token': credentials.token,
              'refresh_token': credentials.refresh_token,
              'token_uri': credentials.token_uri,
              'client_id': credentials.client_id,
              'client_secret': credentials.client_secret,
              'scopes': credentials.scopes
            }
            save = True
            if save:
              del creds_data['token']
              with open('secrets/credentials.json', 'w') as outfile:
                  json.dump(creds_data, outfile)
        else:
            print("Credentials file found")
            CLIENT_CREDENTIALS_FILE = 'secrets/credentials.json'
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(CLIENT_CREDENTIALS_FILE)

        self.youtube = build(API_SERVICE_NAME, API_VERSION, credentials = credentials)
    
    def add_playlist(self, args):
      
      body = dict(
        snippet=dict(
          title=args.title,
          description=args.description
        ),
        status=dict(
          privacyStatus='private'
        ) 
      ) 
        
      print(body)
      playlists_insert_response = self.youtube.playlists().insert(
        part='snippet,status',
        body=body
      ).execute()

      print('New playlist ID: %s' % playlists_insert_response['id'])
      
    def list_playlists(self):
        # body = {
                # 'mine': True
                # }
        # print(body)
        response = self.youtube.playlists().list(part='snippet',mine=True,maxResults=50).execute()
        # import ipdb;ipdb.set_trace()
        for pl in response['items']:
            print("%s | %s" %(pl["id"],pl['snippet']['title']))
        return response

    def list_playlist_items(self,playlist_id):

        response = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id
                ).execute()
        for vid in response['items']:
            print("%s | %s" % (vid["id"], vid["snippet"]["title"]))

        return response

    def update_playlist_item(self,id,playlist_id,resource_id,new_position):
        body = {
                "id": id,
                "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": resource_id,
                        "position": new_position
                    }
                }
        return self.youtube.playlistItems().update(
                    part="snippet",
                    body=body
                ).execute()

    def remove_playlist_item(self,id):
        return self.youtube.playlistItems().delete(id=id).execute()

if __name__ == '__main__':
  x = YTPO()
  
  try:
    x.list_playlist_items("PLvipJsxgjo94NhE92dF7cF4828tXKH_-T")
  except HttpError as e:
    print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
