#!/usr/bin/python
# Copyright (c) 2014 Cedric Bellegarde <gnumdk@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# Many code inspiration from gnome-music at the GNOME project

from gi.repository import Gtk, GObject, Pango

from lollypop.database import Database

class SelectionList(GObject.GObject):

	__gsignals__ = {
		'item-selected': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
	}

	"""
		Init Selection list ui
	"""
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
	
	"""
		Populate view with values
	"""	
	def populate(self, values):
		self._model.clear()
		for (id, string) in values:
			self._model.append([string, id])
				
		
#######################
# PRIVATE             #
#######################

	"""
		Forward "cursor-changed" as "item-selected" with item id as arg
	"""	
	def _new_item_selected(self, view):
		(path, column) = view.get_cursor()
		if path:
			iter = self._model.get_iter(path)
			if iter:
				self.emit('item-selected', self._model.get_value(iter, 1))

