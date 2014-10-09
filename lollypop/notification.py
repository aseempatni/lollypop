# Copyright (c) 2014 Cedric Bellegarde <gnumdk@gmail.com>
# Copyright (c) 2013 Giovanni Campagna <scampa.giovanni@gmail.com>
#
# GNOME Music is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# GNOME Music is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with GNOME Music; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# The GNOME Music authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and GNOME Music.  This permission is above and beyond the permissions
# granted by the GPL license by which GNOME Music is covered.  If you
# modify this code, you may extend this exception to your version of the
# code, but you are not obligated to do so.  If you do not wish to do so,
# delete this exception statement from your version.

from gi.repository import GLib, Gtk, Notify
from gettext import gettext as _

from lollypop.albumart import AlbumArt

class NotificationManager:
	def __init__(self, player, db):
		self._player = player
		self._db = db
		self._art = AlbumArt(db)

		self._notification = Notify.Notification()
		self._notification.set_category('x-gnome.music')
		self._notification.set_hint('action-icons', GLib.Variant('b', True))
		self._notification.set_hint('resident', GLib.Variant('b', True))
		self._notification.set_hint('desktop-entry', GLib.Variant('s', 'lollypop'))

		self._isPlaying = False

		self._player.connect('current-changed', self._update_track)
		self._player.connect('playback-status-changed', self._status_changed)

	def _status_changed(self, obj):
		# this function might be called from one of the action handlers
		# from libnotify, and we can't call _set_actions() from there
		# (we would free the closure we're currently in and corrupt
		# the stack)
		GLib.idle_add(self._update_playing)

	def _update_playing(self):
		is_playing = self._player.is_playing()
		if is_playing:
			self._set_actions(is_playing)

	def _update_track(self, obj, track_id):
		album_id = self._db.get_album_id_by_track_id(track_id)
		album = self._db.get_album_name(album_id)
		artist = self._db.get_artist_name_by_album_id(album_id)
		title = self._db.get_track_name(track_id)
		
		self._notification.set_hint('image-path', GLib.Variant('s', self._art.get_path(album_id)))
		self._notification.update(title,
								  # TRANSLATORS: by refers to the artist, from to the album
								  _("by %s, from %s") % ('<b>' + artist + '</b>',
														 '<i>' + album + '</i>'),
								  'gnome-music')

		self._notification.show()

   
	def _set_actions(self, playing):
		self._notification.clear_actions()

		self._notification.add_action('media-skip-backward', _("Previous"),
									  self._go_previous, None)
		self._notification.add_action('media-skip-forward', _("Next"),
									  self._go_next, None)


	def _go_previous(self, notification, action, data):
		self._player.prev()

	def _go_next(self, notification, action, data):
		self._player.next()
