#!/usr/bin/env python3
"""
Save Game Backup Manager - Kivy GUI Version
A user-friendly graphical interface for the backup.py CLI tool using Kivy
"""

import os
import sys
import threading
import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.stacklayout import StackLayout

# Import the CLI functionality
from backup import (
    SaveBackupManager, 
    load_games_config, 
    save_games_config, 
    expand_path,
    list_games,
    format_file_size,
    get_directory_size
)


class BackupItemWidget(BoxLayout):
    """Widget to display a single backup item"""
    def __init__(self, backup_data, manager_gui, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(60)
        self.spacing = dp(10)
        self.padding = dp(10)
        
        self.backup_data = backup_data
        self.manager_gui = manager_gui
        
        # Backup info
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
        info_layout.add_widget(Label(
            text=f"[b]{backup_data['name']}[/b]",
            markup=True,
            text_size=(None, None),
            halign='left',
            size_hint_y=0.4
        ))
        info_layout.add_widget(Label(
            text=f"{backup_data['date']} {backup_data['time']} - {backup_data['size']}",
            text_size=(None, None),
            halign='left',
            size_hint_y=0.3
        ))
        if backup_data['description']:
            info_layout.add_widget(Label(
                text=backup_data['description'],
                text_size=(None, None),
                halign='left',
                size_hint_y=0.3
            ))
        
        self.add_widget(info_layout)
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=dp(5))
        
        restore_btn = Button(
            text='Restore',
            size_hint=(0.5, 1),
            background_color=(1, 0.8, 0, 1)  # Orange
        )
        restore_btn.bind(on_press=self.restore_backup)
        
        delete_btn = Button(
            text='Delete',
            size_hint=(0.5, 1),
            background_color=(1, 0.2, 0.2, 1)  # Red
        )
        delete_btn.bind(on_press=self.delete_backup)
        
        button_layout.add_widget(restore_btn)
        button_layout.add_widget(delete_btn)
        
        self.add_widget(button_layout)
    
    def restore_backup(self, instance):
        self.manager_gui.restore_backup(self.backup_data)
    
    def delete_backup(self, instance):
        self.manager_gui.delete_backup(self.backup_data)


class ConfirmationPopup(Popup):
    """Generic confirmation popup"""
    def __init__(self, title, message, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.6, 0.4)
        self.auto_dismiss = False
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Message
        content.add_widget(Label(
            text=message,
            text_size=(None, None),
            halign='center'
        ))
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        yes_btn = Button(text='Yes', background_color=(0.2, 0.8, 0.2, 1))
        no_btn = Button(text='No', background_color=(0.8, 0.2, 0.2, 1))
        
        yes_btn.bind(on_press=lambda x: self.confirm(callback))
        no_btn.bind(on_press=self.dismiss)
        
        button_layout.add_widget(no_btn)
        button_layout.add_widget(yes_btn)
        
        content.add_widget(button_layout)
        self.content = content
    
    def confirm(self, callback):
        self.dismiss()
        callback()


class InfoPopup(Popup):
    """Information popup"""
    def __init__(self, title, message, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.5, 0.3)
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Message
        content.add_widget(Label(
            text=message,
            text_size=(None, None),
            halign='center'
        ))
        
        # OK Button
        ok_btn = Button(text='OK', size_hint_y=None, height=dp(50))
        ok_btn.bind(on_press=self.dismiss)
        
        content.add_widget(ok_btn)
        self.content = content


