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


class PlayListRow(Gtk.ListBoxRow):
	"""
		Init row widgets
	"""
	def __init__(self):
		Gtk.ListBoxRow.__init__(self)
		self._object_id = None
		self._is_track = False
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/PlayListRow.ui')
		self._row_widget = self._ui.get_object('row')
		self._artist = self._ui.get_object('artist')
		self._title = self._ui.get_object('title')
		self._cover = self._ui.get_object('cover')
		self._button = self._ui.get_object('delete')
		self._button.connect("clicked", self.destroy_callback)
		self.add(self._row_widget)
		self.show()

	
	"""
		Destroy all widgets
	"""
	def destroy(self):
		self.remove(self._row_widget)
		for widget in self._ui.get_objects():
			widget.destroy()
		Gtk.ListBoxRow.destroy(self)
	def destroy_callback(self, event):
		self.destroy()

	"""
		Set artist label
	"""
	def set_artist(self, name):
		self._artist.set_text(translate_artist_name(name))

	"""
		Set title label
	"""
	def set_title(self, name):
		self._title.set_text(name)

	"""
		Show message about how to use playlist
	"""
	def show_help(self):
		self._button.hide()
		self._title.hide()
		self._cover.hide()
		self._artist.set_text(_("Right click on a song to add it to playlist"))
	
	"""
		Set cover pixbuf
	"""
	def set_cover(self, pixbuf):
		self._cover.set_from_pixbuf(pixbuf)

	"""
		Store object id
	"""
	def set_object_id(self, object_id):
		self._object_id = object_id

	"""
		Return object id
	"""
	def get_object_id(self):
		return self._object_id

	"""
		Return True if button is active
	"""
	def is_button_active(self):
		return self._button.get_active()


class PlayListWidget(Gtk.Popover):
	TARGET_ENTRY_LIST = ["application/x-lollypop-widget", Gtk.TargetFlags.SAME_APP, 0 ]

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

		self._view = Gtk.ListBox()
		self._view.connect("row-activated", self._on_activate)	
		self._view.connect("remove", self._on_remove)
		self._view.show()

		self.set_property('width-request', 500)
		self.set_property('height-request', 700)
		self._scroll = Gtk.ScrolledWindow()
		self._scroll.set_hexpand(True)
		self._scroll.set_vexpand(True)
		self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._scroll.add(self._view)
		self._scroll.show_all()

		self.add(self._scroll)

	"""
		Show playlist popover		
		Populate treeview with current playlist
	"""
	def show(self):
		self._clear()
		tracks = self._player.get_playlist()
		if len(tracks) > 0:
			for track_id in tracks:
				track_name = self._db.get_track_name(track_id)
				album_id = self._db.get_album_id_by_track_id(track_id)
				artist_id = self._db.get_artist_id_by_album_id(album_id)
				artist_name = self._db.get_artist_name_by_id(artist_id)
				art = self._art.get_small(album_id)
				playlist_row = PlayListRow()
				playlist_row.set_artist(artist_name)
				playlist_row.set_title(track_name)
				playlist_row.set_cover(self._art.get_small(album_id))
				playlist_row.set_object_id(track_id)
				self._view.add(playlist_row)
		else:
			playlist_row = PlayListRow()
			playlist_row.show_help()
			self._view.add(playlist_row)
		Gtk.Popover.show(self)

#######################
# PRIVATE             #
#######################

	"""
		Clear widget removing every row
	"""
	def _clear(self):
		for child in self._view.get_children():
			child.destroy()

	"""
		Delete item when item have been destroyed
	"""
	def _on_remove(self, container, widget):
		new_playlist = []
		for child in self._view.get_children():
			new_playlist.append(child.get_object_id())
		self._player.set_playlist(new_playlist)

	"""
		Update playlist order after user drag&drop reorder
	"""
	def _reordered_playlist(self, row1 ,row2):
		return
		new_playlist = []
		for row in self._model:
			if row[2]:
				new_playlist.append(row[2])
		self._player.set_playlist(new_playlist)

	"""
		Play clicked item
	"""
	def _on_activate(self, view, row):
		
		value_id = row.get_object_id()
		self._player.del_from_playlist(value_id)
		self._player.load(value_id)
		view.remove(row)
		row.destroy()
