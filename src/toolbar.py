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

from gettext import gettext as _, ngettext 
from gi.repository import Gtk, GObject, Gdk

from lollypop.albumart import AlbumArt
from lollypop.search import SearchWidget
from lollypop.playlist import PlayListWidget
from lollypop.utils import translate_artist_name

class Toolbar(GObject.GObject):

	"""
		Init toolbar/headerbar ui
	"""
	def __init__(self, db, player):
		GObject.GObject.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Lollypop/headerbar.ui')
		self.header_bar = self._ui.get_object('header-bar')
		self.header_bar.set_custom_title(self._ui.get_object('title-box'))
		self._db = db
		self._player = player
		self._art = AlbumArt(db)
		
		self._prev_btn = self._ui.get_object('previous_button')
		self._play_btn = self._ui.get_object('play_button')
		self._next_btn = self._ui.get_object('next_button')
		self._play_image = self._ui.get_object('play_image')
		self._pause_image = self._ui.get_object('pause_image')

		self._progress = self._ui.get_object('progress_scale')
		self._progress.set_sensitive(False)
		self._time_label = self._ui.get_object('playback')
		self._total_time_label = self._ui.get_object('duration')
		
		self._title_label = self._ui.get_object('title')
		self._artist_label = self._ui.get_object('artist')
		self._cover = self._ui.get_object('cover')
		self._infobox = self._ui.get_object('infobox')	

		self._player.connect("playback-status-changed", self._playback_status_changed)
		self._player.connect("current-changed", self.update_toolbar)
		self._player.set_progress_callback(self._progress_callback)
		
		self._shuffle_btn = self._ui.get_object('shuffle-button')
		self._shuffle_btn.connect("toggled", self._shuffle_update)

		self._party = self._ui.get_object('party-button')
		self._party.connect("toggled", self._party_update)

		self._progress.connect('button-release-event', self._on_progress_scale_button)

		self._prev_btn.connect('clicked', self._on_prev_btn_clicked)
		self._play_btn.connect('clicked', self._on_play_btn_clicked)
		self._next_btn.connect('clicked', self._on_next_btn_clicked)

		search_button = self._ui.get_object('search-button')
		search_button.connect("clicked", self._on_search_btn_clicked)
		self._search = SearchWidget(self._db, self._player)
		self._search.set_relative_to(search_button)

		playlist_button = self._ui.get_object('playlist-button')
		playlist_button.connect("clicked", self._on_playlist_btn_clicked)
		self._playlist = PlayListWidget(self._db, self._player)
		self._playlist.set_relative_to(playlist_button)

		self.header_bar.set_show_close_button(True)

	"""
		Return information eventbox
	"""
	def get_infobox(self):
		return self._infobox

	"""
		Update toolbar items with track_id informations:
			- Cover
			- artist/title
			- reset progress bar
			- update time/total labels
	"""
	def update_toolbar(self, obj, track_id):
		if track_id == None:
			self._cover.hide()
			self._time_label.hide()
			self._total_time_label.hide()
			self._prev_btn.set_sensitive(False)
			self._progress.set_sensitive(False)
			self._play_btn.set_sensitive(False)
			self._next_btn.set_sensitive(False)
			self._title_label.set_text("")
			self._artist_label.set_text("")
		else:
			album_id = self._db.get_album_id_by_track_id(track_id)
			art = self._art.get_small(album_id)
			if art:
				self._cover.set_from_pixbuf(art)
				self._cover.show()
			else:
				self._cover.hide()
			
			title = self._db.get_track_name(track_id)
			artist = self._db.get_artist_name_by_album_id(album_id)
			artist = translate_artist_name(artist)
			self._title_label.set_text(title)
			self._artist_label.set_text(artist)
			self._progress.set_value(0.0)
			duration = self._db.get_track_length(track_id)
			self._progress.set_range(0.0, duration * 60)
			self._total_time_label.set_text(self._player.seconds_to_string(duration))
			self._total_time_label.show()
			self._time_label.set_text("0:00")
			self._time_label.show()

#######################
# PRIVATE             #
#######################
	
	"""
		Callback for progress bar button
		Seek player to scale value
	"""	
	def _on_progress_scale_button(self, scale, data):
		self._player.seek(scale.get_value()/60)
	
	"""
		Update progress bar position and set time label
	"""
	def _progress_callback(self, position):
		self._progress.set_value(position)
		self._time_label.set_text(self._player.seconds_to_string(position/60))
	
	"""
		Update buttons and progress bar
	"""
	def _playback_status_changed(self, obj):
		playing = self._player.is_playing()

		self._progress.set_sensitive(playing)
		if playing:
			self._change_play_btn_status(self._pause_image, _("Pause"))
			self._prev_btn.set_sensitive(True)
			self._play_btn.set_sensitive(True)
			self._next_btn.set_sensitive(True)
		else:
			self._change_play_btn_status(self._play_image, _("Play"))

	"""
		Previous track on prev button clicked
	"""		
	def _on_prev_btn_clicked(self, obj):
		self._player.prev()

	"""
		Play/Pause on play button clicked
	"""		
	def _on_play_btn_clicked(self, obj):
		if self._player.is_playing():
			self._player.pause()
			self._change_play_btn_status(self._play_image, _("Play"))
		else:
			self._player.play()
			self._change_play_btn_status(self._pause_image, _("Pause"))

	"""
		Next track on next button clicked
	"""		
	def _on_next_btn_clicked(self, obj):
		self._player.next()		
	
	"""
		Show search widget on search button clicked
	"""
	def _on_search_btn_clicked(self, obj):
		self._search.show()
		
	"""
		Show playlist widget on playlist button clicked
	"""
	def _on_playlist_btn_clicked(self, obj):
		self._playlist.show()

	"""
		Update play button with image and status as tooltip
	"""
	def _change_play_btn_status(self, image, status):
		self._play_btn.set_image(image)
		self._play_btn.set_tooltip_text(status)

	"""
		Set shuffle mode on if shuffle button active
	"""
	def _shuffle_update(self, obj):
		self._player.set_shuffle(self._shuffle_btn.get_active())

	"""
		Set party mode on if party button active
	"""
	def _party_update(self, obj):
		settings = Gtk.Settings.get_default()
		active = self._party.get_active()
		self._shuffle_btn.set_sensitive(not active)
		settings.set_property("gtk-application-prefer-dark-theme", active)
		self._player.set_party(active)