class GameConfigPopup(Popup):
    """Popup for adding/editing game configuration"""
    def __init__(self, title, callback, game_id="", game_info=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.8, 0.8)
        self.auto_dismiss = False
        
        self.callback = callback
        game_info = game_info or {}
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Game ID
        content.add_widget(Label(text='Game ID (short name, no spaces):', 
                                size_hint_y=None, height=dp(30), halign='left'))
        self.game_id_input = TextInput(
            text=game_id,
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(self.game_id_input)
        
        # Game Name
        content.add_widget(Label(text='Game Name:', 
                                size_hint_y=None, height=dp(30), halign='left'))
        self.name_input = TextInput(
            text=game_info.get('name', ''),
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(self.name_input)
        
        # Save Path
        content.add_widget(Label(text='Save Directory Path:', 
                                size_hint_y=None, height=dp(30), halign='left'))
        save_path_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.save_path_input = TextInput(
            text=game_info.get('save_path', ''),
            multiline=False
        )
        browse_save_btn = Button(text='Browse', size_hint_x=None, width=dp(80))
        browse_save_btn.bind(on_press=self.browse_save_path)
        save_path_layout.add_widget(self.save_path_input)
        save_path_layout.add_widget(browse_save_btn)
        content.add_widget(save_path_layout)
        
        # Backup Path
        content.add_widget(Label(text='Backup Directory Path (optional):', 
                                size_hint_y=None, height=dp(30), halign='left'))
        backup_path_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.backup_path_input = TextInput(
            text=game_info.get('backup_path', ''),
            multiline=False
        )
        browse_backup_btn = Button(text='Browse', size_hint_x=None, width=dp(80))
        browse_backup_btn.bind(on_press=self.browse_backup_path)
        backup_path_layout.add_widget(self.backup_path_input)
        backup_path_layout.add_widget(browse_backup_btn)
        content.add_widget(backup_path_layout)
        
        # Description
        content.add_widget(Label(text='Description (optional):', 
                                size_hint_y=None, height=dp(30), halign='left'))
        self.description_input = TextInput(
            text=game_info.get('description', ''),
            multiline=True,
            size_hint_y=None,
            height=dp(100)
        )
        content.add_widget(self.description_input)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        ok_btn = Button(text='OK', background_color=(0.2, 0.8, 0.2, 1))
        cancel_btn = Button(text='Cancel', background_color=(0.8, 0.2, 0.2, 1))
        
        ok_btn.bind(on_press=self.ok_clicked)
        cancel_btn.bind(on_press=self.dismiss)
        
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(ok_btn)
        
        content.add_widget(button_layout)
        self.content = content
    
    def browse_save_path(self, instance):
        # Simple implementation - in a real app you'd use a file browser
        pass
    
    def browse_backup_path(self, instance):
        # Simple implementation - in a real app you'd use a file browser
        pass
    
    def ok_clicked(self, instance):
        # Validate input
        game_id = self.game_id_input.text.strip()
        name = self.name_input.text.strip()
        save_path = self.save_path_input.text.strip()
        backup_path = self.backup_path_input.text.strip()
        description = self.description_input.text.strip()
        
        if not game_id:
            InfoPopup("Error", "Game ID is required").open()
            return
        
        if ' ' in game_id:
            InfoPopup("Error", "Game ID cannot contain spaces").open()
            return
        
        if not name:
            InfoPopup("Error", "Game name is required").open()
            return
        
        if not save_path:
            InfoPopup("Error", "Save path is required").open()
            return
        
        result = (game_id, {
            "name": name,
            "save_path": save_path,
            "backup_path": backup_path,
            "description": description
        })
        
        self.dismiss()
        self.callback(result)


class BackupManagerGUI(BoxLayout):
    """Main GUI class for the backup manager"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Load configuration
        self.config_path = Path(__file__).parent / "games_config.json"
        self.config = load_games_config(self.config_path)
        
        # Current manager instance
        self.manager = None
        self.current_game_id = None
        self.current_game_info = None
        
        # Build UI
        self.build_ui()
        self.update_game_list()
        
        # Setup periodic refresh
        Clock.schedule_interval(self.refresh_backup_list, 30)
    
    def build_ui(self):
        """Build the main UI"""
        # Title
        title = Label(
            text='🎮 Save Game Backup Manager',
            size_hint_y=None,
            height=dp(50),
            font_size='20sp'
        )
        self.add_widget(title)
        
        # Create tabbed panel
        self.tab_panel = TabbedPanel(
            do_default_tab=False,
            tab_height=dp(50)
        )
        
        # Backup tab
        backup_tab = TabbedPanelItem(text='Backup Manager')
        backup_tab.content = self.create_backup_tab()
        self.tab_panel.add_widget(backup_tab)
        
        # Config tab
        config_tab = TabbedPanelItem(text='Game Configuration')
        config_tab.content = self.create_config_tab()
        self.tab_panel.add_widget(config_tab)
        
        self.add_widget(self.tab_panel)
        
        # Progress bar (initially hidden)
        self.progress_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=0,
            spacing=dp(5)
        )
        
        self.progress_label = Label(text='', size_hint_y=None, height=dp(30))
        self.progress_bar = ProgressBar(size_hint_y=None, height=dp(20))
        
        self.progress_layout.add_widget(self.progress_label)
        self.progress_layout.add_widget(self.progress_bar)
        
        self.add_widget(self.progress_layout)
    
    def create_backup_tab(self):
        """Create the backup management tab content"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Game selection
        game_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        game_layout.add_widget(Label(text='Select Game:', size_hint_y=None, height=dp(30)))
        
        self.game_spinner = Spinner(
            text='Select a game...',
            values=[],
            size_hint_y=None,
            height=dp(40)
        )
        self.game_spinner.bind(text=self.on_game_selected)
        game_layout.add_widget(self.game_spinner)
        
        content.add_widget(game_layout)
        
        # Game info
        self.info_label = Label(
            text='',
            text_size=(None, None),
            size_hint_y=None,
            height=dp(100),
            halign='left'
        )
        content.add_widget(self.info_label)
        
        # Backup controls
        backup_controls = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120))
        
        backup_controls.add_widget(Label(text='Backup Description (optional):', 
                                        size_hint_y=None, height=dp(30)))
        
        self.description_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        backup_controls.add_widget(self.description_input)
        
        # Action buttons
        action_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        self.backup_btn = Button(
            text='💾 Create Backup',
            background_color=(0.2, 0.8, 0.2, 1),
            disabled=True
        )
        self.backup_btn.bind(on_press=self.create_backup)
        
        self.refresh_btn = Button(
            text='🔄 Refresh',
            disabled=True
        )
        self.refresh_btn.bind(on_press=lambda x: self.refresh_backup_list())
        
        self.cleanup_btn = Button(
            text='🧹 Cleanup',
            background_color=(0.2, 0.6, 0.8, 1),
            disabled=True
        )
        self.cleanup_btn.bind(on_press=self.cleanup_backups)
        
        action_layout.add_widget(self.backup_btn)
        action_layout.add_widget(self.refresh_btn)
        action_layout.add_widget(self.cleanup_btn)
        
        backup_controls.add_widget(action_layout)
        content.add_widget(backup_controls)
        
        # Backup list
        content.add_widget(Label(text='Available Backups:', size_hint_y=None, height=dp(30)))
        
        # Scrollable backup list
        scroll = ScrollView()
        self.backup_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.backup_list.bind(minimum_height=self.backup_list.setter('height'))
        
        scroll.add_widget(self.backup_list)
        content.add_widget(scroll)
        
        return content
    
    def create_config_tab(self):
        """Create the configuration tab content"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Games list
        content.add_widget(Label(text='Configured Games:', size_hint_y=None, height=dp(30)))
        
        # Scrollable games list
        scroll = ScrollView(size_hint=(1, 0.7))
        self.games_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.games_list.bind(minimum_height=self.games_list.setter('height'))
        
        scroll.add_widget(self.games_list)
        content.add_widget(scroll)
        
        # Config buttons
        config_btn_layout = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=dp(50),
            spacing=dp(10)
        )
        
        add_btn = Button(text='➕ Add Game', background_color=(0.2, 0.8, 0.2, 1))
        add_btn.bind(on_press=self.add_game)
        
        refresh_config_btn = Button(text='🔄 Refresh')
        refresh_config_btn.bind(on_press=lambda x: self.update_games_list())
        
        config_btn_layout.add_widget(add_btn)
        config_btn_layout.add_widget(refresh_config_btn)
        
        content.add_widget(config_btn_layout)
        
        # Settings
        settings_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120))
        
        settings_layout.add_widget(Label(text='Global Settings:', size_hint_y=None, height=dp(30)))
        
        # Max backups
        max_backups_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        max_backups_layout.add_widget(Label(text='Default Max Backups:'))
        
        self.max_backups_input = TextInput(
            text=str(self.config.get("settings", {}).get("default_max_backups", 10)),
            multiline=False,
            size_hint_x=None,
            width=dp(100)
        )
        max_backups_layout.add_widget(self.max_backups_input)
        
        settings_layout.add_widget(max_backups_layout)
        
        # Save settings button
        save_settings_btn = Button(
            text='💾 Save Settings',
            size_hint_y=None,
            height=dp(40),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        save_settings_btn.bind(on_press=self.save_settings)
        
        settings_layout.add_widget(save_settings_btn)
        
        content.add_widget(settings_layout)
        
        self.update_games_list()
        
        return content
    
    def update_game_list(self):
        """Update the game spinner list"""
        games = list_games(self.config)
        game_names = [f"{game_info.get('name', game_id)} ({game_id})" 
                     for game_id, game_info in games]
        
        self.game_spinner.values = game_names
        
        if game_names and self.game_spinner.text == 'Select a game...':
            self.game_spinner.text = game_names[0]
            self.on_game_selected(self.game_spinner, game_names[0])
    
    def on_game_selected(self, spinner, text):
        """Handle game selection"""
        if text == 'Select a game...':
            return
        
        # Extract game ID from selection
        try:
            game_id = text.split(" (")[-1].rstrip(")")
            game_info = self.config.get("games", {}).get(game_id)
            
            if not game_info:
                return
            
            self.current_game_id = game_id
            self.current_game_info = game_info
            
            # Update info display
            self.update_game_info()
            
            # Initialize backup manager
            self.initialize_backup_manager()
            
            # Refresh backup list
            self.refresh_backup_list()
            
            # Update button states
            self.update_button_states()
            
        except Exception as e:
            Logger.error(f"BackupManager: Error selecting game: {e}")
    
    def update_game_info(self):
        """Update the game information display"""
        if not self.current_game_info:
            return
        
        info_text = f"Game: {self.current_game_info.get('name', 'Unknown')}\n"
        info_text += f"Save Path: {self.current_game_info.get('save_path', 'Unknown')}\n"
        info_text += f"Backup Path: {self.current_game_info.get('backup_path', 'Default')}"
        
        description = self.current_game_info.get('description', '')
        if description:
            info_text += f"\nDescription: {description}"
        
        self.info_label.text = info_text
        self.info_label.text_size = (self.info_label.width, None)
    
    def initialize_backup_manager(self):
        """Initialize the backup manager for the selected game"""
        if not self.current_game_info:
            return
        
        try:
            save_dir = expand_path(self.current_game_info["save_path"])
            backup_dir = None
            
            if "backup_path" in self.current_game_info and self.current_game_info["backup_path"]:
                backup_dir = expand_path(self.current_game_info["backup_path"])
            else:
                default_backup_path = self.config.get("settings", {}).get("default_backup_path")
                if default_backup_path:
                    backup_dir = expand_path(default_backup_path)
            
            max_backups = self.config.get("settings", {}).get("default_max_backups", 10)
            game_name = self.current_game_info.get("name")
            
            self.manager = SaveBackupManager(save_dir, backup_dir, max_backups, game_name)
            
        except Exception as e:
            InfoPopup("Error", f"Failed to initialize backup manager: {e}").open()
            self.manager = None
    
    def update_button_states(self):
        """Update the state of action buttons"""
        has_manager = self.manager is not None
        
        self.backup_btn.disabled = not has_manager
        self.refresh_btn.disabled = not has_manager
        self.cleanup_btn.disabled = not has_manager
    
    def refresh_backup_list(self, dt=None):
        """Refresh the backup list display"""
        # Clear current items
        self.backup_list.clear_widgets()
        
        if not self.manager:
            self.update_button_states()
            return
        
        try:
            backups = self.manager._get_backup_list()
            
            if not backups:
                self.backup_list.add_widget(Label(
                    text='No backups found',
                    size_hint_y=None,
                    height=dp(50)
                ))
                return
            
            for backup_path in backups:
                backup_path_obj = Path(backup_path)
                backup_name = backup_path_obj.name
                
                # Extract timestamp
                timestamp_str = backup_name.replace("backup_", "")
                try:
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    date_str = timestamp.strftime("%Y-%m-%d")
                    time_str = timestamp.strftime("%H:%M:%S")
                    
                    # Calculate age
                    age = datetime.datetime.now() - timestamp
                    if age.days > 0:
                        age_str = f"{age.days} days ago"
                    elif age.seconds > 3600:
                        age_str = f"{age.seconds // 3600} hours ago"
                    elif age.seconds > 60:
                        age_str = f"{age.seconds // 60} minutes ago"
                    else:
                        age_str = "Just now"
                    
                except ValueError:
                    date_str = "Unknown"
                    time_str = "Unknown"
                    age_str = "Unknown"
                
                # Get size
                try:
                    size = get_directory_size(backup_path_obj)
                    size_str = format_file_size(size)
                except Exception:
                    size_str = "Unknown"
                
                # Get description
                desc_file = backup_path_obj / ".backup_description"
                description = ""
                if desc_file.exists():
                    try:
                        description = desc_file.read_text(encoding='utf-8').strip()
                    except Exception:
                        pass
                
                # Create backup data
                backup_data = {
                    'name': backup_name,
                    'path': backup_path,
                    'date': date_str,
                    'time': time_str,
                    'age': age_str,
                    'size': size_str,
                    'description': description,
                    'index': backups.index(backup_path) + 1
                }
                
                # Create backup item widget
                backup_item = BackupItemWidget(backup_data, self)
                self.backup_list.add_widget(backup_item)
        
        except Exception as e:
            Logger.error(f"BackupManager: Failed to refresh backup list: {e}")
        
        self.update_button_states()
    
    def create_backup(self, instance):
        """Create a new backup"""
        if not self.manager:
            InfoPopup("Error", "No game selected").open()
            return
        
        description = self.description_input.text.strip() or None
        
        def backup_thread():
            try:
                if not self.manager:
                    return
                
                Clock.schedule_once(lambda dt: self.show_progress("Creating backup..."))
                result = self.manager.create_backup(description)
                Clock.schedule_once(lambda dt: self.hide_progress())
                
                if result:
                    Clock.schedule_once(lambda dt: InfoPopup("Success", "Backup created successfully!").open())
                    Clock.schedule_once(lambda dt: self.refresh_backup_list())
                    Clock.schedule_once(lambda dt: setattr(self.description_input, 'text', ''))
                else:
                    Clock.schedule_once(lambda dt: InfoPopup("Error", "Failed to create backup").open())
            except Exception as e:
                Clock.schedule_once(lambda dt: self.hide_progress())
                Clock.schedule_once(lambda dt: InfoPopup("Error", f"Backup failed: {e}").open())
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def restore_backup(self, backup_data):
        """Restore the selected backup"""
        if not self.manager:
            InfoPopup("Error", "No game selected").open()
            return
        
        def restore_callback():
            def restore_thread():
                try:
                    if not self.manager:
                        return
                    
                    Clock.schedule_once(lambda dt: self.show_progress("Restoring backup..."))
                    success = self.manager.restore_backup(backup_data['index'], skip_confirmation=True)
                    Clock.schedule_once(lambda dt: self.hide_progress())
                    
                    if success:
                        Clock.schedule_once(lambda dt: InfoPopup("Success", "Backup restored successfully!").open())
                    else:
                        Clock.schedule_once(lambda dt: InfoPopup("Error", "Failed to restore backup").open())
                        
                except Exception as e:
                    Clock.schedule_once(lambda dt: self.hide_progress())
                    Clock.schedule_once(lambda dt: InfoPopup("Error", f"Restore failed: {e}").open())
            
            threading.Thread(target=restore_thread, daemon=True).start()
        
        ConfirmationPopup(
            "Confirm Restore",
            f"This will overwrite your current save files with '{backup_data['name']}'.\n\nAre you sure you want to continue?",
            restore_callback
        ).open()
    
    def delete_backup(self, backup_data):
        """Delete the selected backup"""
        if not self.manager:
            InfoPopup("Error", "No game selected").open()
            return
        
        def delete_callback():
            def delete_thread():
                try:
                    if not self.manager:
                        return
                    
                    success = self.manager.delete_backup(backup_data['index'], skip_confirmation=True)
                    
                    if success:
                        Clock.schedule_once(lambda dt: InfoPopup("Success", "Backup deleted successfully!").open())
                        Clock.schedule_once(lambda dt: self.refresh_backup_list())
                    else:
                        Clock.schedule_once(lambda dt: InfoPopup("Error", "Failed to delete backup").open())
                        
                except Exception as e:
                    Clock.schedule_once(lambda dt: InfoPopup("Error", f"Delete failed: {e}").open())
            
            threading.Thread(target=delete_thread, daemon=True).start()
        
        ConfirmationPopup(
            "Confirm Delete",
            f"Are you sure you want to permanently delete '{backup_data['name']}'?",
            delete_callback
        ).open()
    
    def cleanup_backups(self, instance):
        """Clean up old backups"""
        if not self.manager:
            InfoPopup("Error", "No game selected").open()
            return
        
        # Get current backup count
        backups = self.manager._get_backup_list()
        max_backups = self.manager.max_backups
        
        if len(backups) <= max_backups:
            InfoPopup("Info", f"Only {len(backups)} backup(s) found. No cleanup needed.").open()
            return
        
        to_delete = len(backups) - max_backups
        
        def cleanup_callback():
            def cleanup_thread():
                try:
                    if not self.manager:
                        return
                    self.manager.cleanup_backups()
                    Clock.schedule_once(lambda dt: InfoPopup("Success", "Old backups cleaned up successfully!").open())
                    Clock.schedule_once(lambda dt: self.refresh_backup_list())
                except Exception as e:
                    Clock.schedule_once(lambda dt: InfoPopup("Error", f"Cleanup failed: {e}").open())
            
            threading.Thread(target=cleanup_thread, daemon=True).start()
        
        ConfirmationPopup(
            "Confirm Cleanup",
            f"This will delete {to_delete} old backup(s), keeping the {max_backups} most recent.\n\nContinue?",
            cleanup_callback
        ).open()
    
    def show_progress(self, message):
        """Show progress bar with message"""
        self.progress_label.text = message
        self.progress_layout.height = dp(60)
        self.progress_bar.value = 0
        # Animate progress bar
        def animate_progress(dt):
            self.progress_bar.value = (self.progress_bar.value + 10) % 100
        Clock.schedule_interval(animate_progress, 0.1)
    
    def hide_progress(self):
        """Hide progress bar"""
        Clock.unschedule(lambda dt: None)  # Stop progress animation
        self.progress_layout.height = 0
        self.progress_label.text = ''
    
    def update_games_list(self):
        """Update the games configuration list"""
        # Clear current items
        self.games_list.clear_widgets()
        
        # Reload config
        self.config = load_games_config(self.config_path)
        
        # Populate list
        games = list_games(self.config)
        
        if not games:
            self.games_list.add_widget(Label(
                text='No games configured',
                size_hint_y=None,
                height=dp(50)
            ))
            return
        
        for game_id, game_info in games:
            game_item = self.create_game_item(game_id, game_info)
            self.games_list.add_widget(game_item)
        
        # Update game dropdown
        self.update_game_list()
    
    def create_game_item(self, game_id, game_info):
        """Create a widget for a game configuration item"""
        item = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(10),
            padding=dp(10)
        )
        
        # Game info
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        info_layout.add_widget(Label(
            text=f"[b]{game_info.get('name', game_id)}[/b] ({game_id})",
            markup=True,
            text_size=(None, None),
            halign='left',
            size_hint_y=0.5
        ))
        info_layout.add_widget(Label(
            text=f"Save: {game_info.get('save_path', '')}",
            text_size=(None, None),
            halign='left',
            size_hint_y=0.5
        ))
        
        item.add_widget(info_layout)
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_x=0.3, spacing=dp(5))
        
        edit_btn = Button(
            text='Edit',
            background_color=(0.8, 0.8, 0.2, 1)
        )
        edit_btn.bind(on_press=lambda x: self.edit_game(game_id, game_info))
        
        remove_btn = Button(
            text='Remove',
            background_color=(1, 0.2, 0.2, 1)
        )
        remove_btn.bind(on_press=lambda x: self.remove_game(game_id, game_info))
        
        button_layout.add_widget(edit_btn)
        button_layout.add_widget(remove_btn)
        
        item.add_widget(button_layout)
        
        return item
    
    def add_game(self, instance):
        """Add a new game configuration"""
        def callback(result):
            if result:
                game_id, game_data = result
                
                # Check if game ID already exists
                if game_id in self.config.get("games", {}):
                    InfoPopup("Error", f"Game ID '{game_id}' already exists").open()
                    return
                
                # Add to config
                if "games" not in self.config:
                    self.config["games"] = {}
                
                self.config["games"][game_id] = game_data
                save_games_config(self.config_path, self.config)
                
                InfoPopup("Success", f"Game '{game_data['name']}' added successfully!").open()
                self.update_games_list()
        
        GameConfigPopup("Add Game", callback).open()
    
    def edit_game(self, game_id, game_info):
        """Edit the selected game configuration"""
        def callback(result):
            if result:
                new_game_id, game_data = result
                
                # If game ID changed, remove old and add new
                if new_game_id != game_id:
                    if new_game_id in self.config.get("games", {}):
                        InfoPopup("Error", f"Game ID '{new_game_id}' already exists").open()
                        return
                    del self.config["games"][game_id]
                    self.config["games"][new_game_id] = game_data
                else:
                    self.config["games"][game_id] = game_data
                
                save_games_config(self.config_path, self.config)
                
                InfoPopup("Success", f"Game '{game_data['name']}' updated successfully!").open()
                self.update_games_list()
        
        GameConfigPopup("Edit Game", callback, game_id, game_info).open()
    
    def remove_game(self, game_id, game_info):
        """Remove the selected game configuration"""
        game_name = game_info.get("name", game_id)
        
        def remove_callback():
            del self.config["games"][game_id]
            save_games_config(self.config_path, self.config)
            
            InfoPopup("Success", f"Game '{game_name}' removed successfully!").open()
            self.update_games_list()
        
        ConfirmationPopup(
            "Confirm Remove",
            f"Are you sure you want to remove '{game_name}' from the configuration?",
            remove_callback
        ).open()
    
    def save_settings(self, instance):
        """Save global settings"""
        try:
            max_backups = int(self.max_backups_input.text)
            
            if "settings" not in self.config:
                self.config["settings"] = {}
            
            self.config["settings"]["default_max_backups"] = max_backups
            
            save_games_config(self.config_path, self.config)
            
            InfoPopup("Success", "Settings saved successfully!").open()
            
            # Reinitialize backup manager if needed
            if self.manager:
                self.manager.max_backups = max_backups
            
        except ValueError:
            InfoPopup("Error", "Invalid value for max backups").open()
        except Exception as e:
            InfoPopup("Error", f"Failed to save settings: {e}").open()


class BackupManagerApp(App):
    """Main Kivy application"""
    
    def build(self):
        self.title = "Save Game Backup Manager"
        return BackupManagerGUI()


def main():
    BackupManagerApp().run()


if __name__ == "__main__":
    main()
