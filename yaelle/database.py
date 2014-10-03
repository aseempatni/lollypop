#!/usr/bin/python
# Copyright (c) 2014 Cedric Bellegarde <gnome@gmail.com>
#

import sqlite3
import os

class Database:

	LOCAL_PATH = os.path.expanduser ("~") +  "/.local/share/yaelle"
	DB_PATH = "%s/yaelle.db" % LOCAL_PATH

	create_albums = '''CREATE TABLE albums (id INTEGER PRIMARY KEY AUTOINCREMENT,
						name TEXT NOT NULL,
						art TEXT,
						artist_id INT NOT NULL,
						genre_id INT NOT NULL)'''					
	create_artists = '''CREATE TABLE artists (id INTEGER PRIMARY KEY AUTOINCREMENT,
						  name TEXT NOT NULL)'''
	create_genres = '''CREATE TABLE genres (id INTEGER PRIMARY KEY AUTOINCREMENT,
						name TEXT NOT NULL)'''
	create_songs = '''CREATE TABLE songs (id INTEGER PRIMARY KEY AUTOINCREMENT,
				              name TEXT NOT NULL,
						      filename TEXT NOT NULL,
				              length TEXT,
						      tracknumber TEXT,
						      year TEXT,
						      album_id INT NOT NULL)'''
	def __init__(self):

		if not os.path.exists(self.LOCAL_PATH):
			try:
				os.mkdir(self.LOCAL_PATH)
			except:
				print("Can't create %s" % self.LOCAL_PATH)
				
		try:
			self._sql = sqlite3.connect(self.DB_PATH)
			try:
				self._sql.execute(self.create_albums)
				self._sql.execute(self.create_artists)
				self._sql.execute(self.create_genres)
				self._sql.execute(self.create_songs)
				self._sql.commit()
			except:
					pass
		except Exception as e:
			print("Can't connect to %s" % self.DB_PATH)
			pass


	def reset(self):
		self._sql.execute("DELETE FROM albums")
		self._sql.execute("DELETE FROM artists")
		self._sql.execute("DELETE FROM genres")
		self._sql.execute("DELETE FROM songs")
		self._sql.commit()

	def clean(self):
		self._sql.execute("DELETE FROM albums WHERE NOT EXISTS (SELECT id FROM songs where albums.id = songs.album_id)")
		self._sql.execute("DELETE FROM artists WHERE NOT EXISTS (SELECT id FROM albums where artists.id = albums.artist_id)")
		self._sql.execute("DELETE FROM genres WHERE NOT EXISTS (SELECT id FROM albums where genres.id = albums.genre_id)")
		self._sql.commit()

	def add_album(self, name, artist_id, genre_id):
		self._sql.execute("INSERT INTO albums (name, artist_id, genre_id) VALUES (?, ?, ?)",  (name, artist_id, genre_id))
		self._sql.commit()

	def add_artist(self, name):
		self._sql.execute("INSERT INTO artists (name) VALUES (?)", (name,))
		self._sql.commit()

	def add_genre(self, name):
		self._sql.execute("INSERT INTO genres (name) VALUES (?)", (name,))
		self._sql.commit()

	def add_song(self, name, filename, length, tracknumber, year, album_id):
		self._sql.execute("INSERT INTO songs (name, filename, length, tracknumber, year, album_id) VALUES (?, ?, ?, ?, ?, ?)", (name, filename, length, tracknumber, year, album_id))
		self._sql.commit()

	# Return genre id
	def get_genre(self, name):
		result = self._sql.execute("SELECT id from genres where name=?", (name,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return 0

	# Return a list of genre (id, name)
	def get_genres(self):
		genres = []
		result = self._sql.execute("SELECT id, name FROM genres ORDER BY name")
		for row in result:
			genres += (row,)
		return genres


	# Return artist id
	def get_artist(self, name):
		result = self._sql.execute("SELECT id from artists where name=?", (name,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return 0

	# Return a list of artists (id, name)
	def get_artists_by_genre(self, genre_id):
		artists = []
		result = self._sql.execute("SELECT DISTINCT artists.id, artists.name FROM artists,albums WHERE artists.id == albums.artist_id AND albums.genre_id=? ORDER BY artists.name", (genre_id,))
		for row in result:
			artists += (row,)
		return artists


	# Return album id
	def get_album(self, name, artist_id, genre_id):
		result = self._sql.execute("SELECT id FROM albums where name=? AND artist_id=? AND genre_id=?", (name, artist_id, genre_id))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return 0
		
	# Return album path
	def get_album_path(self, album_id):
		result = self._sql.execute("SELECT filename FROM songs where album_id=? LIMIT 1", (album_id))
		path = result.fetchone()
		if path:
			return os.path.dirname(path[0])

		return ""
	
	# Return a list of albums (id, name)
	def get_albums_by_artist(self, artist_id):
		albums = []
		result = self._sql.execute("SELECT id, name FROM albums WHERE artist_id=?", (artist_id,))
		for row in result:
			albums += (row,)
		return albums

	# Return a list of albums
	def get_albums_by_genre(self, genre_id):
		albums = []
		result = self._sql.execute("SELECT id, name FROM albums WHERE genre_id=?", (genre_id,))
		for row in result:
			albums += (row,)
		return albums

	# Return a list of songs (id, name, filename, length, tracknumber, year)
	def get_songs_by_album(self, album_id):
		songs = []
		result = self._sql.execute("SELECT id, name, filename, length, tracknumber, year FROM songs WHERE album_id=?", (album_id,))
		for row in result:
			songs += (row,)
		return songs

	# Return a list of songs filenames
	def get_songs_filenames(self):
		songs = []
		result = self._sql.execute("SELECT filename FROM songs;")
		for row in result:
			songs += row
		return songs

	# Remove song with filename
	def remove_song(self, filename):
		self._sql.execute("DELETE FROM songs where filename=?",  (filename,))
		self._sql.commit()
