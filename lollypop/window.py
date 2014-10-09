from gi.repository import Gtk, Gdk, Gio, GLib, Tracker
from gettext import gettext as _, ngettext

from lollypop.collectionscanner import CollectionScanner
from lollypop.toolbar import Toolbar
from lollypop.database import Database
from lollypop.selectionlist import SelectionList
from lollypop.player import Player
from lollypop.view import *
from lollypop.notification import NotificationManager

class Window(Gtk.ApplicationWindow):

	def __init__(self, app):
		Gtk.ApplicationWindow.__init__(self,
					       application=app,
					       title=_("Lollypop"))
		
		self.settings = Gio.Settings.new('org.gnome.Lollypop')

		self.set_size_request(200, 100)
		self.set_icon_name('lollypop')
		self._app = app
		self._artist_signal_id = 0
		
		self._db = Database()
		self._player = Player(self._db)
		NotificationManager(self._player, self._db)
		self._scanner = CollectionScanner()

		size_setting = self.settings.get_value('window-size')
		if isinstance(size_setting[0], int) and isinstance(size_setting[1], int):
			self.resize(size_setting[0], size_setting[1])

		position_setting = self.settings.get_value('window-position')
		if len(position_setting) == 2 \
			and isinstance(position_setting[0], int) \
			and isinstance(position_setting[1], int):
			self.move(position_setting[0], position_setting[1])

		if self.settings.get_value('window-maximized'):
			self.maximize()

		self.connect("window-state-event", self._on_window_state_event)
		self.connect("configure-event", self._on_configure_event)
		
		self._setup_view()
		self._proxy = Gio.DBusProxy.new_sync(Gio.bus_get_sync(Gio.BusType.SESSION, None),
											 Gio.DBusProxyFlags.NONE,
											 None,
											 'org.gnome.SettingsDaemon',
											 '/org/gnome/SettingsDaemon/MediaKeys',
											 'org.gnome.SettingsDaemon.MediaKeys',
											 None)
		self._grab_media_player_keys()
		try:
			self._proxy.connect('g-signal', self._handle_media_keys)
		except GLib.GError:
            # We cannot grab media keys if no settings daemon is running
			pass


	def _setup_view(self):
		self._box = Gtk.Grid()
		self.toolbar = Toolbar(self._db, self._player)
		self.set_titlebar(self.toolbar.header_bar)
		self.toolbar.header_bar.show()
		self.toolbar.get_infobox().connect("button-press-event", self._show_current_album)

		self._list_genres = SelectionList("Genre", 150)
		self._list_artists = SelectionList("Artist", 200)
		
		self._view = LoadingView()

		separator = Gtk.Separator()
		separator.show()
		self._box.add(self._list_genres.widget)
		self._box.add(separator)
		self._box.add(self._list_artists.widget)
		self._box.add(self._view)
		self.add(self._box)
		self._box.show()
		self.show()
		self.connect("map-event", self._mapped_window)
		
	def _mapped_window(self, obj, data):
		self._scanner.update(self._update_genres)
		
	def _grab_media_player_keys(self):
		try:
			self._proxy.call_sync('GrabMediaPlayerKeys',
								 GLib.Variant('(su)', ('Lollypop', 0)),
								 Gio.DBusCallFlags.NONE,
								 -1,
								 None)
		except GLib.GError:
			# We cannot grab media keys if no settings daemon is running
			pass

	def _handle_media_keys(self, proxy, sender, signal, parameters):
		if signal != 'MediaPlayerKeyPressed':
			print('Received an unexpected signal \'%s\' from media player'.format(signal))
			return
		response = parameters.get_child_value(1).get_string()
		if 'Play' in response:
			self._player.play_pause()
		elif 'Stop' in response:
			self._player.stop()
		elif 'Next' in response:
			self._player.next()
		elif 'Previous' in response:
			self._player.prev()
			
	def _update_genres(self, genres):
		self._list_genres.populate(genres)
		self._view.set_label(_("You can now listen to your music"))
		self._list_genres.connect('item-selected', self._update_artists)
		self._list_genres.widget.show()

	def _update_artists(self, obj, id):
		if self._artist_signal_id:
			self._list_artists.disconnect(self._artist_signal_id)
		self._list_artists.populate(self._db.get_artists_by_genre_id(id))
		self._artist_signal_id = self._list_artists.connect('item-selected', self._update_view_artist)
		self._list_artists.widget.show()
		self._update_view_albums(self, id)
		self._genre_id = id

	def _update_view_artist(self, obj, id):
		self._box.remove(self._view)
		self._view = ArtistView(self._db, self._player, self._genre_id, id)
		self._box.add(self._view)
		self._view.populate()
			
	def _update_view_albums(self, obj, id):
		self._box.remove(self._view)
		self._view = AlbumView(self._db, self._player, id)
		self._box.add(self._view)
		self._view.populate()
			
	def _on_configure_event(self, widget, event):
		size = widget.get_size()
		self.settings.set_value('window-size', GLib.Variant('ai', [size[0], size[1]]))

		position = widget.get_position()
		self.settings.set_value('window-position', GLib.Variant('ai', [position[0], position[1]]))

	def _on_window_state_event(self, widget, event):
		self.settings.set_boolean('window-maximized', 'GDK_WINDOW_STATE_MAXIMIZED' in event.new_window_state.value_names)

	def _show_current_album(self, obj, data):
			self._view.update_context()
			self._view.update_content()
