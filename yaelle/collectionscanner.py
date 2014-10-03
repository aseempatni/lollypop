#!/usr/bin/python
# Copyright (c) 2014 Cedric Bellegarde <gnome@gmail.com>
#

import os, time
import sqlite3
from _thread import start_new_thread
from gi.repository import GLib
from mutagenx.easyid3 import EasyID3
from yaelle.database import Database

class CollectionScanner:

	_mimes = [ "mp3", "ogg", "flac", "wma", "m4a", "mp4" ]
	def __init__(self):
		self._path = GLib.get_user_special_dir(GLib.USER_DIRECTORY_MUSIC)

	# Update database if empty
	def update(self):
		#start_new_thread(self._scan, ())
		self._scan()


	def _scan(self):
		db = Database()
		songs = db.get_songs_filenames()
		for root, dirs, files in os.walk(self._path):
			for f in files:
				lowername = f.lower()
				supported = False
				for mime in self._mimes:
					if lowername.endswith(mime):
						supported = True
						break	
				if (supported):
					filename = os.path.join(root, f)
					try:
						if filename not in songs:
							tag = EasyID3(filename)
							self._add2db(db, filename, tag)
						else:
							songs.remove(filename)
						
					except Exception as e:
						pass
		# Clean deleted files
		for song in songs:
			db.remove_song(song)
		db.clean()

	def _add2db(self, db, filename, tag):

		title = tag["title"][0]
		artist = tag["artist"][0]
		album = tag["album"][0]
		genre = tag["genre"][0]
		length = tag["length"][0]
		tracknumber = tag["tracknumber"][0]
		year = tag["date"][0]

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

		# Add song to db
		db.add_song(title, filename, length, tracknumber, year, album_id)
