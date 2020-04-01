[![PyPI version](https://badge.fury.io/py/ytpo.svg)](https://badge.fury.io/py/ytpo)
# YTPO - Youtube playlist organizer
YouTube and YouTube music's playlist organization capabilities are severely lacking. Therefore, YTPO is a nifty cli app that allows you to organize your playlist via a host of methods.

## Installation 
```bash
pip install ytpo
```
On the first run of any command, YTPO will need to get accesss to your YouTube account. The authorization page will be opened automatically in your default browser. Log in with the Google account you want to make changes to the playlist in.

![Installation](assets/install.gif)
## Usage
It's a CLI.
```bash
ytpo <cmd>
```
For the list of commands and what they do - 
```Bash
ytpo -h
```
The following are the different commands available currently
### Folder mode
```bash
ytpo folder
```
This mode retrieves all of your playlists, creates a folder for each playlist and fills each folder with filenames for each item in the playlist. Once the directory tree is generated, you can do the following - 
1. Copy/Move songs from one playlist folder to another
2. Delete songs from a playlist folder

The app will then remotely update your playlists to match the directory tree. The orders of songs within a playlist is preserved and new songs are added to the bottom of the playlist.

> After you have made your changes, the app will show you the summary of the edits it will be making before it makes them, so can check if errors if any.

![Folder](assets/folder.gif)
### List mode
```bash
ytpo list
```
This mode retrieves all of your playlists, creates a text file for each playlist and fills each file with playlist items according to their position in the playlist. Once the files have been generated, you can -
1. Change the order of the items by changing their location in the file
1. Delete items by removing the corresponding line
1. Make copies of items by duplicating the lines
1. Add a new item from a different playlist by copying the corresponding line from the other playlist file and pasting it in the target playlist file.

The app will then remotely update your playlists and order to match the files.

> After you have made your changes, the app will show you the summary of the edits it will be making before it makes them, so can check if errors if any.

![List](assets/list.gif)

### Trim mode
```bash
ytpo trim
```
Removes duplicate items from the specified playlists
![Trim](assets/trim.gif)

### Shuffle mode
```bython
ytpo trim
```
Shuffles  the specified playlists
