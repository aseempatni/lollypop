#!/usr/bin/python
# Copyright (c) 2014 Cedric Bellegarde <gnumdk@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# Many code inspiration from gnome-music at the GNOME project

from gi.repository import Gtk, Gdk, GLib, Gio, GObject, Gst, GstAudio
from lollypop.database import Database
import random

class PlaybackStatus:
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2

class Player(GObject.GObject):
	
	__gsignals__ = {
        'current-changed': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        'playback-status-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'playlist-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

	"""
		Create a gstreamer bin and listen to signals on bus
	"""
	def __init__(self, db):
		GObject.GObject.__init__(self)
		Gst.init(None)

		self._current_track_number = -1
		self._current_track_album_id = -1
		self._current_track_id = -1
		self._albums = []
		self._progress_callback = None
		self._timeout = None
		self._shuffle = False
		self._shuffle_history = []
		self._party = False
		self._party_ids = []
		self._playlist = []

		self._db = db
		self._player = Gst.ElementFactory.make('playbin', 'player')
		
		self._bus = self._player.get_bus()
		self._bus.add_signal_watch()
		#self._bus.connect('message::state-changed', self._on_bus_state_changed)
		#self.bus.connect('message::error', self._onBusError)
		self._bus.connect('message::eos', self._on_bus_eos)


	"""
		Return True if player is playing
	"""
	def is_playing(self):
		ok, state, pending = self._player.get_state(0)
		if ok == Gst.StateChangeReturn.ASYNC:
			return pending == Gst.State.PLAYING
		elif ok == Gst.StateChangeReturn.SUCCESS:
			return state == Gst.State.PLAYING
		else:
			return False

	"""
		Return playback status:
			- PlaybackStatus.STOPPED
			- PlaybackStatus.PLAYING
			- PlaybackStatus.PAUSED
	"""
	def get_playback_status(self):
		ok, state, pending = self._player.get_state(0)
		if ok == Gst.StateChangeReturn.ASYNC:
			state = pending
		elif (ok != Gst.StateChangeReturn.SUCCESS):
			return PlaybackStatus.STOPPED

		if state == Gst.State.PLAYING:
			return PlaybackStatus.PLAYING
		elif state == Gst.State.PAUSED:
			return PlaybackStatus.PAUSED
		else:
			return PlaybackStatus.STOPPED


	"""
		Stop current track, load track_id and play it
	"""
	def load(self, track_id):
		self.stop()
		self._load_track(track_id)
		self.play()


	"""
		Change player state to PLAYING
	"""
	def play(self):
		self._player.set_state(Gst.State.PLAYING)
		if not self._timeout:
			self._timeout = GLib.timeout_add(1000, self._update_position)
		self.emit("playback-status-changed")

	"""
		Change player state to PAUSED
	"""
	def pause(self):
		self._player.set_state(Gst.State.PAUSED)
		self.emit("playback-status-changed")
		if self._timeout:
			GLib.source_remove(self._timeout)
			self._timeout = None

	"""
		Change player state to STOPPED
	"""
	def stop(self):
		self._player.set_state(Gst.State.NULL)
		if self._timeout:
			GLib.source_remove(self._timeout)
			self._timeout = None

	"""
		Set PLAYING if PAUSED
		Set PAUSED if PLAYING
	"""
	def play_pause(self):
		if self.is_playing():
			self.pause()
		else:
			self.play()

	"""
		Play previous track
		If shuffle or party => go backward in shuffle history
		Else => Get previous track in currents albums
	"""
	def prev(self):
		track_id = None
		if self._shuffle or self._party:
			try:
				track_id = self._shuffle_history[-2]
				# We remove to last items because playing will readd track_id to list
				self._shuffle_history.pop()
				self._shuffle_history.pop()
			except Exception as e:
				print(e)
				track_id = None
		elif self._current_track_number != -1:
			tracks = self._db.get_tracks_ids_by_album_id(self._current_track_album_id)
			if self._current_track_number <=0 : #Prev album
				pos = self._albums.index(self._current_track_album_id)
				if pos - 1 < 0: #we are on last album, go to first
					pos = len(self._albums) - 1
				else:
					pos -= 1
				self._current_track_album_id = self._albums[pos]
				tracks = self._db.get_track_id_by_album_id(self._current_track_album_id)
				self._current_track_number = len(tracks) - 1
				track_id = self._db.get_tracks_ids_by_album_id(self._albums[pos])[self._current_track_number]
			else:
				self._current_track_number -= 1
				track_id = tracks[self._current_track_number]
	
		if track_id:			
			self.load(track_id)
	
	"""
		Play next track
		If shuffle or party => get a random file not already played
		Else => get next track in currents albums
	"""
	def next(self):
		# Look first at user playlist
		if len(self._playlist) > 0:
			self.load(self._playlist.pop(0))
		# Get a random album/track
		elif self._shuffle or self._party:
			self._shuffle_next()
		elif self._current_track_number != -1:
			track_id = None
			tracks = self._db.get_tracks_ids_by_album_id(self._current_track_album_id)
			if self._current_track_number + 1 >= len(tracks): #next album
				pos = self._albums.index(self._current_track_album_id)
				if pos +1 >= len(self._albums): #we are on last album, go to first
					pos = 0
				else:
					pos += 1
				self._current_track_album_id = self._albums[pos]
				self._current_track_number = 0
				track_id = self._db.get_tracks_ids_by_album_id(self._albums[pos])[0]
			else:
				self._current_track_number += 1
				track_id = tracks[self._current_track_number]	
			self.load(track_id)

	"""
		Seek current track to position
	"""
	def seek(self, position):
		self._player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, position * Gst.SECOND)

	"""
		Return current track id
	"""
	def get_current_track_id(self):
		return self._current_track_id

	"""
		Set shuffle mode on if shuffle
		Clear shuffle history
	"""
	def set_shuffle(self, shuffle):
		self._shuffle_history = []
		self._shuffle = shuffle
		if not shuffle:
			album_id = self._db.get_album_id_by_track_id(self._current_track_id)
			artist_id = self._db.get_artist_id_by_album_id(album_id)
			genre_id = self._db.get_genre_id_by_album_id(album_id)
			self.set_albums(artist_id, genre_id, self._current_track_id)

	"""
		Set party mode on
		Play a new random track
	"""
	def set_party(self, party):
		self._party = party
		self._shuffle_history = []
		if party:
			if len(self._party_ids) > 0:
				self._albums = self._db.get_party_albums_ids(self._party_ids)
			else:
				self._albums = self._db.get_all_albums_ids()
			track_id = self._get_random()
			self.load(track_id)
			self._current_track_album_id = self._db.get_album_id_by_track_id(track_id)
		else:
			album_id = self._db.get_album_id_by_track_id(self._current_track_id)
			artist_id = self._db.get_artist_id_by_album_id(album_id)
			genre_id = self._db.get_genre_id_by_album_id(album_id)
			self.set_albums(artist_id, genre_id, self._current_track_id)

	"""
		Set party ids to ids
		Party ids are genres_id (and specials ids) used to populate party mode
	"""
	def set_party_ids(self, ids):
		self._party_ids = ids

	"""
		Return party ids
	"""
	def get_party_ids(self):
		return self._party_ids

	"""
		Return True if party mode on
	"""
	def is_party(self):
		return self._party

	"""
		Set album list (for next/prev)
		If artist_id and genre_id => Albums for artist_id and genre_id
		Elif genre_id => Albums for genre_id
		Else => Albums populars
	"""
	def set_albums(self, artist_id, genre_id, track_id):
		if self._party:
			return
		self._albums = []
		# We are in artist view, add all albums from artist for genre
		if artist_id:
			self._albums = self._db.get_albums_by_artist_and_genre_ids(artist_id, genre_id)
		# We are in album view, add all albums from genre
		elif genre_id:
			self._albums = self._db.get_albums_by_genre_id(genre_id)
		# We are in popular view, add populars albums
		else:
			self._albums = self._db.get_albums_popular()
		album_id = self._db.get_album_id_by_track_id(track_id)
		tracks = self._db.get_tracks_ids_by_album_id(album_id)
		self._current_track_number = tracks.index(track_id) 
		self._current_track_album_id = album_id

	"""
		Set progress callback, will be called every seconds
		Callback is a function with one float arg position
	"""
	def set_progress_callback(self, callback):
		self._progress_callback = callback

	"""
		Convert seconds to a pretty string
	"""
	def seconds_to_string(self, duration):
		seconds = duration
		minutes = seconds // 60
		seconds %= 60

		return '%i:%02i' % (minutes, seconds)

	"""
		Add track to playlist
	"""
	def add_to_playlist(self, track_id):
		self._playlist.append(track_id)

	"""
		Remove track from playlist
	"""

	def del_from_playlist(self, track_id):
		self._playlist.remove(track_id)

	"""
		Set playlist to new_playlist
	"""
	def set_playlist(self, new_playlist):
		self._playlist = new_playlist
		self.emit("playlist-changed")
	"""
		Return playlist
	"""
	def get_playlist(self):
		return self._playlist

	"""
		ReturnTrue if track_id exist in playlist
	"""
	def is_in_playlist(self, track_id):
		return track_id in self._playlist

	"""
		Return track position in playlist
	"""
	def get_track_position(self, track_id):
		return self._playlist.index(track_id)

