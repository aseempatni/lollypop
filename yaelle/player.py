from gi.repository import Gtk, Gdk, GLib, Gio, GObject, Gst, GstAudio
from yaelle.database import Database

class Player(GObject.GObject):
	
	__gsignals__ = {
        'current-changed': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        'playback-status-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'repeat-mode-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }
    
	def __init__(self, db):
		GObject.GObject.__init__(self)
		Gst.init(None)

		self.current_song = 0
		self._tracks = []

		self._db = db
		self._player = Gst.ElementFactory.make('playbin', 'player')
		
		self._bus = self._player.get_bus()
		self._bus.add_signal_watch()
		#self._bus.connect('message::state-changed', self._on_bus_state_changed)
		#self.bus.connect('message::error', self._onBusError)
		self._bus.connect('message::eos', self._on_bus_eos)

	def _on_bus_eos(self, bus, message):
		self.next()

	def is_playing(self):
		ok, state, pending = self._player.get_state(0)
		if ok == Gst.StateChangeReturn.ASYNC:
			return pending == Gst.State.PLAYING
		elif ok == Gst.StateChangeReturn.SUCCESS:
			return state == Gst.State.PLAYING
		else:
			return False

	def load(self, song_id):
		self._current_song = 0
		# Search song in current playlist
		for track in self._tracks:
			if track == song_id:
					break
			self._current_song += 1

		self.load_track(song_id)

	def load_track(self, song_id):
		self._player.set_property('uri', "file://"+self._db.get_song_filepath(song_id))

	def play(self):
		self._player.set_state(Gst.State.PLAYING)
		self.emit("playback-status-changed")

	def pause(self):
		self._player.set_state(Gst.State.PAUSED)
		self.emit("playback-status-changed")
			
	def stop(self):
		self._player.set_state(Gst.State.NULL)
		self.emit("playback-status-changed")
	
	def set_playing(self, playing):
		if playing:
			self.play()
		else:
			self.pause()

	def prev(self):
		self._current_song -= 1
		if self._current_song < 0:
			self._current_song = 0
		self.stop()
		self.load_track(self._tracks[self._current_song])
		self.play()
		self.emit("current-changed", self._tracks[self._current_song])
		
	def next(self):	
		self._current_song += 1
		if self._current_song > len(self._tracks):
			self._current_song = 0
		self.stop()
		self.load_track(self._tracks[self._current_song])
		self.play()
		self.emit("current-changed", self._tracks[self._current_song])

	def set_tracks(self, tracks):
		self._tracks = tracks
