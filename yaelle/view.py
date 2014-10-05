from gi.repository import Gtk, GObject, Gdk
from gettext import gettext as _

class Loading():
	def __init__(self):
		builder = Gtk.Builder()
		builder.add_from_resource('/org/gnome/Yaelle/Loading.ui')
		self.widget = builder.get_object('container')
		self._label = builder.get_object('label1')
		self._label.set_label(_("Loading please wait..."))	
		self.widget.show_all()

	def set_label(self, str):
		self._label.set_label(str)
