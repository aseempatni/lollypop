from gi.repository import Gtk, Gdk, Gio, GLib, Tracker
from gettext import gettext as _, ngettext

from yaelle.collectionscanner import CollectionScanner
from yaelle.toolbar import Toolbar
from yaelle.database import Database
from yaelle.selectionlist import SelectionList
from yaelle.view import *

class Window(Gtk.ApplicationWindow):

	def __init__(self, app):
		Gtk.ApplicationWindow.__init__(self,
					       application=app,
					       title=_("Yaelle"))
		#self.connect('focus-in-event', self._windows_focus_cb)
		self.settings = Gio.Settings.new('org.gnome.Yaelle')
		self.add_action(self.settings.create_action('repeat'))
		selectAll = Gio.SimpleAction.new('selectAll', None)
		app.add_accelerator('<Primary>a', 'win.selectAll', None)
		#selectAll.connect('activate', self._on_select_all)
		self.add_action(selectAll)
		selectNone = Gio.SimpleAction.new('selectNone', None)
		#selectNone.connect('activate', self._on_select_none)
		self.add_action(selectNone)
		self.set_size_request(200, 100)
		self.set_icon_name('yaelle')

		self.prev_view = None
		self.curr_view = None

		self._setup_view()

		self._app = app

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

     #   self.connect("window-state-event", self._on_window_state_event)
     #   self.connect("configure-event", self._on_configure_event)
      #  self.proxy = Gio.DBusProxy.new_sync(Gio.bus_get_sync(Gio.BusType.SESSION, None),
      #                                      Gio.DBusProxyFlags.NONE,
       #                                     None,
        #                                    'org.gnome.SettingsDaemon',
         #                                   '/org/gnome/SettingsDaemon/MediaKeys',
          #                                  'org.gnome.SettingsDaemon.MediaKeys',
           #                                 None)
        #self._grab_media_player_keys()
        #try:
        #    self.proxy.connect('g-signal', self._handle_media_keys)
        #except GLib.GError:
            # We cannot grab media keys if no settings daemon is running
        #    pass


	def _setup_view(self):
		self._box = Gtk.HBox()
		self.toolbar = Toolbar()
		self.set_titlebar(self.toolbar.header_bar)
		self.toolbar.header_bar.show()

		self._db = Database()

		self._list_genres = SelectionList("Genre", 150)
		self._list_artists = SelectionList("Artist", 200)
		
		self._view = LoadingView()

		separator = Gtk.Separator()
		separator.show()
		self._box.pack_start(self._list_genres.widget, False, False, 0)
		self._box.pack_start(separator, False, False, 0)
		self._box.pack_start(self._list_artists.widget, False, False, 0)
		self._box.pack_start(self._view, True, False, 0)
		self.add(self._box)
		self._box.show()

		self._scanner = CollectionScanner()
		self._scanner.update(self._update_genres)
		
		self.show()
		
		
	def _update_genres(self, genres):
		self._list_genres.populate(genres)
		self._view.set_label(_("You can now listen to your music"))
		self._list_genres.connect('item-selected', self._update_artists)
		self._list_genres.widget.show()

	def _update_artists(self, obj, id):
		self._list_artists.populate(self._db.get_artists_by_genre(id))		
		self._list_artists.connect('item-selected', self._update_view)
		self._list_artists.widget.show()

	def _update_view(self, obj, id):
		self._box.remove(self._view)
		self._view = ArtistView(self._db, id)
		self._box.pack_start(self._view, True, True, 0)
		self._view.populate()
			

