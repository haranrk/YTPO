[![PyPI version](https://badge.fury.io/py/ytpo.svg)](https://badge.fury.io/py/ytpo)
# YTPO - Youtube playlist organizer
YouTube and YouTube music's playlist organization capabilities are severely lacking. Therefore, YTPO is a nifty cli app that allows you to organize your playlist via a host of methods.

## Installation 
```Python
pip install ytpo
```
On the first run of any command, YTPO will need to get accesss to your YouTube account. The authorization page will be opened automatically in your default browser. Log in with the Google account you want to make changes to the playlist in.

## Usage
It's a CLI.
```Python
ytpo <cmd>
```
For the list of commands and what they do - 
```Python
ytpo -h
```

### Folder mode
```Python
ytpo folder
```
This mode retrieves all of your playlists, creates a folder for each playlist and fills each folder with filenames for each item in the playlist. Once the directory tree is generated, you can do the following - 
1. Copy/Move songs from one playlist folder to another
2. Delete songs from a playlist folder

The app will then remotely update your playlists to match the directory tree. The orders of songs within a playlist is preserved and new songs are added to the bottom of the playlist. 

### List mode
```Python
ytpo list
```
This mode retrieves all of your playlists, creates a text file for each playlist and fills each file with playlist items according to their position in the playlist. Once the files have been generated, you can -
1. Change the order of the items by changing their location in the file
1. Delete items by removing the corresponding line
1. Make copies of items by duplicating the lines
1. Add a new item from a different playlist by copying the corresponding line from the other playlist file and pasting it in the target playlist file.

### Trim mode
```Python
ytpo trim
```
Removes duplicate items from the specified playlists

### Shuffle mode
```Python
ytpo trim
```
Shuffles  the specified playlists
