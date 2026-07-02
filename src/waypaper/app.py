"""Module that runs GUI app"""

import json
import threading
import subprocess
import os
import gi
from pathlib import Path

from waypaper.changer import change_wallpaper
from waypaper.config import Config
from waypaper import wallhaven
from waypaper.options import FILL_OPTIONS, SORT_OPTIONS, SORT_DISPLAYS, VIDEO_EXTENSIONS, SWWW_TRANSITION_TYPES, \
    get_monitor_options, LINUX_WALLPAPERENGINE_FILL_OPTIONS, LINUX_WALLPAPERENGINE_CLAMP
from waypaper.translations import Chinese, English, French, German, Polish, Russian, Belarusian, Spanish
from waypaper.keybindings import Keys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib


class App(Gtk.Window):
    """Main application class that controls GUI"""

    def __init__(self, txt: Chinese|English|French|German|Polish|Russian|Belarusian|Spanish, cf: Config) -> None:
        super().__init__(title="Waypaper")
        self.cf = cf
        self.txt = txt
        self.keys = Keys(cf)
        self.check_backends()
        self.set_default_size(820, 600)
        self.connect("delete-event", Gtk.main_quit)
        self.selected_index = 0
        self.filtered_indices = []
        self.status_filter = "all"
        self.highlighted_image_row = 0
        self.is_enering_text = False
        self.number_of_resize = 0

        self.wallhaven_items: list = []
        self.thumbnails: list = []
        self.image_paths: list = []
        self.image_names: list = []
        self.current_page: int = 1
        self.last_page: int = 1
        self.total_results: int = 0
        self._search_timer = None

        self.init_ui()
        self.main_box.grab_focus()
        self.keys.fill_keys_from_file(self.cf.keybindings_file)

        # Start the image processing in a separate thread:
        threading.Thread(target=self.fetch_wallhaven_gallery).start()


    def init_ui(self) -> None:
        """Initialize the UI elements of the application"""

        # Create a vertical box for general app layout:
        self.main_box = Gtk.VBox(spacing=10)
        self.add(self.main_box)

        # Load and apply CSS
        css_provider = Gtk.CssProvider()
        css = b"""
        .highlighted-button {
            border: 1px solid @theme_selected_bg_color;
        }
        """
        try:
            with open(self.cf.style_file, 'rb') as stylesheet:
                css = css + stylesheet.read()
        except OSError:
            pass
        css_provider.load_from_data(css)

        # Apply CSS to the default screen
        screen = Gdk.Screen.get_default()
        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # TOP MENU

        # Create a box to contain the top row of items:
        self.top_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=60)
        self.top_button_box.set_margin_top(20)
        self.main_box.pack_start(self.top_button_box, False, False, 0)

        # Create alignment container for top menu:
        self.top_row_alignment = Gtk.Alignment(xalign=0.5, yalign=0.0, xscale=0.5, yscale=0.5)
        self.top_button_box.pack_start(self.top_row_alignment, True, False, 0)

        # Create a button to open folder dialog (hidden in API mode):
        self.choose_folder_button = Gtk.Button(label=self.txt.msg_changefolder)
        self.choose_folder_button.connect("clicked", self.on_choose_folder_clicked)
        self.choose_folder_button.set_visible(False)

        # Create a search entry:
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text(self.txt.msg_search)
        self.search_entry.connect("changed", self.on_search_entry_changed)
        self.search_entry.get_style_context().add_class("search-entry")
        self.search_entry.connect("focus-in-event", self.on_focus_in)
        self.search_entry.connect("focus-out-event", self.on_focus_out)

        # Create a clear button:
        self.clear_button = Gtk.Button(label=self.txt.msg_clear)
        self.clear_button.connect("clicked", self.on_clear_button)

        # Create the options menu button:
        self.options_button = Gtk.Button(label=self.txt.msg_options)
        self.options_button.connect("clicked", self.on_options_button_clicked)

        # Create a sort option dropdown menu:
        self.sort_combo = Gtk.ComboBoxText()
        for option in SORT_OPTIONS:
            self.sort_combo.append_text(SORT_DISPLAYS[option])
        active_num = SORT_OPTIONS.index(self.cf.sort_option)
        self.sort_combo.set_active(active_num)
        self.sort_combo.connect("changed", self.on_sort_option_changed)
        self.sort_combo.set_tooltip_text(self.txt.tip_sorting)

        # Wallhaven category selector:
        self.wh_label = Gtk.Label(label="Wallhaven:")
        self.wh_label.get_style_context().add_class("wh-label")
        self.wh_combo = Gtk.ComboBoxText()
        self.wh_presets = ["random", "anime", "manga", "sketch", "general"]
        self.wh_labels = ["Random", "Anime", "Manga", "Sketch", "General"]
        for label in self.wh_labels:
            self.wh_combo.append_text(label)
        self.wh_combo.set_active(0)
        self.wh_combo.set_tooltip_text("Wallhaven category to download on refresh")

        # Create save to library button:
        self.save_button = Gtk.Button(label="♥ Save")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.save_button.set_tooltip_text("Save selected wallpaper permanently to library (y)")

        # Create refresh button:
        self.refresh_button = Gtk.Button(label=self.txt.msg_refresh)
        self.refresh_button.connect("clicked", self.on_refresh_clicked)
        self.refresh_button.set_tooltip_text(self.txt.tip_refresh + " (descarga nuevos de Wallhaven)")

        # Create random button:
        self.random_button = Gtk.Button(label=self.txt.msg_random)
        self.random_button.connect("clicked", self.on_random_clicked)
        self.random_button.set_tooltip_text(self.txt.tip_random)

        # Create exit button:
        self.exit_button = Gtk.Button(label=self.txt.msg_exit)
        self.exit_button.connect("clicked", self.on_exit_clicked)
        self.exit_button.set_tooltip_text(self.txt.tip_exit)

        # Group 1: Files (folder, search, sort)
        self.files_box = Gtk.Box(spacing=4)
        self.files_box.get_style_context().add_class("action-group")
        self.files_box.pack_start(self.choose_folder_button, False, False, 0)
        self.files_box.pack_start(self.search_entry, expand=False, fill=False, padding=0)
        self.files_box.pack_start(self.clear_button, expand=False, fill=False, padding=0)
        self.files_box.pack_start(self.sort_combo, expand=False, fill=False, padding=0)

        # Group 2: Wallhaven (category + refresh)
        self.wh_box = Gtk.Box(spacing=4)
        self.wh_box.get_style_context().add_class("action-group")
        self.wh_box.pack_start(self.wh_label, expand=False, fill=False, padding=0)
        self.wh_box.pack_start(self.wh_combo, expand=False, fill=False, padding=0)
        self.wh_box.pack_start(self.refresh_button, expand=False, fill=False, padding=0)

        # Group 3: Actions (save, random, options, exit)
        self.actions_box = Gtk.Box(spacing=4)
        self.actions_box.get_style_context().add_class("action-group")
        self.actions_box.pack_start(self.save_button, expand=False, fill=False, padding=0)
        self.actions_box.pack_start(self.random_button, expand=False, fill=False, padding=0)
        self.actions_box.pack_start(self.options_button, expand=False, fill=False, padding=0)
        self.actions_box.pack_start(self.exit_button, expand=False, fill=False, padding=0)

        # Separators between groups
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)

        # Add all groups to the top container:
        self.top_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.top_container.get_style_context().add_class("top-bar")
        self.top_container.pack_start(self.files_box, False, False, 0)
        self.top_container.pack_start(sep1, False, False, 8)
        self.top_container.pack_start(self.wh_box, False, False, 0)
        self.top_container.pack_start(sep2, False, False, 8)
        self.top_container.pack_start(self.actions_box, False, False, 0)
        self.top_row_alignment.add(self.top_container)

        # STATUS FILTER BAR
        self.filter_box = Gtk.Box(spacing=4)
        self.filter_box.set_margin_top(4)
        self.filter_box.set_margin_bottom(2)
        self.filter_box.set_halign(Gtk.Align.CENTER)

        self.filter_buttons = {}
        for key, label in [("all", "All"), ("kept", "♥ Kept"), ("discarded", "✕ Discarded"), ("unreviewed", "◇ New")]:
            btn = Gtk.ToggleButton(label=label)
            btn.set_active(key == self.status_filter)
            btn.get_style_context().add_class("filter-btn")
            btn.connect("toggled", self.on_status_filter_toggled, key)
            self.filter_buttons[key] = btn
            self.filter_box.pack_start(btn, False, False, 0)

        self.main_box.pack_start(self.filter_box, False, False, 0)

        # PAGINATION BAR
        self.pagination_box = Gtk.Box(spacing=8)
        self.pagination_box.set_margin_top(2)
        self.pagination_box.set_margin_bottom(4)
        self.pagination_box.set_halign(Gtk.Align.CENTER)
        self.prev_page_button = Gtk.Button(label="← Prev")
        self.prev_page_button.get_style_context().add_class("filter-btn")
        self.prev_page_button.connect("clicked", self.on_prev_page)
        self.page_label = Gtk.Label(label="Page 1 / 1")
        self.page_label.get_style_context().add_class("status-label")
        self.next_page_button = Gtk.Button(label="Next →")
        self.next_page_button.get_style_context().add_class("filter-btn")
        self.next_page_button.connect("clicked", self.on_next_page)
        self.pagination_box.pack_start(self.prev_page_button, False, False, 0)
        self.pagination_box.pack_start(self.page_label, False, False, 4)
        self.pagination_box.pack_start(self.next_page_button, False, False, 0)
        self.main_box.pack_start(self.pagination_box, False, False, 0)

        # MIDDLE GRID

        # Create a scrolled window for the grid of images:
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # Create a box to center the grid:
        self.center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.center_box.set_valign(Gtk.Align.CENTER)
        self.center_box.set_halign(Gtk.Align.CENTER)
        self.main_box.add(self.scrolled_window)

        # Create a grid layout for images:
        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(8)
        self.grid.set_column_spacing(8)
        self.center_box.add(self.grid)
        self.center_box.get_style_context().add_class("grid-container")
        self.scrolled_window.add(self.center_box)

        # BACKEND MENU

        # Create a backend dropdown menu:
        self.backend_option_combo = Gtk.ComboBoxText()
        for backend in self.cf.installed_backends:
            self.backend_option_combo.append_text(backend)

        # Set as active line the backend from config, if it is installed:
        active_num = 0
        if self.cf.backend in self.cf.installed_backends:
            active_num = self.cf.installed_backends.index(self.cf.backend)
        self.backend_option_combo.set_active(active_num)
        self.backend_option_combo.connect("changed", self.on_backend_option_changed)
        self.backend_option_combo.set_tooltip_text(self.txt.tip_backend)

        self.create_fill_option_combo()

        # Create a color picker:
        self.color_picker_button = Gtk.ColorButton()
        self.color_picker_button.set_use_alpha(True)
        rgba_color = Gdk.RGBA()
        rgba_color.parse(self.cf.color)
        self.color_picker_button.set_rgba(rgba_color)
        self.color_picker_button.connect("color-set", self.on_color_set)
        self.color_picker_button.set_tooltip_text(self.txt.tip_color)

        # Create mpv stop button:
        self.mpv_stop_button = Gtk.Button(label=self.txt.msg_stop)
        self.mpv_stop_button.connect("clicked", self.on_mpv_stop_button_clicked)
        self.mpv_stop_button.set_tooltip_text(self.txt.tip_mpv_stop)

        # Create mpv pause button:
        self.mpv_pause_button = Gtk.Button(label=self.txt.msg_pause)
        self.mpv_pause_button.connect("clicked", self.on_mpv_pause_button_clicked)
        self.mpv_pause_button.set_tooltip_text(self.txt.tip_mpv_pause)

        # Create mpv sound toggle:
        self.mpv_sound_toggle = Gtk.ToggleButton(label=self.txt.msg_sound)
        self.mpv_sound_toggle.set_active(self.cf.mpvpaper_sound)
        self.mpv_sound_toggle.connect("toggled", self.on_mpv_sound_toggled)
        self.mpv_sound_toggle.set_tooltip_text(self.txt.tip_mpv_sound)

        # Hyprpaper restast button:
        self.hyprpaper_restart = Gtk.Button(label=self.txt.msg_hyprpaper_restart)
        self.hyprpaper_restart.connect("clicked", self.on_hyprland_restart)
        self.hyprpaper_restart.set_tooltip_text(self.txt.tip_hyprpaper_restart)

        # Create a box to contain the bottom row of buttons:
        self.bottom_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=60)
        self.bottom_button_box.set_margin_bottom(15)
        self.main_box.pack_end(self.bottom_button_box, False, False, 0)

        # Create a box to contain the loading label:
        self.bottom_loading_box = Gtk.HBox(spacing=0)
        self.bottom_loading_box.set_margin_bottom(0)
        self.main_box.pack_end(self.bottom_loading_box, False, False, 0)

        # Status bar for stats (always visible at bottom)
        self.status_bar = Gtk.Box(spacing=4)
        self.status_bar.set_margin_bottom(2)
        self.status_bar.set_margin_top(2)
        self.status_bar.set_halign(Gtk.Align.CENTER)
        self.status_label = Gtk.Label(label="")
        self.status_label.set_opacity(0.7)
        self.status_label.get_style_context().add_class("status-label")
        self.status_bar.pack_start(self.status_label, False, False, 0)
        self.main_box.pack_end(self.status_bar, False, False, 0)

        # Create alignment container for bottom menu:
        self.button_row_alignment = Gtk.Alignment(xalign=0.5, yalign=0.0, xscale=0.5, yscale=0.5)
        self.bottom_button_box.pack_start(self.button_row_alignment, True, False, 0)

        # Create a monitor option dropdown menu:
        self.monitor_option_combo = Gtk.ComboBoxText()

        # Create a horizontal box for display backend options:
        self.options_box = Gtk.HBox(spacing=10)
        self.options_box.pack_start(self.backend_option_combo, False, False, 0)
        self.button_row_alignment.add(self.options_box)

        # Create a transition type dropdown menu for swww
        self.swww_transitions_options = Gtk.ComboBoxText()

        #  Get angle for animation
        self.swww_angle_entry = Gtk.Entry()
        self.swww_angle_entry.set_width_chars(5)
        self.swww_angle_entry.set_placeholder_text("angle")
        self.swww_angle_entry.connect("focus-in-event", self.on_focus_in)
        self.swww_angle_entry.connect("focus-out-event", self.on_focus_out)

        #  Get steps for animation
        self.swww_steps_entry = Gtk.Entry()
        self.swww_steps_entry.set_width_chars(5)
        self.swww_steps_entry.set_placeholder_text("steps")
        self.swww_steps_entry.connect("focus-in-event", self.on_focus_in)
        self.swww_steps_entry.connect("focus-out-event", self.on_focus_out)

        #  Get duration for animation
        self.swww_duration_entry = Gtk.Entry()
        self.swww_duration_entry.set_width_chars(7)
        self.swww_duration_entry.set_placeholder_text("duration")
        self.swww_duration_entry.connect("focus-in-event", self.on_focus_in)
        self.swww_duration_entry.connect("focus-out-event", self.on_focus_out)

        #  Get fps for animation
        self.swww_fps_entry = Gtk.Entry()
        self.swww_fps_entry.set_width_chars(5)
        self.swww_fps_entry.set_placeholder_text("fps")
        self.swww_fps_entry.connect("focus-in-event", self.on_focus_in)
        self.swww_fps_entry.connect("focus-out-event", self.on_focus_out)

        # Volume for linux-wallpaperengine
        self.linux_wallpaperengine_volume_entry = Gtk.Entry()
        self.linux_wallpaperengine_volume_entry.set_width_chars(6)
        self.linux_wallpaperengine_volume_entry.set_placeholder_text("volume")
        self.linux_wallpaperengine_volume_entry.connect("focus-in-event", self.on_focus_in)
        self.linux_wallpaperengine_volume_entry.connect("focus-out-event", self.on_focus_out)

        # fps for linux-wallpaperengine
        self.linux_wallpaperengine_fps_entry = Gtk.Entry()
        self.linux_wallpaperengine_fps_entry.set_width_chars(3)
        self.linux_wallpaperengine_fps_entry.set_placeholder_text("fps")
        self.linux_wallpaperengine_fps_entry.connect("focus-in-event", self.on_focus_in)
        self.linux_wallpaperengine_fps_entry.connect("focus-out-event", self.on_focus_out)

        # sound settings linux-wallpaperengine
        self.linux_wallpaperengine_sound_menu = Gtk.Menu()

        self.linux_wallpaperengine_silent_checkbox = Gtk.CheckMenuItem(label="silent")
        self.linux_wallpaperengine_silent_checkbox.set_active(self.cf.linux_wallpaperengine_silent)
        self.linux_wallpaperengine_silent_checkbox.connect("toggled", self.on_linux_wallpaperengine_silent_toggled)
        self.linux_wallpaperengine_sound_menu.append(self.linux_wallpaperengine_silent_checkbox)

        self.linux_wallpaperengine_noautomute_checkbox = Gtk.CheckMenuItem(label="noautomute")
        self.linux_wallpaperengine_noautomute_checkbox.set_active(self.cf.linux_wallpaperengine_noautomute)
        self.linux_wallpaperengine_noautomute_checkbox.connect("toggled", self.on_linux_wallpaperengine_noautomnute_toggled)
        self.linux_wallpaperengine_sound_menu.append(self.linux_wallpaperengine_noautomute_checkbox)

        self.linux_wallpaperengine_no_audio_processing_checkbox = Gtk.CheckMenuItem(label="no-audio-processing")
        self.linux_wallpaperengine_no_audio_processing_checkbox.set_active(self.cf.linux_wallpaperengine_no_audio_processing)
        self.linux_wallpaperengine_no_audio_processing_checkbox.connect("toggled", self.on_linux_wallpaperengine_no_audio_processing_toggled)
        self.linux_wallpaperengine_sound_menu.append(self.linux_wallpaperengine_no_audio_processing_checkbox)

        self.linux_wallpaperengine_sound_menu.show_all()
        self.linux_wallpaperengine_sound_menu_button = Gtk.Button(label="Sound")
        self.linux_wallpaperengine_sound_menu_button.connect("clicked", self.on_linux_wallpaperengine_sound_menu_button_clicked)

        # wallpaper configuration options
        self.linux_wallpaperengine_config_menu = Gtk.Menu()

        self.linux_wallpaperengine_disable_particles_checkbox = Gtk.CheckMenuItem(label="disable-particles")
        self.linux_wallpaperengine_disable_particles_checkbox.set_active(self.cf.linux_wallpaperengine_disable_particles)
        self.linux_wallpaperengine_disable_particles_checkbox.connect("toggled", self.on_linux_wallpaperengine_disable_particles_toggled)
        self.linux_wallpaperengine_config_menu.append(self.linux_wallpaperengine_disable_particles_checkbox)

        self.linux_wallpaperengine_disable_mouse_checkbox = Gtk.CheckMenuItem(label="disable-mouse")
        self.linux_wallpaperengine_disable_mouse_checkbox.set_active(self.cf.linux_wallpaperengine_disable_mouse)
        self.linux_wallpaperengine_disable_mouse_checkbox.connect("toggled", self.on_linux_wallpaperengine_disable_mouse_toggled)
        self.linux_wallpaperengine_config_menu.append(self.linux_wallpaperengine_disable_mouse_checkbox)

        self.linux_wallpaperengine_disable_pararllax_checkbox = Gtk.CheckMenuItem(label="disable-parallax")
        self.linux_wallpaperengine_disable_pararllax_checkbox.set_active(self.cf.linux_wallpaperengine_disable_parallax)
        self.linux_wallpaperengine_disable_pararllax_checkbox.connect("toggled", self.on_linux_wallpaperengine_disable_parallax_toggled)
        self.linux_wallpaperengine_config_menu.append(self.linux_wallpaperengine_disable_pararllax_checkbox)

        self.linux_wallpaperengine_config_menu.show_all()
        self.linux_wallpaperengine_config_menu_button = Gtk.Button(label="Config")
        self.linux_wallpaperengine_config_menu_button.connect("clicked", self.on_linux_wallpaperengine_config_menu_button_clicked)

        # Performance Options
        self.linux_wallpaperengine_performance_menu = Gtk.Menu()

        self.linux_wallpaperengine_no_fullscreen_pause_checkbox = Gtk.CheckMenuItem(label="no-fullscreen-pause")
        self.linux_wallpaperengine_no_fullscreen_pause_checkbox.set_active(self.cf.linux_wallpaperengine_no_fullscreen_pause)
        self.linux_wallpaperengine_no_fullscreen_pause_checkbox.connect("toggled", self.linux_wallpaperengine_no_fullscreen_pause_toggled)
        self.linux_wallpaperengine_performance_menu.append( self.linux_wallpaperengine_no_fullscreen_pause_checkbox)

        self.linux_wallpaperengine_fullscreen_pause_only_active_checkbox = Gtk.CheckMenuItem(label="fullscreen-pause-only-active")
        self.linux_wallpaperengine_fullscreen_pause_only_active_checkbox.set_active(self.cf.linux_wallpaperengine_fullscreen_pause_only_active)
        self.linux_wallpaperengine_fullscreen_pause_only_active_checkbox.connect("toggled", self.linux_wallpaperengine_fullscreen_pause_only_active_toggled)
        self.linux_wallpaperengine_performance_menu.append( self.linux_wallpaperengine_fullscreen_pause_only_active_checkbox)

        self.linux_wallpaperengine_performance_menu.show_all()
        self.linux_wallpaperengine_performance_menu_button = Gtk.Button(label="Performance")
        self.linux_wallpaperengine_performance_menu_button.connect("clicked", self.on_linux_wallpaperengine_performance_menu_button_clicked)

        # linux-wallpaperengine --clamp
        self.linux_wallpaperengine_clamp_combo = Gtk.ComboBoxText()
        self.linux_wallpaperengine_clamp_combo.append_text(LINUX_WALLPAPERENGINE_CLAMP[0].capitalize())
        self.linux_wallpaperengine_clamp_combo.append_text(LINUX_WALLPAPERENGINE_CLAMP[1].capitalize())
        self.linux_wallpaperengine_clamp_combo.append_text(LINUX_WALLPAPERENGINE_CLAMP[2].capitalize())
        self.linux_wallpaperengine_clamp_combo.append_text(LINUX_WALLPAPERENGINE_CLAMP[3].capitalize())
        if self.cf.linux_wallpaperengine_clamp in LINUX_WALLPAPERENGINE_CLAMP:
            self.linux_wallpaperengine_clamp_combo.set_active(LINUX_WALLPAPERENGINE_CLAMP.index(self.cf.linux_wallpaperengine_clamp))
        else:
            self.linux_wallpaperengine_clamp_combo.set_active(0)
        self.linux_wallpaperengine_clamp_combo.connect("changed", self.linux_wallpaperengine_clamp_changed)
        self.linux_wallpaperengine_clamp_combo.set_tooltip_text("clamp")

        # Add different buttons depending on backend:
        self.monitor_option_display()
        self.mpv_options_display()
        self.linux_wallpaperengine_options_display()
        self.fill_option_display()
        self.color_picker_display()
        self.swww_or_awww_options_display()
        self.hyprland_restart_button_display()


        # Connect the key press events to various actions:
        self.connect("key-press-event", self.on_key_pressed)

        self.connect("button-press-event", self.on_window_clicked)

        # Connect window resizing events to change the number of columns.
        # self.connect("size-allocate", self.on_window_resize)

        self.show_all()

    def create_fill_option_combo(self):
        # Create a fill option dropdown menu:
        self.fill_option_combo = Gtk.ComboBoxText()
        for option in FILL_OPTIONS:
            capitalized_option = option[0].upper() + option[1:]
            self.fill_option_combo.append_text(capitalized_option)
        if self.cf.fill_option in FILL_OPTIONS:
            active_fill_option_index = FILL_OPTIONS.index(self.cf.fill_option)
            self.fill_option_combo.set_active(active_fill_option_index)
        else:
            self.fill_option_combo.set_active(0)
        self.fill_option_combo.connect("changed", self.on_fill_option_changed)
        self.fill_option_combo.set_tooltip_text(self.txt.tip_fill)

        # Create a fill option (linux-wallpaperengine) dropdown menu:
        self.fill_option_combo_linux_wallpaperengine = Gtk.ComboBoxText()
        for option in LINUX_WALLPAPERENGINE_FILL_OPTIONS:
            capitalized_option = option[0].upper() + option[1:]
            self.fill_option_combo_linux_wallpaperengine.append_text(capitalized_option)
        if self.cf.fill_option in LINUX_WALLPAPERENGINE_FILL_OPTIONS:
            active_fill_option_index = LINUX_WALLPAPERENGINE_FILL_OPTIONS.index(self.cf.fill_option)
            self.fill_option_combo_linux_wallpaperengine.set_active(active_fill_option_index)
        else:
            self.fill_option_combo_linux_wallpaperengine.set_active(0)
        self.fill_option_combo_linux_wallpaperengine.connect("changed", self.on_fill_option_changed)
        self.fill_option_combo_linux_wallpaperengine.set_tooltip_text(self.txt.tip_fill)

    def create_options_menu(self) -> None:
        """Create a GTK menu with some options of the application"""
        self.menu = Gtk.Menu()

        # Create gifs toggle:
        self.filter_gifs_checkbox = Gtk.CheckMenuItem(label=self.txt.msg_gifs)
        self.filter_gifs_checkbox.set_active(self.cf.show_gifs_only)
        self.filter_gifs_checkbox.connect("toggled", self.on_filter_gifs_toggled)
        self.menu.append(self.filter_gifs_checkbox)

        # Create subfolder toggle (hidden in API mode):
        self.include_subfolders_checkbox = Gtk.CheckMenuItem(label=self.txt.msg_subfolders)
        self.include_subfolders_checkbox.set_active(self.cf.include_subfolders)
        self.include_subfolders_checkbox.connect("toggled", self.on_include_subfolders_toggled)
        self.menu.append(self.include_subfolders_checkbox)
        self.include_subfolders_checkbox.set_visible(False)

        # Create all subfolder toggle (hidden in API mode):
        self.include_all_subfolders_checkbox = Gtk.CheckMenuItem(label=self.txt.msg_all_subfolders)
        self.include_all_subfolders_checkbox.set_active(self.cf.include_all_subfolders)
        self.include_all_subfolders_checkbox.connect("toggled", self.on_include_all_subfolders_toggled)
        self.menu.append(self.include_all_subfolders_checkbox)
        self.include_all_subfolders_checkbox.set_visible(False)

        # Create hidden toggle (hidden in API mode):
        self.include_hidden_checkbox = Gtk.CheckMenuItem(label=self.txt.msg_hidden)
        self.include_hidden_checkbox.set_active(self.cf.show_hidden)
        self.include_hidden_checkbox.connect("toggled", self.on_hidden_files_toggled)
        self.menu.append(self.include_hidden_checkbox)
        self.include_hidden_checkbox.set_visible(False)

        # Create show folder path toggle:
        self.show_path_in_tooltip_checkbox = Gtk.CheckMenuItem(label=self.txt.msg_show_path_in_tooltip)
        self.show_path_in_tooltip_checkbox.set_active(self.cf.show_path_in_tooltip)
        self.show_path_in_tooltip_checkbox.connect("toggled", self.on_show_path_in_tooltip_toggled)
        self.menu.append(self.show_path_in_tooltip_checkbox)

        # Create zen mode toggle:
        self.zen_mode_checkbox = Gtk.CheckMenuItem(label=self.txt.msg_zen)
        self.zen_mode_checkbox.set_active(self.cf.zen_mode)
        self.zen_mode_checkbox.connect("toggled", self.on_zen_mode_toggled)
        self.menu.append(self.zen_mode_checkbox)

        self.menu.show_all()


    def on_options_button_clicked(self, widget) -> None:
        '''Position the menu at the button and show it'''
        self.create_options_menu()
        self.menu.popup_at_widget(widget, Gdk.Gravity.NORTH, Gdk.Gravity.SOUTH, None)

    def monitor_option_display(self) -> None:
        """Display monitor option if backend is not feh or wallutils or macos"""
        self.options_box.remove(self.monitor_option_combo)

        # These backends do not support monitors:
        if self.cf.backend in ["feh", "wallutils", "macos", "none"]:
            return

        # Check available monitors:
        monitor_names = get_monitor_options(self.cf.backend)

        # Create a monitor option dropdown menu:
        self.monitor_option_combo = Gtk.ComboBoxText()
        for monitor in monitor_names:
            self.monitor_option_combo.append_text(monitor)
        if self.cf.monitors[-1] in monitor_names:
            self.monitor_option_combo.set_active(monitor_names.index(self.cf.monitors[-1]))
        else:
            self.monitor_option_combo.set_active(0)

        self.cf.selected_monitor = self.monitor_option_combo.get_active_text()

        self.monitor_option_combo.connect("changed", self.on_monitor_option_changed)
        self.monitor_option_combo.set_tooltip_text(self.txt.tip_display)

        # Add it to the row of buttons:
        self.options_box.pack_start(self.monitor_option_combo, False, False, 0)

    def swww_or_awww_options_display(self) -> None:
        """Show swww transition options if backend is swww or awww"""
        self.options_box.remove(self.swww_transitions_options)
        self.options_box.remove(self.swww_angle_entry)
        self.options_box.remove(self.swww_steps_entry)
        self.options_box.remove(self.swww_fps_entry)
        self.options_box.remove(self.swww_duration_entry)

        if self.cf.backend != "swww" and self.cf.backend != "awww" :
            return

        self.swww_transitions_options = Gtk.ComboBoxText()
        for transitions in SWWW_TRANSITION_TYPES:
            self.swww_transitions_options.append_text(transitions)
        active_transition = 0
        if self.cf.swww_transition_type in SWWW_TRANSITION_TYPES:
            active_transition = SWWW_TRANSITION_TYPES.index(self.cf.swww_transition_type)
            self.swww_transitions_options.set_active(active_transition)
            self.swww_transitions_options.connect("changed", self.on_transition_option_changed)
            self.swww_transitions_options.set_tooltip_text(self.txt.tip_transition)

        self.options_box.pack_end(self.swww_steps_entry, False, False, 0)
        self.options_box.pack_end(self.swww_fps_entry, False, False, 0)
        self.options_box.pack_end(self.swww_angle_entry, False, False, 0)
        self.options_box.pack_end(self.swww_duration_entry, False, False, 0)
        self.options_box.pack_end(self.swww_transitions_options, False, False, 0)

    def hyprland_restart_button_display(self) -> None:
        # If hyprpaper is installed, add a button to restart it
        self.options_box.remove(self.hyprpaper_restart)
        if not self.cf.backend == "hyprpaper":
            return
        self.options_box.pack_end(self.hyprpaper_restart, False, False, 0)

    def swww_or_awww_options_read(self) -> None:
        """Read swww transition options from the UI if they are valid"""
        if self.cf.backend != "swww" and self.cf.backend != "awww":
            return
        angle = self.swww_angle_entry.get_text()
        steps = self.swww_steps_entry.get_text()
        fps = self.swww_fps_entry.get_text()
        duration = self.swww_duration_entry.get_text()
        if angle.isdigit():
            self.cf.swww_transition_angle = angle
        if steps.isdigit():
            self.cf.swww_transition_step = steps
        if fps.isdigit():
            self.cf.swww_transition_fps = fps
        if duration.isdigit():
            self.cf.swww_transition_duration = duration

    def mpv_options_display(self) -> None:
        """Show mpv options if backend is mpvpaper or gslapper, and remove them for other backends"""
        self.options_box.remove(self.mpv_stop_button)
        self.options_box.remove(self.mpv_pause_button)
        self.options_box.remove(self.mpv_sound_toggle)
        if self.cf.backend == "mpvpaper":
            self.options_box.pack_end(self.mpv_stop_button, False, False, 0)
            self.options_box.pack_end(self.mpv_pause_button, False, False, 0)
            self.options_box.pack_end(self.mpv_sound_toggle, False, False, 0)
        elif self.cf.backend == "gslapper":
            # Hide pause button for gSlapper since it doesn't support pause functionality
            self.options_box.pack_end(self.mpv_stop_button, False, False, 0)
            self.options_box.pack_end(self.mpv_sound_toggle, False, False, 0)

    def fill_option_display(self):
        """Display fill option if backend are not linux-wallpaperengine or hyprpaper"""
        self.options_box.remove(self.fill_option_combo)
        self.options_box.remove(self.fill_option_combo_linux_wallpaperengine)
        if self.cf.backend not in ['linux-wallpaperengine', 'hyprpaper', 'none']:
            self.options_box.pack_end(self.fill_option_combo, False, False, 0)
        elif self.cf.backend == 'linux-wallpaperengine':
            self.options_box.pack_end(self.fill_option_combo_linux_wallpaperengine, False, False, 0)

    def on_linux_wallpaperengine_sound_menu_button_clicked(self, widget):
        self.linux_wallpaperengine_sound_menu.popup_at_widget(widget, Gdk.Gravity.NORTH, Gdk.Gravity.SOUTH, None)

    def on_linux_wallpaperengine_config_menu_button_clicked(self, widget):
        self.linux_wallpaperengine_config_menu.popup_at_widget(widget, Gdk.Gravity.NORTH, Gdk.Gravity.SOUTH, None)

    def on_linux_wallpaperengine_performance_menu_button_clicked(self, widget):
        self.linux_wallpaperengine_performance_menu.popup_at_widget(widget, Gdk.Gravity.NORTH, Gdk.Gravity.SOUTH, None)

    def on_linux_wallpaperengine_silent_toggled(self, widget):
        self.cf.linux_wallpaperengine_silent = not self.cf.linux_wallpaperengine_silent

    def on_linux_wallpaperengine_noautomnute_toggled(self, widget):
        self.cf.linux_wallpaperengine_noautomute = not self.cf.linux_wallpaperengine_noautomute

    def on_linux_wallpaperengine_no_audio_processing_toggled(self, widget):
        self.cf.linux_wallpaperengine_no_audio_processing = not self.cf.linux_wallpaperengine_no_audio_processing

    def on_linux_wallpaperengine_disable_particles_toggled(self, widget):
        self.cf.linux_wallpaperengine_disable_particles = not self.cf.linux_wallpaperengine_disable_particles

    def on_linux_wallpaperengine_disable_mouse_toggled(self, widget):
        self.cf.linux_wallpaperengine_disable_mouse = not self.cf.linux_wallpaperengine_disable_mouse

    def on_linux_wallpaperengine_disable_parallax_toggled(self, widget):
        self.cf.linux_wallpaperengine_disable_parallax = not self.cf.linux_wallpaperengine_disable_parallax

    def linux_wallpaperengine_no_fullscreen_pause_toggled(self, widget):
        self.cf.linux_wallpaperengine_no_fullscreen_pause = not self.cf.linux_wallpaperengine_no_fullscreen_pause

    def linux_wallpaperengine_fullscreen_pause_only_active_toggled(self, widget):
        self.cf.linux_wallpaperengine_fullscreen_pause_only_active = not self.cf.linux_wallpaperengine_fullscreen_pause_only_active

    def linux_wallpaperengine_clamp_changed(self, widget):
        self.cf.linux_wallpaperengine_clamp = self.linux_wallpaperengine_clamp_combo.get_active_text().lower()

    def linux_wallpaperengine_options_read(self):
        fps = self.linux_wallpaperengine_fps_entry.get_text()
        volume = self.linux_wallpaperengine_volume_entry.get_text()

        if fps.isdigit():
            self.cf.linux_wallpaperengine_fps = int(fps)
        if volume.isdigit():
            self.cf.linux_wallpaperengine_volume = int(volume)

    def linux_wallpaperengine_options_display(self):
        self.options_box.remove(self.linux_wallpaperengine_clamp_combo)
        self.options_box.remove(self.linux_wallpaperengine_performance_menu_button)
        self.options_box.remove(self.linux_wallpaperengine_sound_menu_button)
        self.options_box.remove(self.linux_wallpaperengine_config_menu_button)
        self.options_box.remove(self.linux_wallpaperengine_volume_entry)
        self.options_box.remove(self.linux_wallpaperengine_fps_entry)

        if self.cf.backend != "linux-wallpaperengine":
            return

        self.options_box.pack_end(self.linux_wallpaperengine_clamp_combo, False, False, 0)
        self.options_box.pack_end(self.linux_wallpaperengine_config_menu_button, False, False, 0)
        self.options_box.pack_end(self.linux_wallpaperengine_sound_menu_button, False, False, 0)
        self.options_box.pack_end(self.linux_wallpaperengine_performance_menu_button, False, False, 0)
        self.options_box.pack_end(self.linux_wallpaperengine_volume_entry, False, False, 0)
        self.options_box.pack_end(self.linux_wallpaperengine_fps_entry, False, False, 0)

    def color_picker_display(self):
        """Display color option if backend is not hyprpaper"""
        self.options_box.remove(self.color_picker_button)
        if self.cf.backend not in ['linux-wallpaperengine', 'hyprpaper', 'none']:
            self.options_box.pack_end(self.color_picker_button, False, False, 0)

    def check_backends(self) -> None:
        """Before running the app, check which backends are installed or show the error"""
        if len(self.cf.installed_backends) == 1:
            self.show_message(self.txt.err_backend)
            exit()

    def show_message(self, message: str) -> None:
        """Show messages to user with ok button"""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format=message,
        )
        dialog.run()
        dialog.destroy()


    def fetch_wallhaven_gallery(self) -> None:
        """Fetch wallpapers from Wallhaven API and display thumbnails in grid"""
        try:
            preset_idx = self.wh_combo.get_active()
            preset = self.wh_presets[preset_idx] if 0 <= preset_idx < len(self.wh_presets) else "random"
            query = self.search_entry.get_text().strip()
            items, meta = wallhaven.search(preset, query, self.current_page)
        except Exception as e:
            GLib.idle_add(self.show_message, f"Wallhaven error: {e}")
            return

        self.wallhaven_items = items
        self.last_page = meta.last
        self.total_results = meta.total
        self.current_page = meta.current

        self.thumbnails = [None] * len(items)
        self.image_paths = [f"wh-{item.id}" for item in items]
        self.image_names = [f"wh-{item.id} ({item.resolution})" for item in items]

        prefs = self._load_preferences()
        self.filtered_indices = self._get_filtered_indices(prefs)
        if not self.filtered_indices:
            self.filtered_indices = []
        self.selected_index = 0

        GLib.idle_add(self._clear_grid)
        GLib.idle_add(self._update_pagination)

        for i in self.filtered_indices:
            pixbuf = wallhaven.fetch_thumbnail(items[i].thumb_url)
            self.thumbnails[i] = pixbuf
            GLib.idle_add(self._add_thumbnail_to_grid, i)

        GLib.idle_add(self.scroll_to_selected_image)
        GLib.idle_add(self._update_status_bar)

    def _clear_grid(self) -> None:
        """Remove all children from the grid"""
        for child in self.grid.get_children():
            self.grid.remove(child)

    def _add_thumbnail_to_grid(self, idx: int) -> None:
        """Add a single thumbnail to the grid at the correct filtered position"""
        if idx >= len(self.thumbnails) or self.thumbnails[idx] is None:
            return

        pixbuf = self.thumbnails[idx]
        item = self.wallhaven_items[idx]
        name = self.image_names[idx]
        path = self.image_paths[idx]

        display_pos = self.filtered_indices.index(idx)
        row = display_pos // self.cf.number_of_columns
        col = display_pos % self.cf.number_of_columns

        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.get_style_context().add_class("grid-image")
        image.set_tooltip_text(name)

        button = Gtk.Button()
        button.get_style_context().add_class("grid-button")
        if idx == self.selected_index:
            button.set_relief(Gtk.ReliefStyle.NORMAL)
            button.get_style_context().add_class("highlighted-button")
        else:
            button.set_relief(Gtk.ReliefStyle.NONE)

        status = self._get_wallpaper_status(path)
        if status == "kept":
            button.get_style_context().add_class("wallpaper-kept")
        elif status == "discarded":
            button.get_style_context().add_class("wallpaper-discarded")

        button.add(image)
        self.grid.attach(button, col, row, 1, 1)
        self.grid.show_all()
        button.connect("clicked", self.on_image_clicked, idx)


    def _get_filtered_indices(self, prefs_cache=None) -> list:
        """Return indices of items matching search query and status filter"""
        search_query = self.search_entry.get_text().lower()
        if prefs_cache is None:
            prefs_cache = self._load_preferences()

        result = []
        for i, name in enumerate(self.image_names):
            if search_query and search_query not in name.lower():
                continue
            if self.status_filter != "all":
                path = self.image_paths[i]
                status = self._get_wallpaper_status(path, prefs_cache)
                if self.status_filter == "unreviewed":
                    if status is not None:
                        continue
                elif status != self.status_filter:
                    continue
            result.append(i)
        return result


    def load_image_grid(self) -> None:
        """Rebuild the grid from current wallhaven_items and filter state"""
        prefs_cache = self._load_preferences()
        self.filtered_indices = self._get_filtered_indices(prefs_cache)
        if not self.filtered_indices:
            self.filtered_indices = []

        if self.selected_index >= len(self.filtered_indices):
            self.selected_index = max(0, len(self.filtered_indices) - 1)

        self._clear_grid()

        for idx in self.filtered_indices:
            thumbnail = self.thumbnails[idx] if idx < len(self.thumbnails) else None
            if thumbnail is None:
                continue

            name = self.image_names[idx] if idx < len(self.image_names) else ""
            path = self.image_paths[idx] if idx < len(self.image_paths) else ""

            display_pos = self.filtered_indices.index(idx)
            row = display_pos // self.cf.number_of_columns
            col = display_pos % self.cf.number_of_columns

            image = Gtk.Image.new_from_pixbuf(thumbnail)
            image.set_tooltip_text(name)
            image.get_style_context().add_class("grid-image")

            button = Gtk.Button()
            button.get_style_context().add_class("grid-button")
            if idx == self.selected_index:
                button.set_relief(Gtk.ReliefStyle.NORMAL)
                button.get_style_context().add_class("highlighted-button")
            else:
                button.set_relief(Gtk.ReliefStyle.NONE)

            status = self._get_wallpaper_status(str(path), prefs_cache)
            if status == "kept":
                button.get_style_context().add_class("wallpaper-kept")
            elif status == "discarded":
                button.get_style_context().add_class("wallpaper-discarded")

            button.add(image)
            self.grid.attach(button, col, row, 1, 1)
            button.connect("clicked", self.on_image_clicked, idx)

        self.grid.show_all()
        self.toggle_zen_mode()
        self._update_status_bar()


    def _update_status_bar(self):
        """Update the status bar with API page info and brain stats"""
        prefs = self._load_preferences()
        kept = len(prefs.get("kept", {}))
        discarded = len(prefs.get("discarded", {}))
        tag_count = int(prefs.get("tag_count", 0))
        top_tags = sorted(prefs.get("tag_weights", {}).items(), key=lambda x: -x[1])[:3]
        tag_str = " | ".join(f"{t} ({w:.0f})" for t, w in top_tags) if top_tags else "—"
        page_info = f"Results: {self.total_results} | Page {self.current_page}/{self.last_page}" if self.total_results else "No results"
        shown = len(self.filtered_indices)
        if shown < len(self.wallhaven_items):
            page_info += f" ({shown} shown)"
        self.status_label.set_text(f"{page_info}  |  ♥ {kept}  |  ✕ {discarded}  |  Tags: {tag_count}  |  Top: {tag_str}")

    def _load_preferences(self):
        """Load preferences.json once and return the parsed dict, or empty dict"""
        try:
            prefs_file = Path.home() / ".config" / "waypaper" / "preferences.json"
            if prefs_file.exists():
                return json.loads(prefs_file.read_text())
        except Exception:
            pass
        return {}

    def _get_wallpaper_status(self, path, prefs_cache=None):
        """Check if a wallpaper is kept or discarded from preferences"""
        if prefs_cache is None:
            prefs_cache = self._load_preferences()
        if not prefs_cache:
            return None
        try:
            name = Path(path).stem
            if name.startswith("wh-"):
                wid = name[3:]
            else:
                import hashlib
                wid = "local_" + hashlib.md5(str(path).encode()).hexdigest()[:12]
            if wid in prefs_cache.get("kept", {}):
                return "kept"
            if wid in prefs_cache.get("discarded", {}):
                return "discarded"
        except Exception:
            pass
        return None

    def toggle_zen_mode(self):
        """Hide or show UI elements when zen mode is enabled or disabled"""
        if self.cf.zen_mode:
            for widget in self.top_container:
                widget.hide()
            for widget in self.options_box:
                widget.hide()
        else:
            for widget in self.top_container:
                widget.show()
            for widget in self.options_box:
                widget.show()


    # def on_window_resize(self, widget, allocation) -> None:
        # """Recalculate the number of columns on window resize and repopulate the grid"""

        # As frequent resize freezed the interface, so we only do it each fifth resize:
        # self.number_of_resize += 1
        # if self.number_of_resize < 5:
            # return

        # Calculate new number of columns and reload the grid:
        # self.cf.number_of_columns = max(1, allocation.width // 250)
        # GLib.idle_add(self.load_image_grid)
        # self.number_of_resize = 0


    def scroll_to_selected_image(self) -> None:
        """Scroll the window to see the highlighted image"""
        scrolled_window_height = self.scrolled_window.get_vadjustment().get_page_size()
        # current_y = self.highlighted_image_row * 180
        subscreen_num = self.highlighted_image_y // scrolled_window_height
        scroll = scrolled_window_height * subscreen_num
        self.scrolled_window.get_vadjustment().set_value(scroll)


    def set_selected_wallpaper(self, path: str) -> None:
        """Set selected image as a wallpaper and save the state"""
        self.swww_or_awww_options_read()
        self.linux_wallpaperengine_options_read()
        self.cf.select_wallpaper(path)
        if self.cf.selected_wallpaper:
            threading.Thread(target=change_wallpaper, args=(self.cf.selected_wallpaper, self.cf, self.cf.selected_monitor)).start()
        self.cf.attribute_selected_wallpaper()
        self.cf.save()


    def choose_folder(self) -> None:
        """No-op in API mode: browsing is always from Wallhaven"""
        pass


    def on_choose_folder_clicked(self, widget) -> None:
        """Choosing the folder of images, saving the path, and reloading images"""
        self.choose_folder()
        self.cf.save()


    def on_status_filter_toggled(self, toggle, key) -> None:
        """Toggle status filter: all/kept/discarded/unreviewed"""
        if not toggle.get_active():
            return
        self.status_filter = key
        for k, btn in self.filter_buttons.items():
            if k != key:
                btn.set_active(False)
        self.load_image_grid()

    def on_filter_gifs_toggled(self, toggle) -> None:
        """No-op in API mode: Wallhaven doesn't have a gif-only filter"""


    def on_zen_mode_toggled(self, toggle) -> None:
        """Toggle zen mode checkbox via menu"""
        self.show_message("You are entering Zen mode.\nPress z to return to normal mode.")
        self.cf.zen_mode = toggle.get_active()
        self.load_image_grid()


    def on_mpv_sound_toggled(self, toggle) -> None:
        """Toggle sound of mpv player or gSlapper"""
        self.cf.mpvpaper_sound = toggle.get_active()
        if self.cf.backend == "mpvpaper":
            subprocess.Popen(f"echo 'cycle mute' | socat - /tmp/mpv-socket-{self.cf.selected_monitor}", shell=True)
        elif self.cf.backend == "gslapper":
            # For gSlapper, immediately restart with new audio setting
            from waypaper.changer import change_with_gslapper
            from pathlib import Path

            # Get current wallpaper path from config
            if hasattr(self.cf, 'selected_wallpaper') and self.cf.selected_wallpaper:
                try:
                    change_with_gslapper(Path(self.cf.selected_wallpaper), self.cf, self.cf.selected_monitor)
                except Exception as e:
                    print(f"Could not restart gSlapper with new audio setting: {e}")


    def on_include_subfolders_toggled(self, toggle) -> None:
        """No-op in API mode"""


    def on_include_all_subfolders_toggled(self, toggle) -> None:
        """No-op in API mode"""


    def toggle_include_subfolders(self) -> None:
        """No-op in API mode"""


    def on_hidden_files_toggled(self, toggle) -> None:
        """No-op in API mode"""


    def toggle_hidden_files(self) -> None:
        """No-op in API mode"""


    def on_show_path_in_tooltip_toggled(self, widget) -> None:
        """No-op in API mode"""


    def on_fill_option_changed(self, combo) -> None:
        """Save fill parameter when it was changed"""
        self.cf.fill_option = combo.get_active_text().lower()


    def on_monitor_option_changed(self, combo) -> None:
        """Save monitor parameter when it was changed"""
        self.cf.selected_monitor = combo.get_active_text()


    def on_sort_option_changed(self, combo) -> None:
        """No-op in API mode: sorting is controlled by Wallhaven API"""


    def on_backend_option_changed(self, combo) -> None:
        """Save backend parameter whet it is changed"""
        self.cf.backend = self.backend_option_combo.get_active_text()
        self.cf.selected_monitor = "All"
        self.monitor_option_display()
        self.mpv_options_display()
        self.fill_option_display()
        self.color_picker_display()
        self.swww_or_awww_options_display()
        self.linux_wallpaperengine_options_display()
        self.hyprland_restart_button_display()
        self.show_all()


    def on_transition_option_changed(self, combo) -> None:
        """Update the active transition type based on the selected option"""
        active_index = combo.get_active()
        self.cf.swww_transition_type = SWWW_TRANSITION_TYPES[active_index]
        print(f"Transition type changed to: {self.cf.swww_transition_type}")


    def on_color_set(self, color_button):
        """Convert selected color to web format"""
        rgba_color = color_button.get_rgba()
        red = int(rgba_color.red * 255)
        green = int(rgba_color.green * 255)
        blue = int(rgba_color.blue * 255)
        self.cf.color = "#{:02X}{:02X}{:02X}".format(red, green, blue)


    def _current_full_path(self):
        """Return the full image path for the current selected_index (only if exists on disk)"""
        if not self.filtered_indices or self.selected_index >= len(self.filtered_indices):
            return None
        full_idx = self.filtered_indices[self.selected_index]
        if full_idx >= len(self.image_paths):
            return None
        path = self.image_paths[full_idx]
        if os.path.exists(path):
            return path
        return None

    def _current_full_idx(self):
        """Return the unfiltered index for the current selected_index"""
        if not self.filtered_indices or self.selected_index >= len(self.filtered_indices):
            return None
        full_idx = self.filtered_indices[self.selected_index]
        if full_idx >= len(self.image_paths):
            return None
        return full_idx

    def _download_and_set(self, item, idx):
        """Download full wallpaper to temp and set as wallpaper"""
        temp_dir = Path.home() / ".cache" / "waypaper" / "temp"
        ext = item.full_url.rsplit('.', 1)[-1].split('?')[0] if '.' in item.full_url else "jpg"
        dest = temp_dir / f"wh-{item.id}.{ext}"
        result = wallhaven.download_full(item.full_url, dest)
        if result:
            self.image_paths[idx] = str(dest)
            GLib.idle_add(lambda: self.set_selected_wallpaper(str(dest)))
        else:
            GLib.idle_add(lambda: self.show_message(f"Failed to download {item.id}"))

    def _save_wallpaper(self, show_message=True) -> None:
        """Save selected wallpaper permanently to library"""
        if not self.filtered_indices or self.selected_index >= len(self.filtered_indices):
            return
        full_idx = self.filtered_indices[self.selected_index]
        if full_idx >= len(self.wallhaven_items):
            return
        item = self.wallhaven_items[full_idx]
        threading.Thread(target=self._run_save, args=(item, show_message), daemon=True).start()

    def _run_save(self, item, show_message):
        """Download full wallpaper to library and register with brain"""
        library_dir = Path.home() / "Imágenes" / "wallpapers"
        ext = item.full_url.rsplit('.', 1)[-1].split('?')[0] if '.' in item.full_url else "jpg"
        dest = library_dir / f"wh-{item.id}.{ext}"
        result = wallhaven.download_full(item.full_url, dest)
        if result:
            try:
                subprocess.run([str(Path.home() / ".local/bin/wallpaper-brain"), "keep", str(result)],
                               capture_output=True, timeout=30)
            except Exception:
                pass
            GLib.idle_add(self.load_image_grid)
            if show_message:
                GLib.idle_add(self.show_message, "♥ Saved to library")
        else:
            GLib.idle_add(lambda: self.show_message(f"Failed to save {item.id}"))

    def on_save_clicked(self, widget) -> None:
        """Button handler: save selected wallpaper to library"""
        self._save_wallpaper()

    def on_refresh_clicked(self, widget) -> None:
        """Re-fetch current page of wallpapers from Wallhaven API"""
        self.current_page = 1
        threading.Thread(target=self.fetch_wallhaven_gallery, daemon=True).start()

    def _run_keep(self, path):
        """Run wallpaper-brain keep in a thread, then reload grid"""
        try:
            subprocess.run([str(Path.home() / ".local/bin/wallpaper-brain"), "keep", str(path)],
                           capture_output=True, timeout=30)
        except Exception:
            pass
        GLib.idle_add(self.load_image_grid)

    def _run_discard(self, path):
        """Run wallpaper-brain discard in a thread, then reload grid"""
        try:
            subprocess.run([str(Path.home() / ".local/bin/wallpaper-brain"), "discard", str(path)],
                           capture_output=True, timeout=30)
        except Exception:
            pass
        GLib.idle_add(self.load_image_grid)

    def on_prev_page(self, widget) -> None:
        """Go to previous page of Wallhaven results"""
        if self.current_page > 1:
            self.current_page -= 1
            threading.Thread(target=self.fetch_wallhaven_gallery, daemon=True).start()

    def on_next_page(self, widget) -> None:
        """Go to next page of Wallhaven results"""
        if self.current_page < self.last_page:
            self.current_page += 1
            threading.Thread(target=self.fetch_wallhaven_gallery, daemon=True).start()

    def _update_pagination(self) -> None:
        """Update pagination UI controls"""
        self.page_label.set_text(f"Page {self.current_page} / {self.last_page if self.last_page else 1}")
        self.prev_page_button.set_sensitive(self.current_page > 1)
        self.next_page_button.set_sensitive(self.current_page < self.last_page)

    def on_hyprland_restart(self, widget) -> None:
        # As in the new Hyprpaper Update Unloading wallpapers is not possible anymore, Hyprpaper needs to be restarted to free up memory
        if self.cf.backend == "hyprpaper":
            hyprpaper_kill_command = ["pkill", "-x", "hyprpaper"]
            hyprpaper_restart_command = ["hyprctl", "dispatch", "exec", "hyprpaper"]
            waypaper_restore_command = ["waypaper", "--restore"]

            try:
                subprocess.run(hyprpaper_kill_command, encoding="utf-8")
                subprocess.run(hyprpaper_restart_command, encoding="utf-8")
                subprocess.run(waypaper_restore_command, encoding="utf-8")
                # Problem: Hyprland uses default wallpaper after restart
            except Exception as e:
                print(f"Exception: {e}")

    def on_mpv_stop_button_clicked(self, widget) -> None:
        """On clicking mpv stop button, kill the mpvpaper or gslapper"""
        if self.cf.backend == "mpvpaper":
            subprocess.Popen(["killall", "mpvpaper"])
        elif self.cf.backend == "gslapper":
            subprocess.Popen(["killall", "gslapper"])

    def on_mpv_pause_button_clicked(self, widget) -> None:
        """On clicking mpv pause button, pause mpvpaper or show not supported for gSlapper"""
        if self.cf.backend == "mpvpaper":
            subprocess.Popen(f"echo 'cycle pause' | socat - /tmp/mpv-socket-{self.cf.selected_monitor}", shell=True)
        elif self.cf.backend == "gslapper":
            # gSlapper doesn't support pause, so do nothing or show message
            print("Pause not supported for gSlapper")

    def on_random_clicked(self, widget) -> None:
        """On clicking random button, set random wallpaper"""
        self.set_random_wallpaper()

    def on_exit_clicked(self, widget) -> None:
        """On clicking exit button, exit"""
        Gtk.main_quit()


    def set_random_wallpaper(self) -> None:
        """Fetch a random wallpaper from Wallhaven API and set it"""
        threading.Thread(target=self._fetch_random_and_set, daemon=True).start()

    def _fetch_random_and_set(self) -> None:
        """Thread: get random from API, download, set"""
        try:
            items, _ = wallhaven.search("random", page=1)
            if not items:
                return
            item = items[0]
            temp_dir = Path.home() / ".cache" / "waypaper" / "temp"
            ext = item.full_url.rsplit('.', 1)[-1].split('?')[0] if '.' in item.full_url else "jpg"
            dest = temp_dir / f"wh-{item.id}.{ext}"
            result = wallhaven.download_full(item.full_url, dest)
            if result:
                GLib.idle_add(lambda: self.set_selected_wallpaper(str(result)))
        except Exception as e:
            GLib.idle_add(lambda: self.show_message(f"Random error: {e}"))

    def clear_cache(self) -> None:
        """Refresh: re-fetch current page of Wallhaven results"""
        self.current_page = 1
        threading.Thread(target=self.fetch_wallhaven_gallery, daemon=True).start()


    def on_key_pressed(self, widget, event) -> bool:
        """Process various key binding"""

        # Processing keys for losing focus on text fields:
        if self.is_enering_text:
            if event.keyval in self.keys.clear_input_fields:
                self.reset_input_fields()
            return

        # Processing rest of the keys:
        elif event.keyval in self.keys.quit:
            Gtk.main_quit()

        elif event.keyval in self.keys.clear_cache:
            self.clear_cache()

        elif event.keyval in self.keys.random_wallpaper:
            self.set_random_wallpaper()

        elif event.keyval in self.keys.hidden_files:
            self.toggle_hidden_files()

        elif event.keyval in self.keys.search:
            self.search_entry.grab_focus()
            return True

        elif event.keyval in self.keys.include_subfolders:
            self.toggle_include_subfolders()

        elif event.keyval in self.keys.navigation_left:
            self.selected_index = max(self.selected_index - 1, 0)
            self.load_image_grid()
            self.scroll_to_selected_image()

        elif event.keyval in self.keys.navigation_down:
            max_idx = max(0, len(self.filtered_indices) - 1)
            self.selected_index = min(self.selected_index + self.cf.number_of_columns, max_idx)
            self.load_image_grid()
            self.scroll_to_selected_image()

        elif event.keyval in self.keys.navigation_up:
            self.selected_index = max(self.selected_index - self.cf.number_of_columns, 0)
            self.load_image_grid()
            self.scroll_to_selected_image()

        elif event.keyval in self.keys.navigation_right:
            max_idx = max(0, len(self.filtered_indices) - 1)
            self.selected_index = min(self.selected_index + 1, max_idx)
            self.load_image_grid()
            self.scroll_to_selected_image()

        elif event.keyval in self.keys.choose_folder:
            self.choose_folder()

        elif event.keyval in self.keys.scroll_to_top:
            self.selected_index = 0
            self.load_image_grid()
            self.scroll_to_selected_image()

        elif event.keyval in self.keys.zen_mode:
            self.cf.zen_mode = not self.cf.zen_mode
            self.load_image_grid()

        elif event.keyval in self.keys.scroll_to_bottom:
            self.selected_index = max(0, len(self.filtered_indices) - 1)
            self.load_image_grid()
            self.scroll_to_selected_image()

        elif event.keyval in self.keys.help_page:
            message = self.txt.msg_help
            self.show_message(message)

        elif event.keyval in self.keys.select_wallpaper:
            wallpaper_path = self._current_full_path()
            full_idx = self._current_full_idx()
            if wallpaper_path:
                threading.Thread(target=lambda: self.set_selected_wallpaper(wallpaper_path),
                                 daemon=True).start()
            elif full_idx is not None and full_idx < len(self.wallhaven_items):
                item = self.wallhaven_items[full_idx]
                threading.Thread(target=self._download_and_set, args=(item, full_idx),
                                 daemon=True).start()

        elif event.keyval in self.keys.keep_wallpaper:
            wallpaper_path = self._current_full_path()
            full_idx = self._current_full_idx()
            if wallpaper_path:
                threading.Thread(target=self._run_keep, args=(wallpaper_path,), daemon=True).start()
            elif full_idx is not None and full_idx < len(self.wallhaven_items):
                item = self.wallhaven_items[full_idx]
                threading.Thread(target=self._run_save, args=(item, False), daemon=True).start()

        elif event.keyval in self.keys.discard_wallpaper:
            wallpaper_path = self._current_full_path()
            full_idx = self._current_full_idx()
            if wallpaper_path:
                threading.Thread(target=self._run_discard, args=(wallpaper_path,), daemon=True).start()
            elif full_idx is not None and full_idx < len(self.wallhaven_items):
                placeholder = self.image_paths[full_idx]
                threading.Thread(target=self._run_discard, args=(placeholder,), daemon=True).start()

        elif event.keyval in self.keys.save_wallpaper:
            self._save_wallpaper()

        # Prevent other default key handling:
        return event.keyval in [Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right, Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_period]


    def on_search_entry_changed(self, entry, event=None):
        """Debounced search: wait 500ms after typing, then fetch from API"""
        if self._search_timer:
            GLib.source_remove(self._search_timer)
        self._search_timer = GLib.timeout_add(500, self._on_search_timeout)

    def _on_search_timeout(self):
        """Trigger API search after debounce delay"""
        self._search_timer = None
        self.current_page = 1
        threading.Thread(target=self.fetch_wallhaven_gallery, daemon=True).start()
        return False

    def on_clear_button(self, event):
        self.search_entry.set_text("")
        self.current_page = 1
        threading.Thread(target=self.fetch_wallhaven_gallery, daemon=True).start()
        self.main_box.grab_focus()

    def on_focus_in(self, widget, event):
        self.is_enering_text = True

    def on_focus_out(self, widget, event):
        self.is_enering_text = False

    def reset_input_fields(self) -> None:
        """Reset all input fields and remove focus from them"""
        self.search_entry.set_visible(False)
        self.search_entry.set_visible(True)
        self.swww_angle_entry.set_visible(False)
        self.swww_angle_entry.set_visible(True)
        self.swww_steps_entry.set_visible(False)
        self.swww_steps_entry.set_visible(True)
        self.swww_duration_entry.set_visible(False)
        self.swww_duration_entry.set_visible(True)
        self.swww_fps_entry.set_visible(False)
        self.swww_fps_entry.set_visible(True)
        self.main_box.grab_focus()
        self.is_enering_text = False

    def on_window_clicked(self, widget, event) -> bool:
        """Handle clicks outside of input fields to unfocus them"""
        if self.is_enering_text:
            x, y = event.get_coords()

            focused_widget = self.get_focus()
            if focused_widget is not None:
                alloc = focused_widget.get_allocation()
                widget_x, widget_y = focused_widget.translate_coordinates(self, 0, 0) if focused_widget.translate_coordinates(self, 0, 0) else (0, 0)

                if (x < widget_x or x > widget_x + alloc.width or
                    y < widget_y or y > widget_y + alloc.height):
                    self.reset_input_fields()
                    return True

        return False

    def run(self) -> None:
        """Run GUI application"""
        self.connect("destroy", self.on_exit_clicked)
        self.show_all()
        Gtk.main()
