#!/usr/bin/python

import random
import argparse
from collections import Counter
import os
import shutil
import os.path as osp
import json
from tqdm import tqdm

import google.oauth2.credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from tinydb import TinyDB, where 

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
    separator = '| - | - |' #String used to separate the title and ID for list and file modes
    liked_videos_pl_id = 'liked-videos'
    def __init__(self):
        self.ytpo_root = osp.dirname(__file__)

        self.CLIENT_SECRETS_FILE = osp.join(self.ytpo_root,'secrets','client_secret.json')
        if not osp.isfile(self.CLIENT_SECRETS_FILE):
            raise FileNotFoundError("Client Secret file not found")

        # This OAuth 2.0 access scope allows for full read/write access to the
        # authenticated user's account.
        self.get_authenticated_service()
    
    # Authorize the request and store authorization credentials.
    def get_authenticated_service(self):
        SCOPES = ['https://www.googleapis.com/auth/youtube']
        CLIENT_CREDENTIALS_FILE = osp.join(self.ytpo_root,'secrets','credentials.json')
        API_SERVICE_NAME = 'youtube'
        API_VERSION = 'v3'
        # credentials = flow.run_console()
        if not os.path.isfile(CLIENT_CREDENTIALS_FILE):
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
              with open(CLIENT_CREDENTIALS_FILE, 'w') as outfile:
                  json.dump(creds_data, outfile)
        else:
            # print("Credentials file found")
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
      
    def list_playlists(self, include_liked_pl, verbose=False):
        response = self.youtube.playlists().list(
                part='snippet', 
                mine=True,
                maxResults=50).execute()

        items = response["items"]

        while "nextPageToken" in response.keys():
            response = self.youtube.playlists().list(
                    part='snippet',
                    pageToken = response["nextPageToken"],
                    mine=True,
                    maxResults=50).execute()
            items += response["items"]

        if include_liked_pl == True:
            items.append({
                'id': type(self).liked_videos_pl_id,
                'snippet': {
                    'title': "Liked Videos",
                    }
                })

        if verbose:
            for pl in items:
                print("%s | %s" %(pl["id"],pl['snippet']['title']))
        return items

    def list_playlist_items(self,pl_id, verbose=False):
        '''
        Lists playlist item for specified playlist

        Parameters:
        pl_id(str) -- Playlist ID
        verbose(bool) -- If true prints the items

        Returns:
        list -- playlist items
        '''

        if pl_id==type(self).liked_videos_pl_id:
            response = self.youtube.videos().list(
                    part="snippet",
                    myRating="like",
                    maxResults=50
                    ).execute()
            items = response["items"]

            while "nextPageToken" in response.keys():
                response = self.youtube.videos().list(
                        part="snippet",
                        pageToken = response["nextPageToken"],
                        myRating="like",
                        maxResults=50
                        ).execute()
                items += response["items"]

                for i,item in enumerate(items): #Modifying response to resemble playlist item to maintain code uniformity 
                    item["snippet"]["position"] = i
                    item["snippet"]["resourceId"] = {
                            "videoId": item["id"]
                            }

                    # item["id"] ="NA"
        else:
            response = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=pl_id,
                    maxResults=50
                    ).execute()
            items = response["items"]

            while "nextPageToken" in response.keys():
                response = self.youtube.playlistItems().list(
                        part="snippet",
                        pageToken = response["nextPageToken"],
                        playlistId=pl_id,
                        maxResults=50
                        ).execute()
                items += response["items"]

        if verbose:
            for vid in items:
                print("%s | %s" % (vid["id"], vid["snippet"]["title"]))
        return items

    def update_playlist_item(self,item_id,pl_id,resource_id,new_pos):
        '''
        Updates the corresponding playlist item with either a different video and/or position

        Parameters:
        id -- Unique ID of playlist item
        pl_id -- ID of playlist
        resource_id -- ID of playlist resource (usually video)
        new_pos -- Position of item within the playlist
        '''
        body = {
                "id": item_id,
                "snippet": {
                        "playlistId": pl_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": resource_id,
                            },
                        "position": new_pos
                    }
                }
        return self.youtube.playlistItems().update(
                    part="snippet",
                    body=body
                ).execute()

    def insert_playlist_item(self, pl_id,video_id, pos=0):
        '''
        Inserts a new item into an existing a playlist at specified position

        Parameters:
            pl_id -- ID of playlist
            video_id -- ID of video
            pos -- Position to be inserted

        Returns:
            dict -- Response of request
        '''
        body = {
                "snippet": {
                    "playlistId": pl_id,
                    "position": pos,
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
        return response

    def remove_playlist_item(self,item_id):
        '''
        Removes item from playlist
        Parameters:
        id -- ID of playlist item
        '''
        return self.youtube.playlistItems().delete(id=item_id).execute()

    @classmethod
    def combine(cls,title, item_id):
        '''
        Combines the title and id with the separator
        '''
        return "%s%s%s"%(title,cls.separator,item_id)

    @classmethod
    def separate(cls,id_str):
        '''
        Combines the title and id with the separator
        '''
        id_str = id_str[::-1] # Reverses the string
        id,title = id_str.split(cls.separator,1)

        return title[::-1],id[::-1]

    def folder_mode(self):
        playlists = self.list_playlists(include_liked_pl=True)
        playlists_root_path = 'YTPO-lists'
        os.mkdir(playlists_root_path)
        db = TinyDB(osp.join(playlists_root_path,'playlists.json'))

        pl_pbar = tqdm(playlists, desc="Retrieving playlists")
        for playlist in pl_pbar:
            pl_id = playlist['id']
            pl_title = playlist['snippet']['title']
            playlist_path = osp.join(playlists_root_path,type(self).combine(pl_title,pl_id))

            os.mkdir(playlist_path)
            playlist_items = self.list_playlist_items(pl_id)
            
            plitem_pbar = tqdm(playlist_items, desc=pl_title)
            for item in plitem_pbar:
                item_title = item["snippet"]["title"].replace('/','_').replace('\\','_') #Replaces back and forward slashes to '_' to avoid file path conflicts
                item_vid_id = item["snippet"]["resourceId"]["videoId"]
                item_id = item["id"]
                open(osp.join(playlist_path,type(self).combine(item_title,item_id)),'a').close()
                db.insert({"id": item_id,"vid_id": item_vid_id, "pl_id": pl_id, "pl_title":pl_title, "vid_title":item_title})

        print("\n\nThe playlists have been retrieved and the folders have been generated at %s." %(osp.abspath(playlists_root_path)))
        print("The Liked Videos playlist is an automatic playlist and thus, unmodifiable. Therefore, any changes made to it's folder will be ignored.")
        print("When you are done, enter Y to update the playlists online. Press n to abort.")
        cmd = input()
        if cmd == 'Y':
            playlist_paths = type(self).list_only_ytpo_files(playlists_root_path)
            add_q = []
            del_q = []

            for playlist_path in playlist_paths:
                pl_title, pl_id = type(self).separate(playlist_path)
                if pl_id==type(self).liked_videos_pl_id:
                    continue
                
                playlist_items_new = [type(self).separate(x)[1] for x in type(self).list_only_ytpo_files(osp.join(playlists_root_path,playlist_path))]
                playlist_items_old = [x["id"] for x in db.search(where("pl_id")==pl_id)]

                # For adding
                for item_id in playlist_items_new:
                    if not item_id in playlist_items_old:
                        item = db.search(where("id")==item_id)[0]
                        add_q.append({"pl_id": pl_id,"vid_id":item["vid_id"],"pl_title":pl_title,"vid_title":item["vid_title"]})

                #For deleting
                for item_id in playlist_items_old:
                    if not item_id in playlist_items_new:
                        # item_ids = db.search((where("video_id")==item) & (where("pl_id")==pl_id))
                        item = db.search(where("id")==item_id)
                        del_q+= item
                
            print("The following changes will be made to your playlists")

            def summarise_q(q):
                for i in q:
                    print("\t%s\t|\t%s" % (i["pl_title"],i["vid_title"]))

            print("\nThese videos would be REMOVED from the corresponding playlists")
            if del_q == []:
                print("No videos to delete")
            else:
                summarise_q(del_q)
            print("\nThese videos would be ADDED to the corresponding playlists")
            if add_q == []:
                print("No videos to add")
            else:
                summarise_q(add_q)

            print("\nProceed? (Y/n)")
            cmd = input()

            if cmd == "Y":
                q_bar = tqdm(del_q,desc="Deleting Videos")
                for i in q_bar:
                    self.remove_playlist_item(i["id"])

                q_bar = tqdm(add_q,desc="Adding Videos")
                for i in q_bar:
                    self.insert_playlist_item(i["pl_id"],i["vid_id"])

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

    def list_mode(self):
        playlists = self.list_playlists(include_liked_pl=True)

        playlists_root_path = 'YTPO-lists'
        try:
            os.mkdir(playlists_root_path)
        except FileExistsError:
            shutil.rmtree(playlists_root_path)
            os.mkdir(playlists_root_path)

        db = TinyDB(osp.join(playlists_root_path,'playlists.json'))

        pl_pbar = tqdm(playlists, desc="Retrieving playlists")
        for pl in pl_pbar:
            pl_id = pl['id']
            pl_title = pl['snippet']['title']
            pl_path = osp.join(playlists_root_path,type(self).combine(pl_title,pl_id))+'.txt'
            pl_file = open(pl_path,'w')

            playlist_items = self.list_playlist_items(pl_id)
            
            plitem_pbar = tqdm(playlist_items, desc=pl_title)
            for item in plitem_pbar:
                item_title = item["snippet"]["title"].replace('/','_').replace('\\','_')
                item_pos = item["snippet"]["position"]
                item_vid_id = item["snippet"]["resourceId"]["videoId"]
                item_id = item["id"]
                pl_file.write("%s\n"%(type(self).combine(item_title,item_vid_id)))
                db.insert({"id": item_id,"pos": item_pos, "vid_id": item_vid_id, "pl_id": pl_id, "pl_title":pl_title, "vid_title":item_title})
            pl_file.close()

        print("\n\nThe playlists have been retrieved and the files have been generated at %s." %(osp.abspath(playlists_root_path)))
        print("The Liked Videos playlist is an automatic playlist and thus, unmodifiable. Therefore, any changes made to it's file will be ignored.")
        print("When you are done, enter Y to update the playlists online. Press n to abort.")
        cmd = input()
        if cmd == 'Y':
            task_q = []
            pl_files = type(self).list_only_ytpo_files(playlists_root_path)
            pl_files = [(type(self).separate(x[:-4])) for x in pl_files]

            for pl_title, pl_id in pl_files:
                if pl_id==type(self).liked_videos_pl_id:
                    continue
                pl_path = osp.join(playlists_root_path,type(self).combine(pl_title,pl_id))+'.txt'
                pl_file = open(pl_path,'r')
                pl_hash_items = pl_file.readlines()
                pl_hash_items = [x.strip() for x in pl_hash_items]
                pl_file.close()

                pl_items_old = db.search(where("pl_id")==pl_id)
                pl_items_old = sorted(pl_items_old, key=lambda i: i['pos'])

                flag = 0
                vids_to_remove =[]
                for pos,pl_hash_item in enumerate(pl_hash_items):
                    item_title, item_vid_id = type(self).separate(pl_hash_item)
                    if flag == 0 and ((pl_items_old[pos]["vid_id"] != item_vid_id) if len(pl_items_old)>pos else True):
                        flag = 1
                        vids_to_remove = [{**{"task": "remove"},**x} for x in pl_items_old[pos:]]

                    if flag == 1:
                        task_q.append({"task": "insert", "pl_id": pl_id, "pl_title": pl_title,"vid_id": item_vid_id,"pos":pos, "vid_title":item_title})
                task_q += vids_to_remove
                    
            affected_playlists = set([type(self).combine(x["pl_title"],x["pl_id"]) for x in task_q])
            print("The following playlists will be affected")
            for pl in affected_playlists:
                print(pl)

            # for q in task_q:
                # print("%s\t%s %s"%(q["pl_title"],"X" if q["task"]=="remove" else str(q["pos"]+1)+'.',q["vid_title"]+q["vid_id"]))

            print("Proceed? (Y/n)")
            cmd = input()

            if cmd == "Y":
                print("Updating videos")
                tasks_pbar = tqdm(task_q, desc="Updating playlists")
                for q in tasks_pbar:
                    if q["task"]=="insert":
                        self.insert_playlist_item(q["pl_id"],q["vid_id"],q["pos"])
                    elif q["task"]=="remove":
                        self.remove_playlist_item(q["id"])
            else:
                print("Aborting")
        
        shutil.rmtree(playlists_root_path)

    def trim_playlist(self,pl_id, pl_title):
        playlist_items = self.list_playlist_items(pl_id)
        removed_items_cntr = Counter()
        unique_vids = []

        plitem_pbar = tqdm(playlist_items, desc=pl_title)
        for item in plitem_pbar:
            if item["snippet"]["resourceId"]["videoId"] not in unique_vids:
                unique_vids.append(item["snippet"]["resourceId"]["videoId"])
            else:
                removed_items_cntr[item["snippet"]["title"]]+=1
                self.remove_playlist_item(item["id"])

        if removed_items_cntr.most_common() == []:
            print("No duplicates found")
        else:
            print("Following duplicates were found")
            print("\nOcurrences Title")
            for title, count in removed_items_cntr.items():
                print("%10i %s"%(count+1,title)) 

    def trim_mode(self):
        playlists = self.list_playlists(include_liked_pl=False)
        print("Choose which playlists you want to trim.")
        print("S.No. Playlist Name")
        for i,pl in enumerate(playlists):
            print("%5i %s"%(i+1,pl["snippet"]["title"]))   

        print("Enter your choices as comma-separated values of the S.Nos (Ex: '2,3' will trim the 2nd and 3rd playlists)")
        print("Or enter 'all' to remove duplicates from all playlists")
        choices = input()
        if choices == 'all':
            pl_indexes = list(range(len(playlists)))

        else:
            pl_indexes = [int(x)-1 for x in choices.split(',')]

        print("\nRemoving duplicates ...")
        for pl_index in pl_indexes:
            self.trim_playlist(playlists[pl_index]["id"],playlists[pl_index]["snippet"]["title"])
            print("\n")

    def shuffle_playlist(self,pl_id, pl_title):
        playlist_items = self.list_playlist_items(pl_id)
        new_positions = list(range(len(playlist_items)))
        random.shuffle(new_positions)

        plitem_pbar = tqdm(playlist_items, desc=pl_title)
        for i,item in enumerate(plitem_pbar):
        # for i,item in enumerate(playlist_items):
            self.update_playlist_item(item["id"],item["snippet"]["playlistId"],item["snippet"]["resourceId"]["videoId"], new_positions[i])

    def shuffle_mode(self):
        playlists = self.list_playlists(include_liked_pl=False)
        print("Choose which playlists you want to shuffle.")
        print("S.No. Playlist Name")
        for i,pl in enumerate(playlists):
            print("%5i %s"%(i+1,pl["snippet"]["title"]))   

        print("Enter your choices as comma-separated values of the S.Nos (Ex: '2,3' will trim the 2nd and 3rd playlists)")
        print("Or enter 'all' to shuffle all playlists")
        choices = input()
        if choices == 'all':
            pl_indexes = list(range(len(playlists)))

        else:
            pl_indexes = [int(x)-1 for x in choices.split(',')]

        print("\nShuffling..." )
        for pl_index in pl_indexes:
            self.shuffle_playlist(playlists[pl_index]["id"],playlists[pl_index]["snippet"]["title"])
            print("\n " )

    def logout(self):
        '''
        Deletes the saved user's session details
        '''
        CLIENT_CREDENTIALS_FILE = osp.join(self.ytpo_root,'secrets','credentials.json')
        os.remove(CLIENT_CREDENTIALS_FILE)
        print("Logged out")

def main():
    print("-"*12)
    print("    YTPO")
    print("-"*12)
    x = YTPO()

    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(help="Available commands")

    trim_parser = sub_parsers.add_parser("trim",help="Removes duplicate items from the specified playlists")
    trim_parser.set_defaults(func=x.trim_mode)
    shuffle_parser = sub_parsers.add_parser("shuffle",help="Shuffles the specified playlists")
    shuffle_parser.set_defaults(func=x.shuffle_mode)
    list_parser = sub_parsers.add_parser("list",help="Creates editable files containing playlist items in their respecitive order")
    list_parser.set_defaults(func=x.list_mode)
    folder_parser = sub_parsers.add_parser("folder",help="Creates a folders for each playlist containing a mock file for each play list item")
    folder_parser.set_defaults(func=x.folder_mode)

    logout_parser = sub_parsers.add_parser("logout", help="Logs out of the session")
    logout_parser.set_defaults(func=x.logout)

    args = parser.parse_args()
    args.func()

if __name__ == '__main__':
    main()
