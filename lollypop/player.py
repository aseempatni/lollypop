from gi.repository import Gtk, Gdk, GLib, Gio, GObject, Gst, GstAudio
from lollypop.database import Database

class Player(GObject.GObject):
	
	__gsignals__ = {
        'current-changed': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        'playback-status-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'repeat-mode-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }
    
	def __init__(self, db):
		GObject.GObject.__init__(self)
		Gst.init(None)

		self._current_track_pos = 0
		self._current_track_id = 0
		self._tracks = []
		self._progress_callback = None
		self._timeout = None

		self._db = db
		self._player = Gst.ElementFactory.make('playbin', 'player')
		
		self._bus = self._player.get_bus()
		self._bus.add_signal_watch()
		#self._bus.connect('message::state-changed', self._on_bus_state_changed)
		#self.bus.connect('message::error', self._onBusError)
		self._bus.connect('message::eos', self._on_bus_eos)

	def _on_bus_eos(self, bus, message):
		self.next()

	def _update_position(self):
		if self._progress_callback:
			position = self._player.query_position(Gst.Format.TIME)[1] / 1000000000
			if position > 0:
				self._progress_callback(position * 60)
		return True

	def _load_track(self, track_id):
		self._player.set_property('uri', "file://"+self._db.get_track_filepath(track_id))
		self._duration = self._db.get_track_length(track_id)
		self._current_track_id = track_id
		self.emit("current-changed", track_id)

	def is_playing(self):
		ok, state, pending = self._player.get_state(0)
		if ok == Gst.StateChangeReturn.ASYNC:
			return pending == Gst.State.PLAYING
		elif ok == Gst.StateChangeReturn.SUCCESS:
			return state == Gst.State.PLAYING
		else:
			return False

	def load(self, track_id):
		self._current_track_pos = 0
		# Search track in current playlist
		for track in self._tracks:
			if track == track_id:
					break
			self._current_track_pos += 1

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
		self._current_track_pos -= 1
		if self._current_track_pos < 0:
			self._current_track_pos = 0
		self.stop()
		self._load_track(self._tracks[self._current_track_pos])
		self.play()
		
	def next(self):	
		self._current_track_pos += 1
		if self._current_track_pos > len(self._tracks):
			self._current_track_pos = 0
		self.stop()
		self._load_track(self._tracks[self._current_track_pos])
		self.play()

	def seek(self, position):
		self._player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, position * Gst.SECOND)

	def get_current_track_id(self):
		return self._current_track_id

	def set_tracks(self, tracks):
		self._tracks = tracks
	
	"""
		Set progress callback, will be called every seconds
		Callback is a function with one float arg position
	"""
	def set_progress_callback(self, callback):
		self._progress_callback = callback
