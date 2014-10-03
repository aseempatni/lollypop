
from gi.repository import Gtk, GObject, Gdk

class Toolbar(GObject.GObject):

	def __init__(self):
		GObject.GObject.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Yaelle/headerbar.ui')
		self.header_bar = self._ui.get_object('header-bar')

		self.prevBtn = self._ui.get_object('previous_button')
		self.playBtn = self._ui.get_object('play_button')
		self.nextBtn = self._ui.get_object('next_button')
		self._playImage = self._ui.get_object('play_image')
		self._pauseImage = self._ui.get_object('pause_image')
		self.progressScale = self._ui.get_object('progress_scale')
		self.songPlaybackTimeLabel = self._ui.get_object('playback')
		self.songTotalTimeLabel = self._ui.get_object('duration')
		self.titleLabel = self._ui.get_object('title')
		self.artistLabel = self._ui.get_object('artist')
		self.coverImg = self._ui.get_object('cover')
		self.duration = self._ui.get_object('duration')
		self.repeatBtnImage = self._ui.get_object('playlistRepeat')

		if Gtk.Settings.get_default().get_property('gtk_application_prefer_dark_theme'):
			color = Gdk.Color(red=65535, green=65535, blue=65535)
		else:
			color = Gdk.Color(red=0, green=0, blue=0)
        #self._playImage.modify_fg(Gtk.StateType.ACTIVE, color)
        #self._pauseImage.modify_fg(Gtk.StateType.ACTIVE, color)

        #self._sync_repeat_image()

        #self.prevBtn.connect('clicked', self._on_prev_btn_clicked)
        #self.playBtn.connect('clicked', self._on_play_btn_clicked)
        #self.nextBtn.connect('clicked', self._on_next_btn_clicked)
        #self.progressScale.connect('button-press-event', self._on_progress_scale_event)
        #self.progressScale.connect('value-changed', self._on_progress_value_changed)
        #self.progressScale.connect('button-release-event', self._on_progress_scale_button_released)

		#self._search_button = self._ui.get_object('search-button')
		#self.dropdown = DropDown()
		#self.searchbar = Searchbar(self._stack_switcher, self._search_button, self.dropdown)
		#self.dropdown.initialize_filters(self.searchbar)
		self.header_bar.set_show_close_button(True)

	def reset_header_title(self):
		self.header_bar.set_custom_title(self._stack_switcher)

	def set_stack(self, stack):
		self._stack_switcher.set_stack(stack)

	def get_stack(self):
		return self._stack_switcher.get_stack()

	def hide_stack(self):
		self._stack_switcher.hide()

	def show_stack(self):
		self._stack_switcher.show()	
