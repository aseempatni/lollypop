from gi.repository import Gtk, GLib, GdkPixbuf, Pango
from lollypop.selectionlist import SelectionList

class SearchWidget(Gtk.Popover):
	def __init__(self, db, player):
		Gtk.Popover.__init__(self)
		
		self._db = db
		self._player = player
		self._timeout = None

		grid = Gtk.Grid()
		grid.set_property("orientation", Gtk.Orientation.VERTICAL)

		self._text_entry = Gtk.Entry()
		self._text_entry.connect("changed", self._do_filtering)
		self._text_entry.show()


		#self._model = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int, int)
		self._model = Gtk.ListStore(str, int)
		view = Gtk.TreeView(self._model)
		renderer = Gtk.CellRendererText()
		renderer.set_property('ellipsize-set',True)
		renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
		view.append_column(Gtk.TreeViewColumn("", renderer, text=0))
		view.set_headers_visible(False)
		view.show()		
		
		self.set_property('height-request', 500)
		
		self._scroll = Gtk.ScrolledWindow()
		self._scroll.set_vexpand(True)
		self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._scroll.add(view)
		
		grid.add(self._text_entry)
		grid.add(self._scroll)
		grid.show()
		self.add(grid)
		
		
	def _do_filtering(self, data):
		if self._timeout:
			GLib.source_remove(self._timeout)
		self._timeout = GLib.timeout_add(1000, self._really_do_filtering)
		
	def _really_do_filtering(self):
		self._timeout = None
		searched = self._text_entry.get_text()
		self._model.clear()
		self._scroll.show()
		for artist_id, string in self._db.search_artist(searched):
			self._model.append([string, artist_id])
		
	
