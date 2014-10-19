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

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from lollypop.player import Player, PlaybackStatus
from lollypop.albumart import AlbumArt
from lollypop.database import Database
from lollypop.utils import translate_artist_name

from gettext import gettext as _



class MediaPlayer2Service(dbus.service.Object):
	MEDIA_PLAYER2_IFACE = 'org.mpris.MediaPlayer2'
	MEDIA_PLAYER2_PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player'

	def __init__(self, db, player):
		DBusGMainLoop(set_as_default=True)
		name = dbus.service.BusName('org.mpris.MediaPlayer2.Lollypop', dbus.SessionBus())
		dbus.service.Object.__init__(self, name, '/org/mpris/MediaPlayer2')
		self._db = db
		self._player = player
		self._player.connect('current-changed', self._on_current_changed)
		self._player.connect('playback-status-changed', self._on_playback_status_changed)

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_IFACE)
	def Raise(self):
		self.app.do_activate()

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_IFACE)
	def Quit(self):
		self.app.quit()

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE)
	def Next(self):
		self._player.next()

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE)
	def Previous(self):
		self._player.prev()

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE)
	def Pause(self):
		self._player.pause()

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE)
	def PlayPause(self):
		self._player.play_pause()

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE)
	def Stop(self):
		self._player.stop()

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE)
	def Play(self):
		self._player.play()

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE,
						 in_signature='ox')
	def SetPosition(self, track_id, position):
		pass

	@dbus.service.method(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE,
						 in_signature='s')
	def OpenUri(self, uri):
		pass

	@dbus.service.signal(dbus_interface=MEDIA_PLAYER2_PLAYER_IFACE,
						 signature='x')
	def Seeked(self, position):
		pass

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
						 in_signature='ss', out_signature='v')
	def Get(self, interface_name, property_name):
		return self.GetAll(interface_name)[property_name]

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
						 in_signature='s', out_signature='a{sv}')
	def GetAll(self, interface_name):
		if interface_name == self.MEDIA_PLAYER2_IFACE:
			return {
                'CanQuit': True,
                'CanRaise': True,
                'HasTrackList': False,
                'Identity': 'Lollypop',
                'DesktopEntry': 'lollypop',
                'SupportedUriSchemes': [
                    'file'
                ],
                'SupportedMimeTypes': [
                    'application/ogg',
                    'audio/x-vorbis+ogg',
                    'audio/x-flac',
                    'audio/mpeg'
                ],
			}
		elif interface_name == self.MEDIA_PLAYER2_PLAYER_IFACE:
			return {
                'PlaybackStatus': self._get_playback_status(),
                'LoopStatus': False,
                'Rate': dbus.Double(1.0),
                'Shuffle': True,
                'Metadata': dbus.Dictionary(self._get_metadata(), signature='sv'),
                'Volume': 100.0,
                'Position': 0.0,
                'MinimumRate': dbus.Double(1.0),
                'MaximumRate': dbus.Double(1.0),
                'CanGoNext': self._player.has_next(),
                'CanGoPrevious': self._player.has_previous(),
                'CanPlay': True,
                'CanPause': True,
                'CanSeek': False,
                'CanControl': False,
			}
		else:
			raise dbus.exceptions.DBusException(
				'org.mpris.MediaPlayer2.Lollypop',
				'This object does not implement the %s interface'
				% interface_name)

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
						 in_signature='ssv')
	def Set(self, interface_name, property_name, new_value):
		pass

	@dbus.service.signal(dbus_interface=dbus.PROPERTIES_IFACE,
						 signature='sa{sv}as')
	def PropertiesChanged(self, interface_name, changed_properties,
						  invalidated_properties):
		pass

#######################
# PRIVATE             #
#######################

	def _get_playback_status(self):
		state = self._player.get_playback_status()
		if state == PlaybackStatus.PLAYING:
			return 'Playing'
		elif state == PlaybackStatus.PAUSED:
			return 'Paused'
		else:
			return 'Stopped'

	def _get_loop_status(self):
		return 'Playlist'

	def _get_metadata(self):
		track_id = self._player.get_current_track_id()
		if track_id == -1:
			return {}

		t = self._db.get_track_infos(track_id)
		album_id = t[4]
		album = self._db.get_album_name_by_id(album_id)
		artist = self._db.get_artist_name_by_album_id(album_id)
		artist = translate_artist_name(artist)
		genre_id = self._db.get_album_genre_by_id(album_id)
		genre = self._db.get_genre_name(genre_id)
		album_art = AlbumArt(self._db)
		
		metadata = {
			'mpris:trackid': '/org/mpris/MediaPlayer2/Track/%s' % track_id,
			'xesam:url': t[1]
		}

		metadata['xesam:trackNumber'] = t[3]
		metadata['xesam:title'] = t[0]
		metadata['xesam:album'] = album
		metadata['xesam:artist'] = [artist]
		metadata['xesam:albumArtist'] = [artist]
		metadata['xesam:genre'] = genre
		metadata['mpris:artUrl'] = "file://"+album_art.get_path(album_id)
		
		return metadata



	def _on_current_changed(self, player, data=None):
		self.PropertiesChanged(self.MEDIA_PLAYER2_PLAYER_IFACE,
							   {
									'Metadata': dbus.Dictionary(self._get_metadata(),
																signature='sv'),
									'CanPlay': True,
									'CanPause': True,
								},
								[])

	def _on_playback_status_changed(self, data=None):
		self.PropertiesChanged(self.MEDIA_PLAYER2_PLAYER_IFACE,
							   {
									'PlaybackStatus': self._get_playback_status(),
							   },
							   [])
