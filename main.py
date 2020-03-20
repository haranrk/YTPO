#!/usr/bin/python

import argparse
import os
import shutil
import os.path as osp
import json
from tqdm import tqdm
import pprint as pp

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from tinydb import TinyDB, where, Query

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
    separator = '----'
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
      
    def list_playlists(self, verbose=False):
        response = self.youtube.playlists().list(part='snippet',mine=True,maxResults=50).execute()
        # import ipdb;ipdb.set_trace()
        if verbose:
            for pl in response['items']:
                print("%s | %s" %(pl["id"],pl['snippet']['title']))
        return response

    def list_playlist_items(self,playlist_id, verbose=False):
        response = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50
                ).execute()
        if verbose:
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

    def insert_playlist_item(self, playlist_id,video_id):
        body = {
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                        }
                    }
                }
        response = self.youtube.playlistItems().insert(
                part="snippet",
                body=body
                ).execute()

    def remove_playlist_item(self,id):
        return self.youtube.playlistItems().delete(id=id).execute()

    def folder_mode(self):
        playlists = self.list_playlists()['items']
        playlists_root_path = 'YTPO-lists'
        os.mkdir(playlists_root_path)
        db = TinyDB(osp.join(playlists_root_path,'playlists.json'))

        pl_pbar = tqdm(playlists, desc="Retrieving playlists")
        for playlist in pl_pbar:
            playlist_id = playlist['id']
            title = playlist['snippet']['title']
            # pl_pbar.set_postfix_str("%s"%(title))
            playlist_path = osp.join(playlists_root_path,YTPO.combiner(title,playlist_id))

            os.mkdir(playlist_path)
            playlist_items = self.list_playlist_items(playlist_id)['items']
            
            plitem_pbar = tqdm(playlist_items, desc=title)
            for item in plitem_pbar:
                item_title = item["snippet"]["title"].replace('/','_').replace('\\','_')
                item_id_video = item["snippet"]["resourceId"]["videoId"]
                open(osp.join(playlist_path,YTPO.combiner(item_title,item_id_video)),'a').close()
                item_id = item["id"]
                db.insert({"id": item_id,"video_id": item_id_video, "playlist_id": playlist_id, "playlist_title":title, "video_title":item_title})

        print("\n The playlists have been retrieved and the folders have been generated at %s. When you are done, enter Y to update the playlists online. Press n to abort." %(osp.abspath(playlists_root_path)))
        cmd = input()
        if cmd == 'Y':
            playlist_paths = type(self).list_only_ytpo_files(playlists_root_path)
            add_q = []
            del_q = []

            for playlist_path in playlist_paths:
                playlist_id = playlist_path.split(type(self).separator)[-1]
                playlist_title = type(self).separator.join(playlist_path.split(type(self).separator)[:-1])
                
                playlist_items_new = [x.split(type(self).separator)[-1] for x in type(self).list_only_ytpo_files(osp.join(playlists_root_path,playlist_path))]
                playlist_items_old = [x["video_id"] for x in db.search(where("playlist_id")==playlist_id)]

                # For adding 
                for item in playlist_items_new:
                    if not item in playlist_items_old:
                        video_title = db.search(where("video_id")==item)[0]["video_title"]
                        add_q.append({"playlist_id": playlist_id,"video_id":item,"playlist_title":playlist_title,"video_title":video_title})

                #For deleting
                for item in playlist_items_old:
                    if not item in playlist_items_new:
                        item_ids = db.search((where("video_id")==item) & (where("playlist_id")==playlist_id))
                        del_q+= item_ids
                
            print("The following changes will be made to your playlists")

            def summarise_q(q):
                for i in q:
                    print("\t%s\t|\t%s" % (i["playlist_title"],i["video_title"]))

            print("\nThese videos would be REMOVED from the corresponding playlists")
            summarise_q(del_q)
            print("\nThese videos would be ADDED to the corresponding playlists")
            summarise_q(add_q)

            print("Proceed? (Y/n)")
            cmd = input()

            if cmd == "Y":
                print("Deleting videos")
                for i in del_q:
                    self.remove_playlist_item(i["id"])
                print("Adding videos")
                for i in add_q:
                    self.insert_playlist_item(i["playlist_id"],i["video_id"])
            else:
                print("Aborting")
        
        shutil.rmtree(playlists_root_path)

    def list_only_ytpo_files(path):
        x = os.listdir(path)
        try:
            x.remove("playlists.json")
        except:
            pass

        def starts_with_stop(y):
            if y[0]=='.':
                return False
            else:
                return True
        x = filter(starts_with_stop,x)
        return x

    @classmethod
    def combiner(cls,title, id):
        '''
        Combines the title and id with a separator
        '''
        return "%s%s%s"%(title,cls.separator,id)

if __name__ == '__main__':
  x = YTPO()
  
  try:
    # x.list_playlist_items("PLvipJsxgjo94NhE92dF7cF4828tXKH_-T",verbose=True)
    x.folder_mode()
  except HttpError as e:
    print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
