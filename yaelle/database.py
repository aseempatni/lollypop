#!/usr/bin/python
# Copyright (c) 2014 Cedric Bellegarde <gnumdk@gmail.com>
#

import sqlite3
import os

class Database:

	DB_PATH = os.path.expanduser ("~") +  "/.local/share/yaelle.db"

	create_albums = '''CREATE TABLE albums (id INTEGER PRIMARY KEY AUTOINCREMENT,
						name TEXT NOT NULL,
						artist_id INT NOT NULL,
						genre_id INT NOT NULL)'''
	create_artists = '''CREATE TABLE artists (id INTEGER PRIMARY KEY AUTOINCREMENT,
						  name TEXT NOT NULL)'''
	create_genres = '''CREATE TABLE genres (id INTEGER PRIMARY KEY AUTOINCREMENT,
						name TEXT NOT NULL)'''
	create_songs = '''CREATE TABLE songs (id INTEGER PRIMARY KEY AUTOINCREMENT,
				              name TEXT NOT NULL,
					      filename TEXT NOT NULL,
				              length TEXT NOT NULL,
					      tracknumber TEXT NOT NULL,
					      year TEXT NOT NULL,
					      album_id INT NOT NULL)'''
	def __init__(self):
		pass

	def init(self, sql):
		try:
			sql.execute(self.create_albums)
			sql.execute(self.create_artists)
			sql.execute(self.create_genres)
			sql.execute(self.create_songs)
		except Exception as e:
			print(e)
			pass
		sql.commit()

	def reset(self, sql):
		sql.execute("DELETE FROM albums")
		sql.execute("DELETE FROM artists")
		sql.execute("DELETE FROM genres")
		sql.execute("DELETE FROM songs")
		sql.commit()

	def clean(self, sql):
		sql.execute("DELETE FROM albums WHERE NOT EXISTS (SELECT id FROM songs where albums.id = songs.album_id)")
		sql.execute("DELETE FROM artists WHERE NOT EXISTS (SELECT id FROM albums where artists.id = albums.artist_id)")
		sql.execute("DELETE FROM genres WHERE NOT EXISTS (SELECT id FROM albums where genres.id = albums.genre_id)")
		sql.commit()

	def add_album(self, sql, name, artist_id, genre_id):
		sql.execute("INSERT INTO albums (name, artist_id, genre_id) VALUES (?, ?, ?)",  (name, artist_id, genre_id))
		sql.commit()

	def add_artist(self, sql, name):
		sql.execute("INSERT INTO artists (name) VALUES (?)", (name,))
		sql.commit()

	def add_genre(self, sql, name):
		sql.execute("INSERT INTO genres (name) VALUES (?)", (name,))
		sql.commit()

	def add_song(self, sql, name, filename, length, tracknumber, year, album_id):
		sql.execute("INSERT INTO songs (name, filename, length, tracknumber, year, album_id) VALUES (?, ?, ?, ?, ?, ?)", (name, filename, length, tracknumber, year, album_id))
		sql.commit()

	# Return genre id
	def get_genre(self, sql, name):
		result = sql.execute("SELECT id from genres where name=?", (name,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return 0

	# Return a list of genre (id, name)
	def get_genres(self, sql):
		genres = []
		result = sql.execute("SELECT id, name FROM genres")
		for row in result:
			genres += (row,)
		return genres


	# Return artist id
	def get_artist(self, sql, name):
		result = sql.execute("SELECT id from artists where name=?", (name,))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return 0

	# Return a list of artists (id, name)
	def get_artists_by_genre(self, sql, genre_id):
		artists = []
		result = sql.execute("SELECT artists.id, artists.name FROM artists,albums WHERE artists.id == albums.artist_id AND albums.genre_id=?", (genre_id,))
		for row in result:
			artists += (row,)
		return artists


	# Return album id
	def get_album(self, sql, name, artist_id, genre_id):
		result = sql.execute("SELECT id from albums where name=? AND artist_id=? AND genre_id=?", (name, artist_id, genre_id))
		id = result.fetchone()
		if id:
			return id[0]
		else:
			return 0
		
	# Return a list of albums (id, name)
	def get_albums_by_artist(self, sql, artist_id):
		albums = []
		result = sql.execute("SELECT id, name FROM albums WHERE artist_id=?", (artist_id,))
		for row in result:
			albums += (row,)
		return albums

	# Return a list of albums
	def get_albums_by_genre(self, sql, genre_id):
		albums = []
		result = sql.execute("SELECT id, name FROM albums WHERE genre_id=?", (genre_id,))
		for row in result:
			albums += (row,)
		return albums

	# Return a list of songs (id, name, filename, length, tracknumber, year)
	def get_songs_by_album(self, sql, album_id):
		songs = []
		result = sql.execute("SELECT id, name, filename, length, tracknumber, year FROM songs WHERE album_id=?", (album_id,))
		for row in result:
			songs += (row,)
		return songs

	# Return a list of songs filenames
	def get_songs_filenames(self, sql):
		songs = []
		result = sql.execute("SELECT filename FROM songs;")
		for row in result:
			songs += row
		return songs

	# Remove song with filename
	def remove_song(self, sql, filename):
		sql.execute("DELETE FROM songs where filename=?",  (filename,))
		sql.commit()
