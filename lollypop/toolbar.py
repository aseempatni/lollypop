from gettext import gettext as _, ngettext 
from gi.repository import Gtk, GObject, Gdk
from lollypop.albumart import AlbumArt

class Toolbar(GObject.GObject):

	def __init__(self, db, player):
		GObject.GObject.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/headerbar.ui')
		self.header_bar = self._ui.get_object('header-bar')

		self._db = db
		self._art = AlbumArt(db)

		self._prevBtn = self._ui.get_object('previous_button')
		self._playBtn = self._ui.get_object('play_button')
		self._nextBtn = self._ui.get_object('next_button')
		self._playImage = self._ui.get_object('play_image')
		self._pauseImage = self._ui.get_object('pause_image')
		self.progressScale = self._ui.get_object('progress_scale')
		self.songPlaybackTimeLabel = self._ui.get_object('playback')
		self.songTotalTimeLabel = self._ui.get_object('duration')
		self._titleLabel = self._ui.get_object('title')
		self._artistLabel = self._ui.get_object('artist')
		self._coverImg = self._ui.get_object('cover')
		self.duration = self._ui.get_object('duration')
		self.repeatBtnImage = self._ui.get_object('playlistRepeat')

		self._player = player
		self._player.connect("playback-status-changed", self._playback_status_changed)
		self._player.connect("current-changed", self._update_toolbar)

        #self._sync_repeat_image()

		self._prevBtn.connect('clicked', self._on_prev_btn_clicked)
		self._playBtn.connect('clicked', self._on_play_btn_clicked)
		self._nextBtn.connect('clicked', self._on_next_btn_clicked)
        #self.progressScale.connect('button-press-event', self._on_progress_scale_event)
        #self.progressScale.connect('value-changed', self._on_progress_value_changed)
        #self.progressScale.connect('button-release-event', self._on_progress_scale_button_released)

		#self._search_button = self._ui.get_object('search-button')
		#self.dropdown = DropDown()
		#self.searchbar = Searchbar(self._stack_switcher, self._search_button, self.dropdown)
		#self.dropdown.initialize_filters(self.searchbar)
		self.header_bar.set_show_close_button(True)
		
	
	def _playback_status_changed(self, obj):
		if self._player.is_playing():
			self._prevBtn.set_sensitive(True)
			self._playBtn.set_sensitive(True)
			self._change_playBtn_status(self._pauseImage, _("Pause"))
			self._nextBtn.set_sensitive(True)

	def _update_toolbar(self, obj, track_id):
		album_id = self._db.get_album_by_track(track_id)
		art = self._art.get_small(album_id)
		if art:
			self._coverImg.set_from_pixbuf(art)
			self._coverImg.show()
		else:
			self._coverImg.hide()
		
		title = self._db.get_song_name(track_id)
		artist = self._db.get_artist_name_by_album_id(album_id)
		self._titleLabel.set_text(title)
		self._artistLabel.set_text(artist)
		
	def _on_prev_btn_clicked(self, obj):
		self._player.prev()

	def _on_play_btn_clicked(self, obj):
		if self._player.is_playing():
			self._player.pause()
			self._change_playBtn_status(self._playImage, _("Pause"))
		else:
			self._player.play()
			self._change_playBtn_status(self._pauseImage, _("Play"))

		

	def _on_next_btn_clicked(self, obj):
		self._player.next()
		
	def _change_playBtn_status(self, image, status):
		self._playBtn.set_image(image)
		self._playBtn.set_tooltip_text(status)
