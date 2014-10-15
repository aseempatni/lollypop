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

from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango
from gettext import gettext as _, ngettext 

from lollypop.albumart import AlbumArt
from lollypop.utils import translate_artist_name

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
		self._view.set_property("activate-on-single-click", False)
		self._view.set_property("reorderable", True)
		renderer1 = Gtk.CellRendererText()
		renderer1.set_property('ellipsize-set',True)
		renderer1.set_property('ellipsize', Pango.EllipsizeMode.END)
		renderer2 = Gtk.CellRendererPixbuf()
		renderer2.set_property('stock-size', 16)
		self._view.append_column(Gtk.TreeViewColumn("Pixbuf", renderer2, pixbuf=0))
		self._view.append_column(Gtk.TreeViewColumn("Text", renderer1, text=1))
		self._view.set_headers_visible(False)		
		self._view.connect('row-activated', self._new_item_selected)
		self._view.connect('key-release-event', self._on_keyboard_event)
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
		tracks = self._player.get_playlist()
		if len(tracks) > 0:
			for track_id in tracks:
				track_name = self._db.get_track_name(track_id)
				album_id = self._db.get_album_id_by_track_id(track_id)
				artist_id = self._db.get_artist_id_by_album_id(album_id)
				artist_name = self._db.get_artist_name_by_id(artist_id)
				artist_name = translate_artist_name(artist_name)
				art = self._art.get_small(album_id)
				self._model.append([art, artist_name + " - " + track_name, track_id])
			self._row_signal = self._model.connect("row-deleted", self._reordered_playlist)
		else:
			self._model.append([None, _("Right click on a song to add it to playlist"), None])
		Gtk.Popover.show(self)

#######################
# PRIVATE             #
#######################

	"""
		Delete item if Delete was pressed
	"""
	def _on_keyboard_event(self, obj, event):
		if len(self._player.get_playlist()) > 0:
			if event.keyval == 65535:
				path, column = self._view.get_cursor()
				iter = self._model.get_iter(path)
				self._model.remove(iter)
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

	"""
		Play clicked item
	"""
	def _new_item_selected(self, view, path, column):
		iter = self._model.get_iter(path)
		if iter:
			value_id = self._model.get_value(iter, 2)
			self._player.del_from_playlist(value_id)
			self._player.load(value_id)
		self.hide()
