#!/usr/bin/python
# Copyright (c) 2014 Cedric Bellegarde <gnome@gmail.com>
#

import os, time
import sqlite3
from _thread import start_new_thread
from gi.repository import GLib
import mutagen
from lollypop.database import Database

class CollectionScanner:

	_mimes = [ "mp3", "ogg", "flac", "m4a", "mp4" ]
	def __init__(self):
		self._path = GLib.get_user_special_dir(GLib.USER_DIRECTORY_MUSIC)

	# Update database if empty
	def update(self, callback):
		GLib.idle_add(self._scan, callback)
		#start_new_thread(self._scan, (callback,))
		#self._scan(callback)


	def _scan(self, callback):
		db = Database()
		tracks = db.get_tracks_filepath()
		for root, dirs, files in os.walk(self._path):
			for f in files:
				lowername = f.lower()
				supported = False
				for mime in self._mimes:
					if lowername.endswith(mime):
						supported = True
						break	
				if (supported):
					filepath = os.path.join(root, f)
					try:
						if filepath not in tracks:
							tag = mutagen.File(filepath, easy = True)
							self._add2db(db, filepath, tag)
						else:
							tracks.remove(filepath)
						
					except Exception as e:
						print("CollectionScanner::_scan(): %s" %e)

		# Clean deleted files
		for track in tracks:
			db.remove_track(track)

		db.commit()
		callback(db.get_genres())
		db.close()

	def _add2db(self, db, filepath, tag):
		keys = tag.keys()
		if "title" in keys:
			title = tag["title"][0]
		else:
			title = os.path.basename(filepath)

		if "artist" in keys:
			artist = tag["artist"][0]
		else:
			artist = "Unknown"

		if "performer" in keys:
			artist = tag["performer"][0]

		if "album" in keys:
			album = tag["album"][0]
		else:
			album = "Unknown"

		if "genre" in keys:
			genre = tag["genre"][0]
		else:
			genre = "Unknown"

		length = int(tag.info.length)

		if "tracknumber" in keys:
			str = tag["tracknumber"][0]
			if "/" in str:
				index = str.find("/")
				tracknumber = int(str[0:index])
			else:
				tracknumber = int(str)
		else:
			tracknumber = 0
		
		if "date" in keys:
			year = tag["date"][0]
		else:
			year = ""

		# Get artist id, add it if missing
		artist_id = db.get_artist(artist)
		if not artist_id:
			db.add_artist(artist)
			artist_id = db.get_artist(artist)

		# Get genre id, add genre if missing
		genre_id = db.get_genre(genre)
		if not genre_id:
			db.add_genre(genre)
			genre_id = db.get_genre(genre)

		# Get album id, add it if missing
		album_id = db.get_album(album, artist_id, genre_id)
		if not album_id:
			db.add_album(album, artist_id, genre_id)
			album_id = db.get_album(album, artist_id, genre_id)

		# Add track to db
		db.add_track(title, filepath, length, tracknumber, year, album_id)
