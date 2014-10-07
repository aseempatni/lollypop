
from gi.repository import Gtk, Gdk, GLib, GObject, Pango
from gi.repository import GdkPixbuf

from _thread import start_new_thread
from gettext import gettext as _, ngettext        

from yaelle.albumart import AlbumArt

class AlbumWidget(Gtk.Grid):

	def __init__(self, db, album_id):
		Gtk.Grid.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Yaelle/AlbumWidget.ui')
		
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

	def __init__(self, db, album_id):
		Gtk.Grid.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Yaelle/AlbumWidgetSongs.ui')
		
		self._songs = []
		self._db = db
		self._art = AlbumArt(db)
		
		self._ui.get_object('cover').set_from_pixbuf(self._art.get(album_id))
		self._ui.get_object('title').set_label(self._db.get_album_name(album_id))
		self.add(self._ui.get_object('AlbumWidgetSongs'))
		GLib.idle_add(self._add_tracks, album_id)
	

	def _add_tracks(self, album_id):
		tracks = self._db.get_tracks_count_for_album(album_id)
		i = 0
		for (id, name, filepath, length, year) in self._db.get_songs_by_album(album_id):
			ui = Gtk.Builder()
			ui.add_from_resource('/org/gnome/Yaelle/TrackWidget.ui')
			song_widget = ui.get_object('eventbox1')
			self._songs.append(song_widget)
			ui.get_object('num').set_markup('<span color=\'grey\'>%d</span>' % len(self._songs))
			ui.get_object('title').set_text(name)
			ui.get_object('title').set_alignment(0.0, 0.5)
			self._ui.get_object('grid1').attach(
					song_widget,
					int(i / (tracks / 2)),
					int(i % (tracks / 2)), 1, 1)
			song_widget.checkButton = ui.get_object('select')
			song_widget.checkButton.set_visible(False)
			song_widget.show_all()
			i+=1
			
			
			
			
			
			
			
			
			
		
