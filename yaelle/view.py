from gi.repository import Gtk, GObject, Gdk
from gettext import gettext as _

from yaelle.database import Database
from yaelle.widgets import *

class LoadingView(Gtk.HBox):
	def __init__(self):
		Gtk.HBox.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Yaelle/Loading.ui')
		self.set_property('halign', Gtk.Align.CENTER)
		self.set_property('valign', Gtk.Align.CENTER)
		self._label = self._ui.get_object('label')
		self._label.set_label(_("Loading please wait..."))
		self.pack_start(self._ui.get_object('image'),
											False, False, 0)
		self.pack_start(self._label, False, False, 0)
		self.show_all()
		

	def set_label(self, str):
		self._label.set_label(str)
		

class ArtistView(Gtk.VBox):

	def __init__(self, db, artist_id):
		Gtk.VBox.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Yaelle/ArtistView.ui')
		self.set_border_width(0)
		
		self._artist_id = artist_id
		self._db = db

		artist_name = self._db.get_artist_by_id(artist_id)
		self._ui.get_object('artist').set_label(artist_name)

		self._widgets = []
		self._albumbox = Gtk.VBox()
		
		self._scrolledWindow = Gtk.ScrolledWindow()
		self._scrolledWindow.set_policy(
										Gtk.PolicyType.NEVER,
										Gtk.PolicyType.AUTOMATIC)
		self._scrolledWindow.add(self._albumbox)
		self.pack_start(self._ui.get_object('ArtistView'),
											False, False, 0)
		self.pack_start(self._scrolledWindow, True, True, 0)
		self.show_all()
        
	def _add_album(self, album_id):
		widget = AlbumWidgetSongs(self._db, album_id)
		self._albumbox.pack_start(widget, True, True, 0)
		self._widgets.append(widget)
		widget.show()		

	def populate(self):
		for (id, name) in self._db.get_albums_by_artist(self._artist_id):
			self._add_album(id)
			
