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
        'repeat-mode-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }
    
	def __init__(self, db):
		GObject.GObject.__init__(self)
		Gst.init(None)

		self._current_track_number = 0
		self._current_track_album_id = 0
		self._current_track_id = 0
		self._albums = []
		self._progress_callback = None
		self._timeout = None
		self._shuffle = False
		self._shuffle_history = []
		self._party = False

		self._db = db
		self._player = Gst.ElementFactory.make('playbin', 'player')
		
		self._bus = self._player.get_bus()
		self._bus.add_signal_watch()
		#self._bus.connect('message::state-changed', self._on_bus_state_changed)
		#self.bus.connect('message::error', self._onBusError)
		self._bus.connect('message::eos', self._on_bus_eos)

	def _on_bus_eos(self, bus, message):
		if self._party:
			self.shuffle_next()
		else:
			self.next()

	def _update_position(self):
		if self._progress_callback:
			position = self._player.query_position(Gst.Format.TIME)[1] / 1000000000
			if position > 0:
				self._progress_callback(position * 60)
		return True

	def _load_track(self, track_id):
		self._current_track_id = track_id
		self.emit("current-changed", track_id)
		self._player.set_property('uri', "file://"+self._db.get_track_filepath(track_id))
		self._duration = self._db.get_track_length(track_id)
		if self._shuffle or self._party:
			self._shuffle_history.append(track_id)

	"""
		Return a random track and make sure it has never been played
	"""
	def _get_random(self):
		for album in sorted(self._albums, key=lambda *args: random.random()):
			tracks = self._db.get_tracks_ids_by_album_id(album)
			for track in sorted(tracks, key=lambda *args: random.random()):
					if not track in self._shuffle_history:
						return track
		return None

	def is_playing(self):
		ok, state, pending = self._player.get_state(0)
		if ok == Gst.StateChangeReturn.ASYNC:
			return pending == Gst.State.PLAYING
		elif ok == Gst.StateChangeReturn.SUCCESS:
			return state == Gst.State.PLAYING
		else:
			return False

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


	def load(self, track_id):
		self.stop()
		self._load_track(track_id)
		self.play()


	def play(self):
		self._player.set_state(Gst.State.PLAYING)
		if not self._timeout:
			self._timeout = GLib.timeout_add(1000, self._update_position)
		self.emit("playback-status-changed")

	def pause(self):
		self._player.set_state(Gst.State.PAUSED)
		self.emit("playback-status-changed")
		if self._timeout:
			GLib.source_remove(self._timeout)
			self._timeout = None

			
	def stop(self):
		self._player.set_state(Gst.State.NULL)
		if self._timeout:
			GLib.source_remove(self._timeout)
			self._timeout = None

	
	def play_pause(self):
		if self.is_playing():
			self.pause()
		else:
			self.play()

	def prev(self):
		if self._shuffle or self._party:
			try:
				track_id = self._shuffle_history[-2]
				# We remove to last items because playing will readd track_id to list
				self._shuffle_history.pop()
				self._shuffle_history.pop()
			except Exception as e:
				print(e)
				track_id = None
		else:
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
		
	def next(self):
		# Get a random album/track
		if self._shuffle or self._party:
			self.shuffle_next()
		else:
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
		Next track in shuffle mode
	"""
	def shuffle_next(self):
		track_id = self._get_random()
		# Need to clear history
		if not track_id:
			self.shuffle_history = []
			self.shuffle_next()
			return
		self._current_track_album_id = self._db.get_album_id_by_track_id(track_id)
		self.load(track_id)


	def seek(self, position):
		self._player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, position * Gst.SECOND)

	def get_current_track_id(self):
		return self._current_track_id

	def set_shuffle(self, shuffle):
		self._shuffle_history = []
		self._shuffle = shuffle

	def set_party(self, party):
		self._party = party
		self._shuffle_history = []
		if party:
			self._albums = self._db.get_all_albums_id()
			track_id = self._get_random()
			self.load(track_id)
			self._current_track_album_id = self._db.get_album_id_by_track_id(track_id)

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
