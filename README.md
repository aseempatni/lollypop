Lollypop 0.5
========================

Lollypop is a new GNOME music playing application.

Is support mp3/4, ogg and flac.

It provides:
- Genre/Cover browsing
- Genre/Artist/Cover browsing
- Search
- Main playlist (called queue in other apps)
- Party mode

Tarball: https://github.com/gnumdk/lollypop-data/raw/master/lollypop-0.5.tar.xz

![Lollypop screenshot](https://github.com/gnumdk/lollypop-data/raw/master/lollypop1.png)
![Lollypop screenshot](https://github.com/gnumdk/lollypop-data/raw/master/lollypop2.png)

TODO:
- Better search/playlist interface
- Extract covers from files (is mutagen able?)
- Add an gsetting option to add more music path

Patchs are welcome ;)


=== Depends on ===
    gtk3
    intltool (make)
    itstool (make)
    python (make)
    python-cairo
    python-dbus
    python-gobject
    python-mutagen



=== Building from git ===

$ git clone https://github.com/gnumdk/lollypop.git

$ cd lollypop

$ ./autogen.sh

$ make

\# make install
