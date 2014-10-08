#!/usr/bin/python
# Copyright (c) 2014 Cedric Bellegarde <gnome@gmail.com>
#


from gi.repository import Gtk, Gio, GLib, Gdk, Notify
from gettext import gettext as _
from lollypop.window import Window

class Application(Gtk.Application):
	def __init__(self):
		Gtk.Application.__init__(self,
					 application_id='org.gnome.Lollypop',
					 flags=Gio.ApplicationFlags.FLAGS_NONE)
		GLib.set_application_name(_("Lollypop"))
		GLib.set_prgname('lollypop')
		self._window = None

	def build_app_menu(self):
		builder = Gtk.Builder()

		builder.add_from_resource('/org/gnome/Lollypop/app-menu.ui')

		menu = builder.get_object('app-menu')
		self.set_app_menu(menu)

		aboutAction = Gio.SimpleAction.new('about', None)
		aboutAction.connect('activate', self.about)
		self.add_action(aboutAction)

		quitAction = Gio.SimpleAction.new('quit', None)
		quitAction.connect('activate', self.quit)
		self.add_action(quitAction)


	def about(self, action, param):
        	builder = Gtk.Builder()
        	builder.add_from_resource('/org/gnome/Lollypop/AboutDialog.ui')
        	about = builder.get_object('about_dialog')
        	about.set_transient_for(self._window)
        	about.connect("response", self.about_response)
        	about.show()

	def about_response(self, dialog, response):
		dialog.destroy()

	def do_startup(self):
		Gtk.Application.do_startup(self)
		Notify.init(_("Lollypop"))
		self.build_app_menu()

	def quit(self, action=None, param=None):
		self._window.destroy()

	def do_activate(self):
		if not self._window:
			self._window = Window(self)
			#self.service = MediaPlayer2Service(self)
			#self._notifications = NotificationManager(self._window.player)

		self._window.present()

