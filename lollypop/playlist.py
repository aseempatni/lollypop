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

from gi.repository import Gtk, GLib, GdkPixbuf, Pango
from lollypop.albumart import AlbumArt

class PlayListWidget(Gtk.Popover):

	"""
		Init Popover ui with a text entry and a scrolled treeview
	"""
	def __init__(self, db, player):
		Gtk.Popover.__init__(self)
		
		self._db = db
		self._player = player
		self._timeout = None
		self._art = AlbumArt(db)
		self._row_signal = None

		self._model = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int)
		self._view = Gtk.TreeView(self._model)
		self._view.set_property("activate-on-single-click", True)
		self._view.set_property("reorderable", True)
		renderer1 = Gtk.CellRendererText()
		renderer1.set_property('ellipsize-set',True)
		renderer1.set_property('ellipsize', Pango.EllipsizeMode.END)
		renderer2 = Gtk.CellRendererPixbuf()
		renderer2.set_property('stock-size', 16)
		self._view.append_column(Gtk.TreeViewColumn("Pixbuf", renderer2, pixbuf=0))
		self._view.append_column(Gtk.TreeViewColumn("Text", renderer1, text=1))
		self._view.set_headers_visible(False)		

		self.set_property('height-request', 700)
		self.set_property('width-request', 500)
		self._scroll = Gtk.ScrolledWindow()
		self._scroll.set_hexpand(True)
		self._scroll.set_vexpand(True)
		self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._scroll.add(self._view)
		self._scroll.show_all()

		self.connect("closed", self._on_closed)	
		self.add(self._scroll)


	"""
		Show playlist popover		
		Populate treeview with current playlist
	"""
	def show(self):
		self._model.clear()
		for track_id in self._player.get_playlist():
			track_name = self._db.get_track_name(track_id)
			album_id = self._db.get_album_id_by_track_id(track_id)
			artist_id = self._db.get_artist_id_by_album_id(album_id)
			artist_name = self._db.get_artist_name_by_id(artist_id)
			art = self._art.get_small(album_id)
			self._model.append([art, artist_name + " - " + track_name, track_id])
		self._row_signal = self._model.connect("row-deleted", self._reordered_playlist)
		Gtk.Popover.show(self)

#######################
# PRIVATE             #
#######################

	"""
		Clear reorderer signal
	"""
	def _on_closed(self, widget):
		if self._row_signal:
			self._model.disconnect(self._row_signal)
			self._row_signal = None
			
	"""
		Update playlist order after user drag&drop reorder
	"""
	def _reordered_playlist(self, view,  path):
		new_playlist = []
		for row in self._model:
			if row[2]:
				new_playlist.append(row[2])
		self._player.set_playlist(new_playlist)

