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

from gi.repository import Gtk, Gdk, GLib, GObject, Pango
from gi.repository import GdkPixbuf

from _thread import start_new_thread
from gettext import gettext as _, ngettext        

from lollypop.albumart import AlbumArt
from lollypop.player import Player

class AlbumWidget(Gtk.Grid):

	def __init__(self, db, album_id):
		Gtk.Grid.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/AlbumWidget.ui')
		
		self._album_id = album_id
		self._db = db
		self._art = AlbumArt(db)
		
		self._ui.get_object('cover').set_from_pixbuf(self._art.get(album_id))
		#TODO Can't find a way to have ellipsized label
		label = self._db.get_album_name(album_id)
		if len(label) > 20:
			label = label[0:20] + "..."
		self._ui.get_object('title').set_label(label)
		label = self._db.get_artist_name_by_album_id(album_id)
		if len(label) > 20:
			label = label[0:20] + "..."
		self._ui.get_object('artist').set_label(label)
		self.add(self._ui.get_object('AlbumWidget'))
		
	def get_id(self):
		return self._album_id

class AlbumWidgetSongs(Gtk.Grid):

	__gsignals__ = {
        'new-playlist': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
    }

	def __init__(self, db, player, album_id):
		Gtk.Grid.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/AlbumWidgetSongs.ui')
		
		self._tracks = []
		self._db = db
		self._player = player
		self._art = AlbumArt(db)
		self.set_vexpand(False)
		self.set_hexpand(False)
		grid = self._ui.get_object('grid2')
		self._nb_tracks = self._db.get_tracks_count_for_album_id(album_id)
		self._player.connect("current-changed", self._update_tracks)
		
		self._ui.get_object('cover').set_from_pixbuf(self._art.get(album_id))
		self._ui.get_object('title').set_label(self._db.get_album_name(album_id))
		self.add(self._ui.get_object('AlbumWidgetSongs'))
		GLib.idle_add(self._add_tracks, album_id)
	

	def _add_tracks(self, album_id):
		i = 0
		for id, name, filepath, length, year in self._db.get_tracks_by_album_id(album_id):
			ui = Gtk.Builder()
			ui.add_from_resource('/org/gnome/Lollypop/TrackWidget.ui')
			track_widget = ui.get_object('eventbox1')
			
			track_widget.playing = ui.get_object('image1')
			track_widget.playing.set_alignment(1, 0.6)
			
			track_widget.connect("button-release-event", self._track_selected)
			self._tracks.append((id, track_widget))
			ui.get_object('num').set_markup('<span color=\'grey\'>%d</span>' % len(self._tracks))
			track_widget.title = ui.get_object('title')
			if not id == self._player.get_current_track_id():
				track_widget.playing.set_no_show_all('True')
				track_widget.title.set_text(name)
			else:
				track_widget.title.set_markup('<b>%s</b>' % name)

			ui.get_object('title').set_alignment(0.0, 0.5)
			self._ui.get_object('grid2').attach(track_widget,
                    					   int(i / (self._nb_tracks / 2)),
                    					   int(i % (self._nb_tracks / 2)), 1, 1
                					   )
			ui.get_object('duration').set_text(self._player.seconds_to_string(length))
			track_widget.show_all()
			i += 1
			
	def _track_selected(self, widget, data):
		for track_id, track_widget in self._tracks:
			if track_widget == widget:
				self.emit("new-playlist", track_id)
			
	def _update_tracks(self, widget, track_id):
		for track_widget_id, track_widget in self._tracks:
			if track_widget_id == track_id:
				track_widget.title.set_markup('<b>%s</b>' % self._db.get_track_name(track_widget_id))
				track_widget.playing.show()
			else:
				if track_widget.playing.is_visible():
					track_widget.playing.hide()
					track_widget.title.set_text(self._db.get_track_name(track_widget_id))
