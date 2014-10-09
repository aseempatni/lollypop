from gi.repository import Gtk, GObject, Gdk
from gettext import gettext as _

from lollypop.database import Database
from lollypop.widgets import *

class LoadingView(Gtk.Grid):
	def __init__(self):
		Gtk.Grid.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/Loading.ui')
		self.set_property('halign', Gtk.Align.CENTER)
		self.set_property('valign', Gtk.Align.CENTER)
		self.set_vexpand(True)
		self.set_hexpand(True)
		self._label = self._ui.get_object('label')
		self._label.set_label(_("Loading please wait..."))
		self.add(self._label)
		self.show_all()
		
	def _update_content(self):
		pass
	def _update_context(self):
		pass

class View(Gtk.Grid):
	def __init__(self, db, player, genre_id):
		Gtk.Grid.__init__(self)
		self.set_property("orientation", Gtk.Orientation.VERTICAL)
		self.set_border_width(0)
		self._db = db
		self._player = player
		self._genre_id = genre_id			

class ArtistView(View):
	def __init__(self, db, player, genre_id, artist_id):
		View.__init__(self, db, player, genre_id)
		self.set_property("orientation", Gtk.Orientation.VERTICAL)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/ArtistView.ui')

		self._artist_id = artist_id

		self._player.connect("current-changed", self._update_view)

		artist_name = self._db.get_artist_name_by_id(artist_id)
		self._ui.get_object('artist').set_label(artist_name)

		self._albumbox = Gtk.Grid()
		self._albumbox.set_property("orientation", Gtk.Orientation.VERTICAL)
		self._scrolledWindow = Gtk.ScrolledWindow()
		self._scrolledWindow.set_vexpand(True)
		self._scrolledWindow.set_hexpand(True)
		self._scrolledWindow.set_policy(Gtk.PolicyType.NEVER,
						Gtk.PolicyType.AUTOMATIC)
		self._scrolledWindow.add(self._albumbox)
		self.add(self._ui.get_object('ArtistView'))
		self.add(self._scrolledWindow)
		self.show_all()

	"""
		Update content if in party mode
	"""
	def _update_view(self, widget, track_id):
		if self._player.is_party():
			self.update_content()	    
	"""
    	Add album with album_id to the grid
    	arg: int
    	"""   
	def _add_album(self, album_id):
		widget = AlbumWidgetSongs(self._db, self._player, album_id)
		widget.connect("new-playlist", self._new_playlist)
		self._albumbox.add(widget)
		widget.show()		

	"""
		Play track with track_id and set a new playlist in player
		arg: GObject, int
	"""
	def _new_playlist(self, obj, track_id):
		self._player.load(track_id)
		album_id = self._db.get_album_id_by_track_id(track_id)
		self._db.set_more_popular(album_id)
		self._player.set_albums(self._artist_id, self._genre_id, track_id)

	"""
		Populate the view
	"""
	def populate(self):
		for id in self._db.get_albums_by_artist_and_genre_ids(self._artist_id, self._genre_id):
			self._add_album(id)

	"""
		Update the content view
		We need to clean it first
	"""
	def update_content(self):
		for child in self._albumbox.get_children():
			self._albumbox.remove(child)
			child.hide()
			#child.destroy()
		album_id = self._db.get_album_id_by_track_id(self._player.get_current_track_id())
		self._add_album(album_id)
		artist_id = self._db.get_artist_id_by_album_id(album_id)
		artist_name = self._db.get_artist_name_by_id(artist_id)
		self._ui.get_object('artist').set_label(artist_name)
		for album_id in self._db.get_albums_by_artist_id(artist_id, album_id):
			self._add_album(album_id)

	"""
		Update the context view
		Do nothing here
	"""
	def update_context(self):
		pass


class AlbumView(View):
	def __init__(self, db, player, genre_id):
		View.__init__(self, db, player, genre_id)

		self._context_album_id = None

		self._player.connect("current-changed", self._update_view)

		self._albumbox = Gtk.FlowBox()
		self._albumbox.set_homogeneous(True)
		self._albumbox.set_selection_mode(Gtk.SelectionMode.NONE)
		self._albumbox.connect("child-activated", self._on_album_activated)
		self._scrolledWindow = Gtk.ScrolledWindow()
		self._scrolledWindow.set_vexpand(True)
		self._scrolledWindow.set_hexpand(True)
		self._scrolledWindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._scrolledWindow.add(self._albumbox)
		self._scrolledWindow.show_all()

		self._scrolledContext = Gtk.ScrolledWindow()
		self._scrolledContext.set_min_content_height(250)
		self._scrolledContext.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		
		separator = Gtk.Separator()
		separator.show()
		
		self.add(self._scrolledWindow)
		self.add(separator)
		self.add(self._scrolledContext)
		self.show()
    
	"""
		Update context if in party mode
	"""
	def _update_view(self, widget, track_id):
		if self._player.is_party():
			self.update_context()

	"""
		Show Context view for activated album
	"""
	def _on_album_activated(self, obj, data):
		for child in self._scrolledContext.get_children():
			self._scrolledContext.remove(child)
			child.hide()
			#child.destroy()
		self._context_album_id = data.get_child().get_id()
		context = AlbumWidgetSongs(self._db, self._player, self._context_album_id)
		context.connect("new-playlist", self._new_playlist)
		self._scrolledContext.add(context)
		self._scrolledContext.show_all()		
		
	"""
    		Add albums with current genre to the flowbox
    		arg: int
    	"""   
	def _add_albums(self):
		for album_id in self._db.get_albums_by_genre_id(self._genre_id):
			widget = AlbumWidget(self._db, album_id)
			widget.show()
			self._albumbox.insert(widget, -1)		

	"""
		Play track with track_id and set a new playlist in player
		arg: GObject, int
	"""
	def _new_playlist(self, obj, track_id):
		self._player.load(track_id)
		album_id = self._db.get_album_id_by_track_id(track_id)
		self._player.set_albums(None, self._genre_id, track_id)
		self._db.set_more_popular(album_id)
		self._db.commit()

	"""
		Update the content view
		Do nothing
	"""
	def update_content(self	):
		pass

	"""
		Update the context view
		We need to clean it first
	"""
	def update_context(self):
		for child in self._scrolledContext.get_children():
			self._scrolledContext.remove(child)
			child.hide()
			#child.destroy()
		self._context_album_id = self._db.get_album_id_by_track_id(self._player.get_current_track_id())
		context = AlbumWidgetSongs(self._db, self._player, self._context_album_id)
		context.connect("new-playlist", self._new_playlist)
		self._scrolledContext.add(context)
		self._scrolledContext.show_all()

	"""
		Populate albums
	"""	
	def populate(self):
		GLib.idle_add(self._add_albums)
	
	"""
		Populate albums with popular ones
	"""			
	def populate_popular(self):
		# We are in a thread, can't use global db object
		db = Database()
		for album_id in db.get_albums_popular():
			widget = AlbumWidget(db, album_id)
			widget.show()
			self._albumbox.insert(widget, -1)	
