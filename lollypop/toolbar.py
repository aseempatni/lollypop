from gettext import gettext as _, ngettext 
from gi.repository import Gtk, GObject, Gdk
from lollypop.albumart import AlbumArt

class Toolbar(GObject.GObject):

	def __init__(self, db, player):
		GObject.GObject.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/headerbar.ui')
		self.header_bar = self._ui.get_object('header-bar')
		self.header_bar.set_custom_title(self._ui.get_object('title-box'))
		self._db = db
		self._art = AlbumArt(db)

		self._prev_btn = self._ui.get_object('previous_button')
		self._play_btn = self._ui.get_object('play_button')
		self._next_btn = self._ui.get_object('next_button')
		self._play_image = self._ui.get_object('play_image')
		self._pause_image = self._ui.get_object('pause_image')

		self._progress = self._ui.get_object('progress_scale')
		self._progress.set_sensitive(False)
		self._time_label = self._ui.get_object('playback')
		self._total_time_label = self._ui.get_object('duration')
		
		self._title_label = self._ui.get_object('title')
		self._artist_label = self._ui.get_object('artist')
		self._cover = self._ui.get_object('cover')
		self._infobox = self._ui.get_object('infobox')
		
		self._player = player
		self._player.connect("playback-status-changed", self._playback_status_changed)
		self._player.connect("current-changed", self._update_toolbar)
		self._player.set_progress_callback(self._progress_callback)
		
		self._shuffle = self._ui.get_object('shuffleButton')
		self._shuffle.connect("toggled", self._shuffle_update)

		self._party = self._ui.get_object('partyButton')
		self._party.connect("toggled", self._party_update)

		self._progress.connect('button-release-event', self._on_progress_scale_button)

		self._prev_btn.connect('clicked', self._on_prev_btn_clicked)
		self._play_btn.connect('clicked', self._on_play_btn_clicked)
		self._next_btn.connect('clicked', self._on_next_btn_clicked)

		#self._search_button = self._ui.get_object('search-button')
		#self.dropdown = DropDown()
		#self.searchbar = Searchbar(self._stack_switcher, self._search_button, self.dropdown)
		#self.dropdown.initialize_filters(self.searchbar)
		self.header_bar.set_show_close_button(True)
		
	def _on_progress_scale_button(self, scale, data):
		self._player.seek(scale.get_value()/60)
	
	def _progress_callback(self, position):
		self._progress.set_value(position)
		self._time_label.set_text(self._seconds_to_string(position/60))
	
	def _playback_status_changed(self, obj):
		playing = self._player.is_playing()

		self._progress.set_sensitive(playing)
		if playing:
			self._change_play_btn_status(self._pause_image, _("Pause"))
			self._prev_btn.set_sensitive(True)
			self._play_btn.set_sensitive(True)
			self._next_btn.set_sensitive(True)
		else:
			self._change_play_btn_status(self._play_image, _("Play"))

	def _update_toolbar(self, obj, track_id):
		album_id = self._db.get_album_id_by_track_id(track_id)
		art = self._art.get_small(album_id)
		if art:
			self._cover.set_from_pixbuf(art)
			self._cover.show()
		else:
			self._cover.hide()
		
		title = self._db.get_track_name(track_id)
		artist = self._db.get_artist_name_by_album_id(album_id)
		self._title_label.set_text(title)
		self._artist_label.set_text(artist)
		self._progress.set_value(0.0)
		duration = self._db.get_track_length(track_id)
		self._progress.set_range(0.0, duration * 60)
		self._total_time_label.set_text(self._seconds_to_string(duration))
		self._total_time_label.show()
		self._time_label.set_text("0:00")
		self._time_label.show()
		
	def _on_prev_btn_clicked(self, obj):
		self._player.prev()

	def _on_play_btn_clicked(self, obj):
		if self._player.is_playing():
			self._player.pause()
			self._change_play_btn_status(self._play_image, _("Play"))
		else:
			self._player.play()
			self._change_play_btn_status(self._pause_image, _("PausePlay"))

	def _on_next_btn_clicked(self, obj):
			self._player.next()		
		
	def _seconds_to_string(self, duration):
		seconds = duration
		minutes = seconds // 60
		seconds %= 60

		return '%i:%02i' % (minutes, seconds)
		
	def _change_play_btn_status(self, image, status):
		self._play_btn.set_image(image)
		self._play_btn.set_tooltip_text(status)

	def _shuffle_update(self, obj):
		self._player.set_shuffle(self._shuffle.get_active())

	def _party_update(self, obj):
		settings = Gtk.Settings.get_default()
		active = self._party.get_active()
		settings.set_property("gtk-application-prefer-dark-theme", active)
		self._player.set_party(active)

	def get_infobox(self):
		return self._infobox


