from gi.repository import Gtk, GLib, GdkPixbuf, Pango
from lollypop.albumart import AlbumArt

class SearchWidget(Gtk.Popover):
	def __init__(self, db, player):
		Gtk.Popover.__init__(self)
		
		self._db = db
		self._player = player
		self._timeout = None
		self._art = AlbumArt(db)

		grid = Gtk.Grid()
		grid.set_property("orientation", Gtk.Orientation.VERTICAL)

		self._text_entry = Gtk.Entry()
		self._text_entry.connect("changed", self._do_filtering)
		self._text_entry.set_hexpand(True)
		self._text_entry.show()


		#self._model = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int, int)
		self._model = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int, bool)
		self._view = Gtk.TreeView(self._model)
		self._view.set_property("activate-on-single-click", True)
		self._view.connect('row-activated', self._new_item_selected)
		renderer1 = Gtk.CellRendererText()
		renderer1.set_property('ellipsize-set',True)
		renderer1.set_property('ellipsize', Pango.EllipsizeMode.END)
		renderer2 = Gtk.CellRendererPixbuf()
		renderer2.set_property('stock-size', 16)
		self._view.append_column(Gtk.TreeViewColumn("Pixbuf", renderer2, pixbuf=0))
		self._view.append_column(Gtk.TreeViewColumn("Text", renderer1, text=1))
		self._view.set_headers_visible(False)
		self._view.show()		
		
		self.set_property('height-request', 500)
		self.set_property('width-request', 350)
		self._scroll = Gtk.ScrolledWindow()
		self._scroll.set_hexpand(True)
		self._scroll.set_vexpand(True)
		self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._scroll.add(self._view)
		
		grid.add(self._text_entry)
		grid.add(self._scroll)
		grid.show()
		self.add(grid)
		
		
	def _do_filtering(self, data):
		if self._timeout:
			GLib.source_remove(self._timeout)
		if self._text_entry.get_text() != "":
			self._timeout = GLib.timeout_add(500, self._really_do_filtering)
		else:
			self._model.clear()
		
	def _really_do_filtering(self):
		self._timeout = None
		searched = self._text_entry.get_text()
		self._model.clear()
		self._scroll.show()
		for album_id, album_name in self._db.search_albums(searched):
			art = self._art.get_small(album_id)
			self._model.append([art, album_name, album_id, False])

		for artist_id, artist_name in self._db.search_artists(searched):
			albums = self._db.get_albums_by_artist_id(artist_id)
			for album_id in albums:
				album_name = self._db.get_album_name(album_id)
				art = self._art.get_small(album_id)
				self._model.append([art, album_name, album_id, False])

		for track_id, track_name in self._db.search_tracks(searched):
			album_id = self._db.get_album_id_by_track_id(track_id)
			art = self._art.get_small(album_id)
			self._model.append([art, track_name, track_id, True])

	def _new_item_selected(self, view, path, column):
		iter = self._model.get_iter(path)
		if iter:
			value_id = self._model.get_value(iter, 2)
			is_track = self._model.get_value(iter, 3)
			if is_track:
				self._player.load(value_id)
			else:
				self._player.load(self._db.get_track_id_by_album_id(value_id)[0])