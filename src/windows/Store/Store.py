"""
Year: 2023

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This programm comes with ABSOLUTELY NO WARRANTY!

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
# Import gtk modules
import gi

from src.backend.DeckManagement.HelperMethods import is_video


gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, GObject, GdkPixbuf

# Import Python modules
from loguru import logger as log
from fuzzywuzzy import fuzz
import webbrowser as web
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.windows.mainWindow.mainWindow import MainWindow

# Import globals
import globals as gl

# Import own modules
from src.backend.DeckManagement.ImageHelpers import image2pixbuf
from src.windows.Store.Backend import StoreBackend

class Store(Gtk.ApplicationWindow):
    def __init__(self, main_window: "MainWindow", *args, **kwargs):
        super().__init__(
            title="Store",
            default_width=1050,
            default_height=750,
            transient_for=main_window,
            *args, **kwargs
            )
        self.main_window = main_window

        self.backend = StoreBackend()

        self.build()

    def build(self):
        # Header bar
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)

        self.main_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT, hexpand=True, vexpand=True)
        self.main_box.append(self.main_stack)

        # Header stack switcher
        self.stack_switcher = Gtk.StackSwitcher(stack=self.main_stack)
        self.header.set_title_widget(self.stack_switcher)

        self.plugin_page = PluginPage(store=self)
        self.icon_page = IconPage(store=self)
        self.wallpaper_page = WallpaperPage(store=self)

        self.main_stack.add_titled(self.plugin_page, "Plugins", "Plugins")
        self.main_stack.add_titled(self.icon_page, "Icons", "Icons")
        self.main_stack.add_titled(self.wallpaper_page, "Wallpapers", "Wallpapers")


class StorePage(Gtk.Box):
    def __init__(self, store: Store):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_margin_start(15)
        self.set_margin_end(15)
        self.set_margin_top(15)
        self.set_margin_bottom(15)

        self.store = store

        self.build()

    def build(self):
        self.nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        self.append(self.nav_box)

        self.search_entry = Gtk.SearchEntry(placeholder_text="Search", hexpand=True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.nav_box.append(self.search_entry)

        self.scrolled_window = Gtk.ScrolledWindow(hexpand=True)
        self.append(self.scrolled_window)

        self.scrolled_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        self.scrolled_window.set_child(self.scrolled_box)

        self.flow_box = Gtk.FlowBox(orientation=Gtk.Orientation.HORIZONTAL)
        self.scrolled_box.append(self.flow_box)

        # Add vexpand box to the bottom to avoid unwanted stretching of the flowbox children
        self.scrolled_box.append(Gtk.Box(hexpand=True, vexpand=True))

    def on_search_changed(self, entry: Gtk.SearchEntry):
        pass

class PluginPage(StorePage):
    def __init__(self, store: Store):
        super().__init__(store=store)
        self.search_entry.set_placeholder_text("Search for plugins")

        self.load()

    def load(self):
        plugins = self.store.backend.get_all_plugins()
        for plugin in plugins:
            self.flow_box.append(PluginPreview(plugin_page=self, plugin_dict=plugin))

class PluginPreview(Gtk.FlowBoxChild):
    def __init__(self, plugin_page: PluginPage, plugin_dict: dict):
        super().__init__()
        self.plugin_dict = plugin_dict

        self.build()

    def build(self):
        self.overlay = Gtk.Overlay()
        self.set_child(self.overlay)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                 hexpand=True, vexpand=False,
                                 css_classes=["no-padding"],
                                 width_request=250, height_request=250)
        self.set_child(self.main_box)

        self.main_button = Gtk.Button(hexpand=True, vexpand=False,
                                      width_request=250, height_request=200,
                                      css_classes=["no-padding", "no-round-bottom"])
        self.main_box.append(self.main_button)
        
        self.main_button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                       hexpand=True, vexpand=False)
        self.main_button.set_child(self.main_button_box)
        
        self.image = Gtk.Picture(hexpand=True,
                                 content_fit=Gtk.ContentFit.COVER,
                                 height_request=90, width_request=250,
                                 css_classes=["plugin-store-image"])
        pil_image = self.plugin_dict["image"]
        pil_image.thumbnail((250, 90))
        self.image.set_pixbuf(image2pixbuf(pil_image, force_transparency=True))
        self.main_button_box.append(self.image)

        self.label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                 margin_start=6, margin_top=6)
        self.main_button_box.append(self.label_box)

        self.name_label = Gtk.Label(label=self.plugin_dict["name"],
                                    css_classes=["bold"],
                                    xalign=0)
        self.label_box.append(self.name_label)

        self.author_label = Gtk.Label(label=f"By {self.plugin_dict['user_name']}",
                                      sensitive=False, #Grey out
                                      xalign=0)
        self.label_box.append(self.author_label)

        self.batch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                 hexpand=False, vexpand=False,
                                 margin_start=7, margin_top=15, margin_bottom=15)
        # self.overlay.add_overlay(self.batch_box)
        self.main_button_box.append(self.batch_box)

        if self.plugin_dict["official"]:
            self.batch_box.append(OfficialBatch(margin_end=7))
        
        if self.plugin_dict["commit_sha"] is not None:
            self.batch_box.append(VerifiedBatch())

        self.main_button_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                  hexpand=True)
        self.main_box.append(self.button_box)

        self.github_button = Gtk.Button(icon_name="github-symbolic",
                                        hexpand=True,
                                        css_classes=["no-round-top-left", "no-round-top-right", "no-round-bottom-right"])
        self.github_button.connect("clicked", self.on_github_clicked)
        self.button_box.append(self.github_button)

        self.button_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self.download_button = Gtk.Button(icon_name="download-symbolic",
                                          hexpand=True,
                                          css_classes=["no-round-top-left", "no-round-top-right", "no-round-bottom-left"])
        self.download_button.connect("clicked", self.on_download_clicked)
        self.button_box.append(self.download_button)


    def on_github_clicked(self, button: Gtk.Button):
        web.open(self.plugin_dict["url"])

    def on_download_clicked(self, button: Gtk.Button):
        self.install()

    def install(self):
        pass

class OfficialBatch(Gtk.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(label="Official", *args, **kwargs)

class VerifiedBatch(Gtk.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(label="Verified", *args, **kwargs)



class IconPage(StorePage):
    def __init__(self, store: Store):
        super().__init__(store=store)
        self.search_entry.set_placeholder_text("Search for icons")

class WallpaperPage(StorePage):
    def __init__(self, store: Store):
        super().__init__(store=store)
        self.search_entry.set_placeholder_text("Search for wallpapers")