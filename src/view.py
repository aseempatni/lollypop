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

from gi.repository import Gtk, GObject, Gdk
from gettext import gettext as _

from lollypop.database import Database
from lollypop.widgets import *
from lollypop.utils import translate_artist_name

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

	def destroy(self):
		for obj in self._ui.get_objects():
			obj.destroy()
		Gtk.Grid.destroy(self)

class View(Gtk.Grid):
	def __init__(self, db, player, genre_id):
		Gtk.Grid.__init__(self)
		self.set_property("orientation", Gtk.Orientation.VERTICAL)
		self.set_border_width(0)
		self._db = db
		self._player = player
		# Current genre
		self._genre_id = genre_id
		# Current object, used to handle context/content view
		self._object_id = None

		self._player.connect("current-changed", self._current_changed)

	def destroy(self):
		self._player.disconnect_by_func(self._current_changed)
		Gtk.Grid.destroy(self)

	"""
		Current song changed
		If album changed => new context view
		else => update context view
	"""
	def _current_changed(self, widget, track_id):
		update = False
		object_id = self._get_object_id_by_track_id(track_id)
		if object_id != self._object_id:
			update = True
			self._object_id = object_id

		self._update_content(update)
		self._update_context(update)

	"""
		Update content view
		If replace True, create a new content view
	"""
	def _update_content(self, replace):
		pass

	"""
		Update context view
		if replace True, create a new context view
	"""
	def _update_context(self, replace):
		pass

class ArtistView(View):

	"""
		Init ArtistView ui with a scrolled grid of AlbumWidgetSongs
	"""
	def __init__(self, db, player, genre_id, artist_id):
		View.__init__(self, db, player, genre_id)
		self.set_property("orientation", Gtk.Orientation.VERTICAL)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/ArtistView.ui')

		self._object_id = artist_id
		artist_name = self._db.get_artist_name_by_id(artist_id)
		artist_name = translate_artist_name(artist_name)
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

	def destroy(self):
		for obj in self._ui.get_objects():
			obj.destroy()
		View.destroy(self)

	"""
		Populate the view
	"""
	def populate(self):
		if self._genre_id == -1:
			albums = self._db.get_albums_by_artist_id(self._object_id)
		else:
			albums = self._db.get_albums_by_artist_and_genre_ids(self._object_id, self._genre_id)
		for album_id in albums:
			self._populate_content(album_id)

#######################
# PRIVATE             #
#######################

	"""
		Return object id for track_id
	"""
	def _get_object_id_by_track_id(self, track_id):
		album_id = self._db.get_album_id_by_track_id(track_id)
		return self._db.get_artist_id_by_album_id(album_id)

	"""
		Update the content view
		New view if replace True
	"""
	def _update_content(self, replace):
		if replace:
			self._clean_content()
			album_id = self._db.get_album_id_by_track_id(self._player.get_current_track_id())
			self._object_id = self._db.get_artist_id_by_album_id(album_id)
			artist_name = self._db.get_artist_name_by_id(self._object_id)
			self._ui.get_object('artist').set_label(artist_name)
			for album_id in self._db.get_albums_by_artist_id(self._object_id):
				self._populate_content(album_id)
		else:
			for widget in self._albumbox.get_children():
				widget.update_tracks(self._player.get_current_track_id())


	"""
		populate content view with album_id
	"""
	def _populate_content(self, album_id):
		widget = AlbumWidgetSongs(self._db, self._player, album_id)
		widget.connect("new-playlist", self._new_playlist)
		self._albumbox.add(widget)
		widget.show()	

	"""
		Clean content view
	"""
	def _clean_content(self):
		for widget in self._albumbox.get_children():
			widget.hide()
			widget.destroy()

	"""
		Play track with track_id and set a new playlist in player
		arg: GObject, int
	"""
	def _new_playlist(self, obj, track_id):
		self._player.load(track_id)
		if not self._player.is_party():
			album_id = self._db.get_album_id_by_track_id(track_id)
			self._player.set_albums(self._object_id, self._genre_id, track_id)
			self._db.set_more_popular(album_id)

class AlbumView(View):

	"""
		Init album view ui with a scrolled flow box and a scrolled context view
	"""
	def __init__(self, db, player, genre_id):
		View.__init__(self, db, player, genre_id)

		self._albumsongs = None

		self._albumbox = Gtk.FlowBox()
		self._albumbox.set_homogeneous(True)
		self._albumbox.set_selection_mode(Gtk.SelectionMode.NONE)
		self._albumbox.connect("child-activated", self._on_album_activated)
		self._albumbox.set_max_children_per_line(100)
		self._scrolledWindow = Gtk.ScrolledWindow()
		self._scrolledWindow.set_vexpand(True)
		self._scrolledWindow.set_hexpand(True)
		self._scrolledWindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._scrolledWindow.add(self._albumbox)
		self._scrolledWindow.show_all()

		self._scrolledContext = Gtk.ScrolledWindow()
		self._scrolledContext.set_min_content_height(250)
		self._scrolledContext.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._viewport = Gtk.Viewport()
		Gtk.Container.add(self._scrolledContext ,self._viewport)
		separator = Gtk.Separator()
		separator.show()
		
		self.add(self._scrolledWindow)
		self.add(separator)
		self.add(self._scrolledContext)
		self.show()

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

#######################
# PRIVATE             #
#######################

	"""
		Return object id for track_id
	"""
	def _get_object_id_by_track_id(self, track_id):
		return self._db.get_album_id_by_track_id(track_id)

	"""
		Update the context view
		New view if replace True
	"""
	def _update_context(self, replace):
		# If in party mode and context not visible, show it
		if replace or (not self._scrolledContext.is_visible() and self._player.is_party()):
			self._clean_context()
			album_id = self._db.get_album_id_by_track_id(self._player.get_current_track_id())
			self._populate_context(album_id)
		elif self._albumsongs:
			self._albumsongs.update_tracks(self._player.get_current_track_id())

	"""
		populate context view
	"""
	def _populate_context(self, album_id):
		self._albumsongs = AlbumWidgetSongs(self._db, self._player, album_id)
		self._albumsongs.connect("new-playlist", self._new_playlist)
		self._viewport.add(self._albumsongs)
		self._scrolledContext.show_all()

	"""
		Clean context view
	"""
	def _clean_context(self):
		if self._albumsongs:
			self._viewport.remove(self._albumsongs)
			self._albumsongs.destroy()
			self._albumsongs = None
			
	"""
		Show Context view for activated album
	"""
	def _on_album_activated(self, obj, data):
		if self._albumsongs and self._object_id == data.get_child().get_id():
			self._clean_context()
			self._scrolledContext.hide()
		else:
			if self._albumsongs:
				self._clean_context()
			self._object_id = data.get_child().get_id()
			self._populate_context(self._object_id)
			self._scrolledContext.show_all()		
		
	"""
		Add albums with current genre to the flowbox
		arg: int
	"""   
	def _add_albums(self):
		if self._genre_id == -1:
			albums = self._db.get_all_albums()
		else:
			albums = self._db.get_albums_by_genre_id(self._genre_id)
		for album_id in albums:
			widget = AlbumWidget(self._db, album_id)
			widget.show()
			self._albumbox.insert(widget, -1)		

	"""
		Play track with track_id and set a new playlist in player
		arg: GObject, int
	"""
	def _new_playlist(self, obj, track_id):
		self._player.load(track_id)	
		if not self._player.is_party():
			album_id = self._db.get_album_id_by_track_id(track_id)
			self._player.set_albums(None, self._genre_id, track_id)
			self._db.set_more_popular(album_id)
		
