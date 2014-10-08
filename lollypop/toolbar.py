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
		self.trackPlaybackTimeLabel = self._ui.get_object('playback')
		self.trackTotalTimeLabel = self._ui.get_object('duration')
		self._title_label = self._ui.get_object('title')
		self._artist_label = self._ui.get_object('artist')
		self._cover = self._ui.get_object('cover')
		self.duration = self._ui.get_object('duration')
		self.repeat_btnImage = self._ui.get_object('playlistRepeat')

		self._player = player
		self._player.connect("playback-status-changed", self._playback_status_changed)
		self._player.connect("current-changed", self._update_toolbar)
		self._player.set_progress_callback(self._progress_callback)

        #self._sync_repeat_image()

		self._prev_btn.connect('clicked', self._on_prev_btn_clicked)
		self._play_btn.connect('clicked', self._on_play_btn_clicked)
		self._next_btn.connect('clicked', self._on_next_btn_clicked)

		#self._search_button = self._ui.get_object('search-button')
		#self.dropdown = DropDown()
		#self.searchbar = Searchbar(self._stack_switcher, self._search_button, self.dropdown)
		#self.dropdown.initialize_filters(self.searchbar)
		self.header_bar.set_show_close_button(True)
		
	#def _on_progress_scale_button_released(self, scale, data):
		
	
	def _progress_callback(self, position, length):
		pass
	
	def _playback_status_changed(self, obj):
		if self._player.is_playing():
			self._prev_btn.set_sensitive(True)
			self._play_btn.set_sensitive(True)
			self._change_play_btn_status(self._pause_image, _("Pause"))
			self._next_btn.set_sensitive(True)

	def _update_toolbar(self, obj, track_id):
		album_id = self._db.get_album_by_track(track_id)
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
		
	def _on_prev_btn_clicked(self, obj):
		self._player.prev()

	def _on_play_btn_clicked(self, obj):
		if self._player.is_playing():
			self._player.pause()
			self._change_play_btn_status(self._play_image, _("Pause"))
		else:
			self._player.play()
			self._change_play_btn_status(self._pause_image, _("Play"))

		

	def _on_next_btn_clicked(self, obj):
		self._player.next()
		
	def _change_play_btn_status(self, image, status):
		self._play_btn.set_image(image)
		self._play_btn.set_tooltip_text(status)
