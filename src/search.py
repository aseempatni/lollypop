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
from lollypop.utils import translate_artist_name

class SearchRow(Gtk.ListBoxRow):
	"""
		Init row widgets
	"""
	def __init__(self):
		Gtk.ListBoxRow.__init__(self)
		self._object_id = None
		self._is_track = False
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/SearchRow.ui')
		self._row_widget = self._ui.get_object('row')
		self._artist = self._ui.get_object('artist')
		self._item = self._ui.get_object('item')
		self._cover = self._ui.get_object('cover')
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

	"""
		Set artist label
	"""
	def set_artist(self, name):
		#FIXME
		name = translate_artist_name(name)
		if len(name) > 30:
			name = name[0:30] + "..."
		self._artist.set_text(translate_artist_name(name))

	"""
		Set item label
	"""
	def set_item(self, name):
		#FIXME
		if len(name) > 30:
			name = name[0:30] + "..."
		self._item.set_text(name)

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
		Set as a track
	"""
	def track(self):
		self._is_track = True

	"""
		Return True if it's a track
	"""
	def is_track(self):
		return self._is_track

class SearchWidget(Gtk.Popover):

	"""
		Init Popover ui with a text entry and a scrolled treeview
	"""
	def __init__(self, db, player):
		Gtk.Popover.__init__(self)
		
		self._db = db
		self._player = player
		self._timeout = None
		self._art = AlbumArt(db)

		self.set_property('height-request', 600)
		self.set_property('width-request', 400)

		grid = Gtk.Grid()
		grid.set_property("orientation", Gtk.Orientation.VERTICAL)

		self._text_entry = Gtk.Entry()
		self._text_entry.connect("changed", self._do_filtering)
		self._text_entry.set_hexpand(True)
		self._text_entry.show()

		self._view = Gtk.ListBox()
		self._view.connect("row-activated", self._on_activate)	
		self._view.show()		
		
		self._scroll = Gtk.ScrolledWindow()
		self._scroll.set_vexpand(True)
		self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._scroll.add(self._view)
		
		grid.add(self._text_entry)
		grid.add(self._scroll)
		grid.show()
		self.add(grid)

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
		Timeout filtering, call _really_do_filterting() after a small timeout
	"""	
	def _do_filtering(self, data):
		if self._timeout:
			GLib.source_remove(self._timeout)
		if self._text_entry.get_text() != "":
			self._timeout = GLib.timeout_add(500, self._really_do_filtering)
		else:
			self._clear()

	"""
		Populate treeview searching items in db based on text entry current text
	"""
	def _really_do_filtering(self):
		self._timeout = None
		self._clear()
		searched = self._text_entry.get_text()
		self._scroll.show()

		albums = self._db.search_albums(searched)
		
		for artist_id in self._db.search_artists(searched):
			for album_id in self._db.get_albums_by_artist_id(artist_id):
				if (album_id, artist_id) not in albums:
					albums.append((album_id, artist_id))

		for album_id, artist_id in albums:
			artist_name = self._db.get_artist_name_by_id(artist_id)
			album_name = self._db.get_album_name_by_id(album_id)
			search_row = SearchRow()
			search_row.set_artist(artist_name)
			search_row.set_item(album_name)
			search_row.set_cover(self._art.get_small(album_id))
			search_row.set_object_id(album_id)			
			self._view.add(search_row)

		for track_id, track_name in self._db.search_tracks(searched):
			album_id = self._db.get_album_id_by_track_id(track_id)
			artist_id = self._db.get_artist_id_by_album_id(album_id)
			artist_name = self._db.get_artist_name_by_id(artist_id)
			search_row = SearchRow()
			search_row.set_artist(artist_name)
			search_row.set_item(track_name)
			search_row.set_cover(self._art.get_small(album_id))
			search_row.set_object_id(track_id)
			search_row.track()
			self._view.add(search_row)

		
	"""
		Play searched item when selected
		If item is an album, play first track
	"""
	def _on_activate(self, widget, row):
		value_id = row.get_object_id()
		if row.is_track():
			self._player.load(value_id)
		else:
			self._db.set_more_popular(value_id)
			genre_id = self._db.get_genre_id_by_album_id(value_id)
			# Get first track from album
			track_id = self._db.get_track_ids_by_album_id(value_id)[0]
			artist_id = self._db.get_artist_id_by_album_id(value_id)
			self._player.load(track_id)
			if not self._player.is_party():
				self._db.set_more_popular(value_id)
				self._player.set_albums(artist_id, genre_id, track_id)


