#!/usr/bin/python
# Copyright (c) 2014 Cedric Bellegarde <gnome@gmail.com>
#

from gettext import gettext as _
import sqlite3
import os

class Database:

	LOCAL_PATH = os.path.expanduser ("~") +  "/.local/share/lollypop"
	DB_PATH = "%s/lollypop.db" % LOCAL_PATH

	create_albums = '''CREATE TABLE albums (id INTEGER PRIMARY KEY AUTOINCREMENT,
						name TEXT NOT NULL,
						artist_id INT NOT NULL,
						genre_id INT NOT NULL)'''					
	create_artists = '''CREATE TABLE artists (id INTEGER PRIMARY KEY AUTOINCREMENT,
						  name TEXT NOT NULL)'''
	create_genres = '''CREATE TABLE genres (id INTEGER PRIMARY KEY AUTOINCREMENT,
						name TEXT NOT NULL)'''
	create_tracks = '''CREATE TABLE tracks (id INTEGER PRIMARY KEY AUTOINCREMENT,
				          name TEXT NOT NULL,
					      filepath TEXT NOT NULL,
			              length INT,
					      tracknumber INT,
					      year TEXT,
					      album_id INT NOT NULL)'''
	create_sort_index = '''CREATE INDEX index_name ON table_name(tracknumber ASC)'''
							   
	def __init__(self):
		# Create db directory if missing
		if not os.path.exists(self.LOCAL_PATH):
			try:
				os.mkdir(self.LOCAL_PATH)
			except:
				print("Can't create %s" % self.LOCAL_PATH)
				
		try:
			self._sql = sqlite3.connect(self.DB_PATH)
			# Create db schema
			try:
				self._sql.execute(self.create_albums)
				self._sql.execute(self.create_artists)
				self._sql.execute(self.create_genres)
				self._sql.execute(self.create_tracks)
				self._sql.execute(self.create_sort_index)
				self._sql.commit()
			except:
					pass
		except Exception as e:
			print("Can't connect to %s" % self.DB_PATH)
			pass

	def close(self):
		self._sql.close()

	def commit(self):
		self._sql.commit()
		
	"""
		Reset database, all datas will be lost
	"""
	def reset(self):
		self._sql.execute("DELETE FROM albums")
		self._sql.execute("DELETE FROM artists")
		self._sql.execute("DELETE FROM genres")
		self._sql.execute("DELETE FROM tracks")
		self._sql.commit()

	"""
		Clean database deleting orphaned entries
	"""
	def clean(self):
		self._sql.execute("DELETE FROM albums WHERE NOT EXISTS (SELECT id FROM tracks where albums.id = tracks.album_id)")
		self._sql.execute("DELETE FROM artists WHERE NOT EXISTS (SELECT id FROM albums where artists.id = albums.artist_id)")
		self._sql.execute("DELETE FROM genres WHERE NOT EXISTS (SELECT id FROM albums where genres.id = albums.genre_id)")
		self._sql.commit()

	"""
		Add a new album to database
		arg: string, int, int
	"""
	def add_album(self, name, artist_id, genre_id):
		self._sql.execute("INSERT INTO albums (name, artist_id, genre_id) VALUES (?, ?, ?)",  (name, artist_id, genre_id))

	"""
		Add a new artist to database
		arg: string
	"""
	def add_artist(self, name):
		self._sql.execute("INSERT INTO artists (name) VALUES (?)", (name,))

	"""
		Add a new genre to database
		arg: string
	"""
	def add_genre(self, name):
		self._sql.execute("INSERT INTO genres (name) VALUES (?)", (name,))

	"""
		Add a new track to database
		arg: string, string, int, int, string, int
	"""
	def add_track(self, name, filepath, length, tracknumber, year, album_id):
		self._sql.execute("INSERT INTO tracks (name, filepath, length, tracknumber, year, album_id) VALUES (?, ?, ?, ?, ?, ?)", (name, filepath, length, tracknumber, year, album_id))

	"""
		Get genre id by name
		arg: string
		ret: int
	"""
	def get_genre_id_by_name(self, name):
		result = self._sql.execute("SELECT id from genres where name=?", (name,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return -1

	"""
		Get all availables genres
		ret: [(int, string)]
	"""
	def get_genres(self):
		genres = []
		result = self._sql.execute("SELECT id, name FROM genres ORDER BY name")
		for row in result:
			genres += (row,)
		return genres


	"""
		Get artist id by name
		arg: string
		ret: int
	"""
	def get_artist_id_by_name(self, name):
		result = self._sql.execute("SELECT id from artists where name=?", (name,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return -1

	"""
		Get artist name by id
		arg: int
		ret: string
	"""
	def get_artist_name_by_id(self, id):
		result = self._sql.execute("SELECT name from artists where id=?", (id,))
		name = result.fetchone()
		if name:
			return name[0]
		else:
			return _("Unknown")
	
	"""
		Get artist id by album id
		arg: int
		ret: int
	"""
	def get_artist_id_by_album_id(self, album_id):
		result = self._sql.execute("SELECT artist_id from albums where id=?", (album_id,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return -1

	"""
		Get artist name by album id
		arg: int
		ret: string
	"""
	def get_artist_name_by_album_id(self, album_id):
		result = self._sql.execute("SELECT artists.name from artists,albums where albums.id=? AND albums.artist_id == artists.id", (album_id,))
		name = result.fetchone()
		if name:
			return name[0]
		else:
			return _("Unknown")

	"""
		Get all available artists(id, name) for genre id
		arg: int
		ret: [(int, string)]
	"""
	def get_artists_by_genre_id(self, genre_id):
		artists = []
		result = self._sql.execute("SELECT DISTINCT artists.id, artists.name FROM artists,albums WHERE artists.id == albums.artist_id AND albums.genre_id=? ORDER BY artists.name", (genre_id,))
		for row in result:
			artists += (row,)
		return artists


	"""
		Get album id with name, artist id and genre id
		arg: string, int, int
		ret: int
	"""
	def get_album_id(self, name, artist_id, genre_id):
		result = self._sql.execute("SELECT id FROM albums where name=? AND artist_id=? AND genre_id=?", (name, artist_id, genre_id))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return 0

	"""
		Get album id for track id
		arg: int
		ret: int
	"""
	def get_album_id_by_track_id(self, track_id):
		result = self._sql.execute("SELECT albums.id FROM albums,tracks where tracks.album_id=albums.id AND tracks.id=?", (track_id,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return 0

	"""
		Get album name for id
		arg: int
		ret: string
	"""
	def get_album_name(self, album_id):
		result = self._sql.execute("SELECT name FROM albums where id=?", (album_id,))
		name = result.fetchone()
		if name:
			return name[0]
		else:
			return _("Unknown")
		
	"""
		Get album path for id
		arg: id
		ret: string
	"""
	def get_album_path(self, album_id):
		result = self._sql.execute("SELECT filepath FROM tracks where album_id=? LIMIT 1", (album_id,))
		path = result.fetchone()
		if path:
			return os.path.dirname(path[0])
		else:
			return ""
	
	"""
		Get all albums for artist id and genre id
		arg: int, int
		ret: [int]
	"""
	def get_albums_by_artist_and_genre_ids(self, artist_id, genre_id):
		albums = []
		result = self._sql.execute("SELECT id FROM albums WHERE artist_id=? and genre_id=?", (artist_id, genre_id))
		for row in result:
			albums += row
		return albums

	"""
		Get all albums for artist id and not prohibed id
		arg: int, int
		ret: [int]
	"""	
	def get_albums_by_artist_id(self, artist_id, prohibed_id = -1):
		albums = []
		result = self._sql.execute("SELECT id FROM albums WHERE artist_id=? and id!=?", (artist_id, prohibed_id))
		for row in result:
			albums += row
		return albums

	"""
		Get all albums for genre id
		arg: int
		ret: [int]
	"""	
	def get_albums_by_genre_id(self, genre_id):
		albums = []
		result = self._sql.execute("SELECT id FROM albums WHERE genre_id=? ORDER BY artist_id", (genre_id,))
		for row in result:
			albums += row
		return albums

	"""
		Get number of tracks in an album id
		arg: int
		ret: int
	"""
	def get_tracks_count_for_album_id(self, album_id):
		result = self._sql.execute("SELECT COUNT(*) FROM tracks where album_id=?", (album_id,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return -1

	"""
		Get tracks (id, name, filepath, length, year) for album id
		arg: int
		ret: [(int, string, string, int, string)]
	"""
	def get_tracks_by_album_id(self, album_id):
		tracks = []
		result = self._sql.execute("SELECT id, name, filepath, length, year FROM tracks WHERE album_id=? ORDER BY tracknumber" , (album_id,))
		for row in result:
			tracks += (row,)
		return tracks

	"""
		Get tracks id for album id
		arg: int
		ret: [int]
	"""
	def get_tracks_ids_by_album_id(self, album_id):
		tracks = []
		result = self._sql.execute("SELECT id FROM tracks WHERE album_id=? ORDER BY tracknumber" , (album_id,))
		for row in result:
			tracks += row
		return tracks

	"""
		Get track filepath for track id
		arg: int
		ret: string
	"""
	def get_track_filepath(self, id):
		result = self._sql.execute("SELECT filepath FROM tracks where id=?", (id,))
		path = result.fetchone()
		if path:
			return path[0]
		else:
			return ""

	"""
		Get all tracks filepath
		arg: int
		ret: string
	"""
	def get_tracks_filepath(self):
		tracks = []
		result = self._sql.execute("SELECT filepath FROM tracks;")
		for row in result:
			tracks += row
		return tracks

	"""
		Get track name for track id
		arg: int
		ret: string
	"""
	def get_track_name(self, id):
		result = self._sql.execute("SELECT name FROM tracks where id=?", (id,))
		name = result.fetchone()
		if name:
			return name[0]
		else:
			return ""
			
	"""
		Get track length for track id
		arg: int
		ret: int
	"""
	def get_track_length(self, id):
		result = self._sql.execute("SELECT length FROM tracks where id=?", (id,))
		length = result.fetchone()
		if length:
			return length[0]
		else:
			return 0