#######################
# PRIVATE             #
#######################

	"""
		Next track in shuffle mode
	"""
	def _shuffle_next(self):
		track_id = self._get_random()
		# Need to clear history
		if not track_id:
			self.shuffle_history = []
			self._shuffle_next()
			return
		self._current_track_album_id = self._db.get_album_id_by_track_id(track_id)
		self.load(track_id)

	"""
		Return a random track and make sure it has never been played
	"""
	def _get_random(self):
		for album in sorted(self._albums, key=lambda *args: random.random()):
			tracks = self._db.get_tracks_ids_by_album_id(album)
			for track in sorted(tracks, key=lambda *args: random.random()):
					if not track in self._shuffle_history:
						return track
			# No new tracks for this album, remove it
			self._albums.remove(album)
		return None

	"""
		On End Of Stream => next()
	"""
	def _on_bus_eos(self, bus, message):
		self.next()

	"""
		Call progress callback with new position
	"""
	def _update_position(self):
		if self._progress_callback:
			position = self._player.query_position(Gst.Format.TIME)[1] / 1000000000
			if position > 0:
				self._progress_callback(position * 60)
		return True

	"""
		Load track_id
		Emit "current-changed" to notify others components
		Add track to shuffle history if needed
	"""
	def _load_track(self, track_id):
		self._current_track_id = track_id
		self.emit("current-changed", track_id)
		self._player.set_property('uri', "file://"+self._db.get_track_filepath(track_id))
		self._duration = self._db.get_track_length(track_id)
		if self._shuffle or self._party:
			self._shuffle_history.append(track_id)
