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

from gi.repository import Gtk, Gdk, GObject, GdkPixbuf
import cairo
import os
from math import pi
from lollypop.database import Database

class AlbumArt: 

	_mimes = [ "jpeg", "jpg", "png", "gif" ]
	_ART_SIZE = 200
	_ART_SMALL_SIZE = 32
	CACHE_PATH = os.path.expanduser ("~") +  "/.cache/lollypop"
	
	"""
		Create cache path
	"""	
	def __init__(self, db):
		self._db = db

		if not os.path.exists(self.CACHE_PATH):
			try:
				os.mkdir(self.CACHE_PATH)
			except:
				print("Can't create %s" % self.CACHE_PATH)

	"""
		get cover cache path for album_id
	"""
	def get_path(self, album_id):
		album_path = self._db.get_album_path(album_id)
		return "%s/%s.jpg" % (self.CACHE_PATH, album_path.replace("/", "_"))
	
	"""
		Return pixbuf for album_id
	"""
	def get(self, album_id):
		album_path = self._db.get_album_path(album_id)
		cache_path = "%s/%s.jpg" % (self.CACHE_PATH, album_path.replace("/", "_"))
		cached = True
		try:
			if not os.path.exists(cache_path):
				path = self._get_art(album_path)
				if path:
					pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale (path,
																	  self._ART_SIZE, self._ART_SIZE, False)
					pixbuf.savev(cache_path, "jpeg", ["quality"], ["90"])
				else:
					pixbuf = self._get_default_art()
			else:
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size (cache_path,
																 self._ART_SIZE, self._ART_SIZE)
			return pixbuf
			
		except Exception as e:
			print(e)
			return self._get_default_art()			

	"""
		Return small pixbuf for album_id
	"""
	def get_small(self, album_id):
		album_path = self._db.get_album_path(album_id)
		cache_path = "%s/%s_small.jpg" % (self.CACHE_PATH, album_path.replace("/", "_"))
		cached = True
		try:
			if not os.path.exists(cache_path):
				path = self._get_art_path(album_path)
				if path:
					pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale (self._get_art(album_path), 												  self._ART_SMALL_SIZE,
											  self._ART_SMALL_SIZE, False)
					pixbuf.savev(cache_path, "jpeg", ["quality"], ["90"])
				else:
					pixbuf = None
			else:
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size (cache_path, self._ART_SMALL_SIZE,
											     self._ART_SMALL_SIZE)
			return pixbuf
			
		except Exception as e:
			print(e)
			return None

#######################
# PRIVATE             #
#######################

	"""
		Return pixbuf for default album
	"""
	def _get_default_art(self):
		# get a small pixbuf with the given path
		icon = Gtk.IconTheme.get_default().load_icon('folder-music-symbolic', 
							     max(self._ART_SIZE, self._ART_SIZE) / 4, 0)

		# create an empty pixbuf with the requested size
		result = GdkPixbuf.Pixbuf.new(icon.get_colorspace(),
									  True,
									  icon.get_bits_per_sample(),
									  icon.get_width() * 4,
									  icon.get_height() * 4)
		result.fill(0xffffffff)
		icon.composite(result,
					   icon.get_width() * 3 / 2,
					   icon.get_height() * 3 / 2,
					   icon.get_width(),
					   icon.get_height(),
					   icon.get_width() * 3 / 2,
					   icon.get_height() * 3 / 2,
					   1, 1,
					   GdkPixbuf.InterpType.NEAREST, 0xff)
		return self._make_icon_frame(result)

	"""
		Return path for a cover art in dir
	"""
	def _get_art_path(self, dir):
		try:
			for file in os.listdir (dir):
				lowername = file.lower()
				supported = False
				for mime in self._mimes:
					if lowername.endswith(mime):
						supported = True
						break	
				if (supported):
					return "%s/%s" % (dir, file)

			return None
		except:
		    pass

	"""
		Make an icon frame on pixbuf
	"""
	def _make_icon_frame(self, pixbuf):
		border = 1.5
		degrees = pi / 180
		radius = 3

		w = pixbuf.get_width()
		h = pixbuf.get_height()
		new_pixbuf = pixbuf.scale_simple(w - border * 2,
                                     h - border * 2,
                                     0)

		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
		ctx = cairo.Context(surface)
		ctx.new_sub_path()
		ctx.arc(w - radius, radius, radius - 0.5, -90 * degrees, 0 * degrees)
		ctx.arc(w - radius, h - radius, radius - 0.5, 0 * degrees, 90 * degrees)
		ctx.arc(radius, h - radius, radius - 0.5, 90 * degrees, 180 * degrees)
		ctx.arc(radius, radius, radius - 0.5, 180 * degrees, 270 * degrees)
		ctx.close_path()
		ctx.set_line_width(0.6)
		ctx.set_source_rgb(0.2, 0.2, 0.2)
		ctx.stroke_preserve()
		ctx.set_source_rgb(1, 1, 1)
		ctx.fill()
		border_pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, w, h)

		new_pixbuf.copy_area(border, border,
		                     w - border * 4,
		                     h - border * 4,
		                     border_pixbuf,
		                     border * 2, border * 2)
		return border_pixbuf

