#!/usr/bin/python2
# Copyright (c) 2014 Cedric Bellegarde <gnumdk@gmail.com>
#

import os, time
import sqlite3
from thread import start_new_thread
from gi.repository import GLib
from mutagen.easyid3 import EasyID3
from database import Database

class CollectionScanner:

	_mimes = [ "mp3", "ogg", "flac", "wma", "m4a", "mp4" ]
	def __init__(self):
		self._path = GLib.get_user_special_dir(GLib.USER_DIRECTORY_MUSIC)
		self._db = Database()

	# Update database if empty
	def update(self):
		sql = sqlite3.connect(Database.DB_PATH)
		self._db.init(sql)
		sql.close()

		start_new_thread(self._scan, ())


	def _scan(self):
		sql = sqlite3.connect(Database.DB_PATH)
		songs = self._db.get_songs_filenames(sql)
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
							self._add2db(sql, filename, tag)
						else:
							songs.remove(filename)
						
					except Exception as e:
						pass
		# Clean deleted files
		for song in songs:
			self._db.remove_song(sql, song)
		self._db.clean(sql)
		sql.close()

	def _add2db(self, sql, filename, tag):
		title="Unknown"
		artist="Unknown"
		album="Unknown"
		genre="Unknown"
		length="0"
		tracknumber="0"
		year="0"

		keys = tag.keys()
		if "title" in keys:
			title = tag["title"][0]
		if "artist" in keys:
			artist = tag["artist"][0]
		if "album" in keys:
			album = tag["album"][0]
		if "genre" in keys:
			genre = tag["genre"][0]
		else: print (keys)
		if "length" in keys:
			length = tag["length"][0]
		if "tracknumber" in keys:
			tracknumber = tag["tracknumber"][0]
		if "date" in keys:
			year = tag["date"][0]

		# Get artist id, add it if missing
		artist_id = self._db.get_artist(sql, artist)
		if not artist_id:
			self._db.add_artist(sql, artist)
			artist_id = self._db.get_artist(sql, artist)

		# Get genre id, add genre if missing
		genre_id = self._db.get_genre(sql, genre)
		if not genre_id:
			self._db.add_genre(sql, genre)
			genre_id = self._db.get_genre(sql, genre)

		# Get album id, add it if missing
		album_id = self._db.get_album(sql, album, artist_id, genre_id)
		if not album_id:
			self._db.add_album(sql, album, artist_id, genre_id)
			album_id = self._db.get_album(sql, album, artist_id, genre_id)

		# Add song to db
		self._db.add_song(sql, title, filename, length, tracknumber, year, album_id)

scanner = CollectionScanner()
scanner.update()
time.sleep(300)
