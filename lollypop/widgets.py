
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
		
		self._songs = []
		self._db = db
		self._player = player
		self._art = AlbumArt(db)
		self.set_vexpand(False)
		self.set_hexpand(False)
		flowbox = self._ui.get_object('flow')
		nb_tracks = self._db.get_tracks_count_for_album(album_id)
		flowbox.set_property("min-children-per-line", nb_tracks/2)
		flowbox.set_property("max-children-per-line", nb_tracks/2)
		flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
		self._player.connect("current-changed", self._update_tracks)
		
		self._ui.get_object('cover').set_from_pixbuf(self._art.get(album_id))
		self._ui.get_object('title').set_label(self._db.get_album_name(album_id))
		self.add(self._ui.get_object('AlbumWidgetSongs'))
		GLib.idle_add(self._add_tracks, album_id)
	

	def _add_tracks(self, album_id):
		for (id, name, filepath, length, year) in self._db.get_songs_by_album(album_id):
			ui = Gtk.Builder()
			ui.add_from_resource('/org/gnome/Lollypop/TrackWidget.ui')
			song_widget = ui.get_object('eventbox1')
			
			song_widget.playing = ui.get_object('image1')
			song_widget.playing.set_alignment(1, 0.6)
			
			song_widget.connect("button-release-event", self._track_selected)
			self._songs.append((id, song_widget))
			ui.get_object('num').set_markup('<span color=\'grey\'>%d</span>' % len(self._songs))
			song_widget.title = ui.get_object('title')
			if not id == self._player.current_song:
				song_widget.playing.set_no_show_all('True')
				song_widget.title.set_text(name)
			else:
				song_widget.title.set_markup('<b>%s</b>' % name)

			ui.get_object('title').set_alignment(0.0, 0.5)
			self._ui.get_object('flow').insert(song_widget, -1)
			song_widget.checkButton = ui.get_object('select')
			song_widget.checkButton.set_visible(False)
			song_widget.show_all()
			
	def _track_selected(self, widget, data):
		for id, song_widget in self._songs:
			if song_widget == widget:
				self.emit("new-playlist", id)
			
	def _update_tracks(self, widget, song_id):
		for id, song_widget in self._songs:
			if id == song_id:
				song_widget.title.set_markup('<b>%s</b>' % self._db.get_song_name(id))
				song_widget.playing.show()
			else:
				if song_widget.playing.is_visible():
					song_widget.playing.hide()
					song_widget.title.set_text(self._db.get_song_name(id))
