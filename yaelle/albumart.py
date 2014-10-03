from gi.repository import Gtk, GObject, GdkPixbuf
from yaelle.database import Database

class AlbumArt: 

	_mimes = [ "jpeg", "jpg", "png", "gif" ]
	ART_SIZE = 128
	CACHE_PATH = os.path.expanduser ("~") +  "/.cache/yaelle"
	
	def __init__(self, sql):
		self._db = Database()
		self._sql = sql

		if not os.path.exists(self.CACHE_PATH):
			try:
				os.mkdir(self.CACHE_PATH)
			except:
				print("Can't create %s" % self.CACHE_PATH)
	
	def get(self, album_id):
		album_path = self._db.get_album_path(self, self._sql, album_id)
		art_path = "%s.jpg" % album_path.replace("/", "_")
		cached = True
		if not os.path.exists(cache_art):
			art_path = self._get_art(album_path)
			cached = False
		try:
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size (art_path, self.ART_SIZE, self.ART_SIZE)
			if not cached:
				pixbuf.save(art_path, "jpeg", {"quality":"90"})
		except:
			return get_default_art()			

	
	def _get_default_art(self):
		# get a small pixbuf with the given path
		icon = Gtk.IconTheme.get_default().load_icon('folder-music-symbolic', max(self.ART_SIZE, self.ART_SIZE) / 4, 0)

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
		return _make_icon_frame(result)

		def _get_art (self, dir):
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

	def _make_icon_frame(pixbuf, path=None):
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

