from gi.repository import Gtk, GObject, Pango

from lollypop.database import Database

class SelectionState:
    NONE = -1
    ALL = 0

class SelectionList(GObject.GObject):

	__gsignals__ = {
		'item-selected': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
	}

	def __init__(self, title, width):
		GObject.GObject.__init__(self)
		
		self._model = Gtk.ListStore(str, int)

		self._view = Gtk.TreeView(self._model)
		self._view.connect('cursor-changed', self._new_item_selected)
		renderer = Gtk.CellRendererText()
		renderer.set_fixed_size(width, -1)
		renderer.set_property('ellipsize-set',True)
		renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
		self._view.append_column(Gtk.TreeViewColumn(title, renderer, text=0))
		self._view.set_headers_visible(False)
		self._view.show()

		self.widget = Gtk.ScrolledWindow()
		self.widget.set_vexpand(True)
		self.widget.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self.widget.add(self._view)
		
		self._genre_id = SelectionState.NONE
		self._artist_id = SelectionState.NONE
		
		
	def populate(self, values):
		self._model.clear()
		for (id, string) in values:
			self._model.append([string, id])
				
		
	
	def _new_item_selected(self, view):
		(path, column) = view.get_cursor()
		if path:
			iter = self._model.get_iter(path)
			if iter:
				self.emit('item-selected', self._model.get_value(iter, 1))

