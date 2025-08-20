#!/usr/bin/env python3
"""
Save Game Backup Manager - DearPyGui Version
A user-friendly graphical interface for the backup.py CLI tool using DearPyGui
"""

import dearpygui.dearpygui as dpg
import os
import sys
import threading
import datetime
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

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

class BackupManagerGUI:
    def __init__(self):
        self.config_path = Path(__file__).parent / "games_config.json"
        self.config = load_games_config(self.config_path)
        
        # Current manager instance
        self.manager = None
        self.current_game_id = None
        self.current_game_info = None
        
        # GUI state
        self.selected_backup_path = None
        self.is_operation_running = False
        
        # Initialize DearPyGui
        dpg.create_context()
        self.setup_themes()
        self.create_gui()
        
        # Setup viewport
        dpg.create_viewport(title="🎮 Save Game Backup Manager", width=1000, height=800)
        dpg.setup_dearpygui()
        
        # Update initial data
        self.update_game_list()
        self.start_periodic_refresh()
    
    def setup_themes(self):
        """Setup custom themes for different button types"""
        # Success theme (green)
        with dpg.theme() as success_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 150, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 180, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 120, 0, 255))
        self.success_theme = success_theme
        
        # Warning theme (orange)
        with dpg.theme() as warning_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 100, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (230, 120, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (170, 80, 0, 255))
        self.warning_theme = warning_theme
        
        # Danger theme (red)
        with dpg.theme() as danger_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 0, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (230, 0, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (170, 0, 0, 255))
        self.danger_theme = danger_theme
        
        # Primary theme (blue)
        with dpg.theme() as primary_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 100, 200, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 120, 230, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 80, 170, 255))
        self.primary_theme = primary_theme
    
    def create_gui(self):
        """Create the main GUI layout"""
        with dpg.window(label="Backup Manager", tag="main_window"):
            
            # Create tab bar
            with dpg.tab_bar(label="Main Tabs"):
                
                # Backup Management Tab
                with dpg.tab(label="Backup Manager"):
                    self.create_backup_tab()
                
                # Configuration Tab
                with dpg.tab(label="Game Configuration"):
                    self.create_config_tab()
        
        dpg.set_primary_window("main_window", True)
    
    def create_backup_tab(self):
        """Create the backup management interface"""
        
        # Game Selection Group
        with dpg.group():
            dpg.add_text("Game Selection")
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                dpg.add_text("Select Game:")
                dpg.add_combo(items=[], tag="game_combo", width=400, 
                             callback=self.on_game_selected)
        
        dpg.add_spacer(height=10)
        
        # Game Information Group
        with dpg.group():
            dpg.add_text("Game Information")
            dpg.add_separator()
            dpg.add_text("", tag="game_info_text", wrap=800)
        
        dpg.add_spacer(height=10)
        
        # Actions Group
        with dpg.group():
            dpg.add_text("Actions")
            dpg.add_separator()
            
            # Backup description
            with dpg.group(horizontal=True):
                dpg.add_text("Backup Description (optional):")
            dpg.add_input_text(tag="backup_description", width=400)
            
            dpg.add_spacer(height=5)
            
            # Action buttons
            with dpg.group(horizontal=True):
                backup_btn = dpg.add_button(label="💾 Create Backup", 
                                          callback=self.create_backup,
                                          tag="create_backup_btn")
                dpg.bind_item_theme(backup_btn, self.success_theme)
                
                dpg.add_button(label="🔄 Refresh", callback=self.refresh_backup_list)
        
        dpg.add_spacer(height=10)
        
        # Backup List Group
        with dpg.group():
            dpg.add_text("Available Backups")
            dpg.add_separator()
            
            # Create table for backups
            with dpg.table(header_row=True, tag="backup_table", 
                          borders_outerH=True, borders_innerV=True, borders_innerH=True,
                          borders_outerV=True, scrollY=True, height=300):
                dpg.add_table_column(label="Backup Name", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Date", width_fixed=True, init_width_or_weight=100)
                dpg.add_table_column(label="Time", width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label="Age", width_fixed=True, init_width_or_weight=100)
                dpg.add_table_column(label="Size", width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label="Description", width_stretch=True)
            
            dpg.add_spacer(height=10)
            
            # Backup action buttons
            with dpg.group(horizontal=True):
                restore_btn = dpg.add_button(label="🔄 Restore Selected", 
                                           callback=self.restore_backup,
                                           tag="restore_backup_btn", enabled=False)
                dpg.bind_item_theme(restore_btn, self.warning_theme)
                
                delete_btn = dpg.add_button(label="🗑️ Delete Selected", 
                                          callback=self.delete_backup,
                                          tag="delete_backup_btn", enabled=False)
                dpg.bind_item_theme(delete_btn, self.danger_theme)
                
                cleanup_btn = dpg.add_button(label="🧹 Cleanup Old Backups", 
                                           callback=self.cleanup_backups,
                                           tag="cleanup_backups_btn", enabled=False)
                dpg.bind_item_theme(cleanup_btn, self.primary_theme)
        
        # Progress indicator (initially hidden)
        dpg.add_text("", tag="progress_text", show=False)
        dpg.add_progress_bar(tag="progress_bar", show=False, width=800)
    
    def create_config_tab(self):
        """Create the configuration management interface"""
        
        # Games Configuration Group
        with dpg.group():
            dpg.add_text("Configured Games")
            dpg.add_separator()
            
            # Games table
            with dpg.table(header_row=True, tag="games_table", 
                          borders_outerH=True, borders_innerV=True, borders_innerH=True,
                          borders_outerV=True, scrollY=True, height=250):
                dpg.add_table_column(label="Game ID", width_fixed=True, init_width_or_weight=100)
                dpg.add_table_column(label="Name", width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column(label="Save Path", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Backup Path", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Description", width_stretch=True)
            
            dpg.add_spacer(height=10)
            
            # Config action buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="➕ Add Game", callback=self.show_add_game_dialog)
                dpg.add_button(label="✏️ Edit Selected", callback=self.show_edit_game_dialog, 
                              tag="edit_game_btn", enabled=False)
                dpg.add_button(label="🗑️ Remove Selected", callback=self.remove_game, 
                              tag="remove_game_btn", enabled=False)
                dpg.add_button(label="🔄 Refresh", callback=self.update_games_table)
        
        dpg.add_spacer(height=20)
        
        # Global Settings Group
        with dpg.group():
            dpg.add_text("Global Settings")
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                dpg.add_text("Default Max Backups:")
                dpg.add_input_int(tag="max_backups_input", 
                                 default_value=self.config.get("settings", {}).get("default_max_backups", 10),
                                 min_value=1, max_value=100, width=100)
            
            dpg.add_spacer(height=5)
            
            with dpg.group(horizontal=True):
                dpg.add_text("Default Backup Path:")
            dpg.add_input_text(tag="backup_path_input", 
                              default_value=self.config.get("settings", {}).get("default_backup_path", ""),
                              width=400)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Browse", callback=self.browse_backup_path)
                dpg.add_button(label="💾 Save Settings", callback=self.save_settings)
        
        # Update the games table
        self.update_games_table()
    
    def show_modal_dialog(self, title: str, message: str, callback=None):
        """Show a modal dialog"""
        with dpg.window(label=title, modal=True, tag="modal_dialog", width=400, height=150):
            dpg.add_text(message, wrap=350)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                if callback:
                    dpg.add_button(label="OK", callback=lambda: (callback(), dpg.delete_item("modal_dialog")))
                    dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("modal_dialog"))
                else:
                    dpg.add_button(label="OK", callback=lambda: dpg.delete_item("modal_dialog"))
    
    def show_confirmation_dialog(self, title: str, message: str, confirm_callback):
        """Show a confirmation dialog"""
        with dpg.window(label=title, modal=True, tag="confirm_dialog", width=400, height=150):
            dpg.add_text(message, wrap=350)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Yes", callback=lambda: (confirm_callback(), dpg.delete_item("confirm_dialog")))
                dpg.add_button(label="No", callback=lambda: dpg.delete_item("confirm_dialog"))
    
    def show_error_dialog(self, title: str, message: str):
        """Show an error dialog"""
        self.show_modal_dialog(title, message)
    
    def show_info_dialog(self, title: str, message: str):
        """Show an info dialog"""
        self.show_modal_dialog(title, message)
    
    def update_game_list(self):
        """Update the game dropdown list"""
        games = list_games(self.config)
        game_names = [f"{game_info.get('name', game_id)} ({game_id})" 
                     for game_id, game_info in games]
        
        dpg.configure_item("game_combo", items=game_names)
        
        if game_names and not dpg.get_value("game_combo"):
            dpg.set_value("game_combo", game_names[0])
            self.on_game_selected()
    
    def on_game_selected(self, sender=None, app_data=None):
        """Handle game selection"""
        selection = dpg.get_value("game_combo")
        if not selection:
            return
        
        # Extract game ID from selection
        game_id = selection.split(" (")[-1].rstrip(")")
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
    
    def update_game_info(self):
        """Update the game information display"""
        if not self.current_game_info:
            return
        
        info_text = f"Game: {self.current_game_info.get('name', 'Unknown')}\n"
        info_text += f"Save Path: {self.current_game_info.get('save_path', 'Unknown')}\n"
        info_text += f"Backup Path: {self.current_game_info.get('backup_path', 'Default')}\n"
        
        description = self.current_game_info.get('description', '')
        if description:
            info_text += f"Description: {description}"
        
        dpg.set_value("game_info_text", info_text)
    
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
            self.show_error_dialog("Error", f"Failed to initialize backup manager: {e}")
            self.manager = None
    
    def update_button_states(self):
        """Update the state of action buttons"""
        has_manager = self.manager is not None
        has_selection = self.selected_backup_path is not None
        
        dpg.configure_item("create_backup_btn", enabled=has_manager and not self.is_operation_running)
        dpg.configure_item("restore_backup_btn", enabled=has_manager and has_selection and not self.is_operation_running)
        dpg.configure_item("delete_backup_btn", enabled=has_manager and has_selection and not self.is_operation_running)
        dpg.configure_item("cleanup_backups_btn", enabled=has_manager and not self.is_operation_running)
    
    def refresh_backup_list(self):
        """Refresh the backup list display"""
        # Clear current table rows
        if dpg.does_item_exist("backup_table"):
            dpg.delete_item("backup_table", children_only=True)
        
        if not self.manager:
            self.update_button_states()
            return
        
        try:
            backups = self.manager._get_backup_list()
            
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
                
                # Add table row
                with dpg.table_row(parent="backup_table"):
                    dpg.add_selectable(label=backup_name, 
                                     callback=lambda s, a, u: self.on_backup_selected(u),
                                     user_data=backup_path)
                    dpg.add_text(date_str)
                    dpg.add_text(time_str)
                    dpg.add_text(age_str)
                    dpg.add_text(size_str)
                    dpg.add_text(description)
        
        except Exception as e:
            self.show_error_dialog("Error", f"Failed to refresh backup list: {e}")
        
        self.update_button_states()
    
    def on_backup_selected(self, backup_path):
        """Handle backup selection"""
        self.selected_backup_path = backup_path
        self.update_button_states()
    
    def create_backup(self):
        """Create a new backup"""
        if not self.manager or self.is_operation_running:
            return
        
        description = dpg.get_value("backup_description").strip() or None
        
        def backup_thread():
            try:
                self.is_operation_running = True
                dpg.set_value("progress_text", "Creating backup...")
                dpg.show_item("progress_text")
                dpg.show_item("progress_bar")
                
                if self.manager:
                    result = self.manager.create_backup(description)
                    
                    dpg.hide_item("progress_bar")
                    dpg.hide_item("progress_text")
                    
                    if result:
                        self.show_info_dialog("Success", "Backup created successfully!")
                        dpg.set_value("backup_description", "")
                        self.refresh_backup_list()
                    else:
                        self.show_error_dialog("Error", "Failed to create backup")
            except Exception as e:
                dpg.hide_item("progress_bar")
                dpg.hide_item("progress_text")
                self.show_error_dialog("Error", f"Backup failed: {e}")
            finally:
                self.is_operation_running = False
                self.update_button_states()
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def restore_backup(self):
        """Restore the selected backup"""
        if not self.manager or not self.selected_backup_path or self.is_operation_running:
            return
        
        backup_name = Path(self.selected_backup_path).name
        
        def do_restore():
            def restore_thread():
                try:
                    self.is_operation_running = True
                    dpg.set_value("progress_text", "Restoring backup...")
                    dpg.show_item("progress_text")
                    dpg.show_item("progress_bar")
                    
                    # Get backup index
                    if self.manager and self.selected_backup_path:
                        backups = self.manager._get_backup_list()
                        try:
                            backup_index = backups.index(self.selected_backup_path) + 1  # Convert to 1-based index
                            
                            success = self.manager.restore_backup(backup_index, skip_confirmation=True)
                            
                            dpg.hide_item("progress_bar")
                            dpg.hide_item("progress_text")
                            
                            if success:
                                self.show_info_dialog("Success", "Backup restored successfully!")
                            else:
                                self.show_error_dialog("Error", "Failed to restore backup")
                        except ValueError:
                            dpg.hide_item("progress_bar")
                            dpg.hide_item("progress_text")
                            self.show_error_dialog("Error", "Could not find backup in list")
                        
                except Exception as e:
                    dpg.hide_item("progress_bar")
                    dpg.hide_item("progress_text")
                    self.show_error_dialog("Error", f"Restore failed: {e}")
                finally:
                    self.is_operation_running = False
                    self.update_button_states()
            
            threading.Thread(target=restore_thread, daemon=True).start()
        
        self.show_confirmation_dialog(
            "Confirm Restore",
            f"This will overwrite your current save files with '{backup_name}'.\n\nAre you sure you want to continue?",
            do_restore
        )
    
    def delete_backup(self):
        """Delete the selected backup"""
        if not self.manager or not self.selected_backup_path or self.is_operation_running:
            return
        
        backup_name = Path(self.selected_backup_path).name
        
        def do_delete():
            def delete_thread():
                try:
                    self.is_operation_running = True
                    
                    # Get backup index
                    if self.manager and self.selected_backup_path:
                        backups = self.manager._get_backup_list()
                        try:
                            backup_index = backups.index(self.selected_backup_path) + 1  # Convert to 1-based index
                            
                            success = self.manager.delete_backup(backup_index, skip_confirmation=True)
                            
                            if success:
                                self.show_info_dialog("Success", "Backup deleted successfully!")
                                self.selected_backup_path = None
                                self.refresh_backup_list()
                            else:
                                self.show_error_dialog("Error", "Failed to delete backup")
                        except ValueError:
                            self.show_error_dialog("Error", "Could not find backup in list")
                        
                except Exception as e:
                    self.show_error_dialog("Error", f"Delete failed: {e}")
                finally:
                    self.is_operation_running = False
                    self.update_button_states()
            
            threading.Thread(target=delete_thread, daemon=True).start()
        
        self.show_confirmation_dialog(
            "Confirm Delete",
            f"Are you sure you want to permanently delete '{backup_name}'?",
            do_delete
        )
    
    def cleanup_backups(self):
        """Clean up old backups"""
        if not self.manager or self.is_operation_running:
            return
        
        # Get current backup count
        backups = self.manager._get_backup_list()
        max_backups = self.manager.max_backups
        
        if len(backups) <= max_backups:
            self.show_info_dialog("Info", f"Only {len(backups)} backup(s) found. No cleanup needed.")
            return
        
        to_delete = len(backups) - max_backups
        
        def do_cleanup():
            def cleanup_thread():
                try:
                    self.is_operation_running = True
                    if self.manager:
                        self.manager.cleanup_backups()
                        self.show_info_dialog("Success", "Old backups cleaned up successfully!")
                        self.refresh_backup_list()
                except Exception as e:
                    self.show_error_dialog("Error", f"Cleanup failed: {e}")
                finally:
                    self.is_operation_running = False
                    self.update_button_states()
            
            threading.Thread(target=cleanup_thread, daemon=True).start()
        
        self.show_confirmation_dialog(
            "Confirm Cleanup",
            f"This will delete {to_delete} old backup(s), keeping the {max_backups} most recent.\n\nContinue?",
            do_cleanup
        )
    
    def update_games_table(self):
        """Update the games configuration table"""
        # Clear current table rows
        if dpg.does_item_exist("games_table"):
            dpg.delete_item("games_table", children_only=True)
        
        # Reload config
        self.config = load_games_config(self.config_path)
        
        # Populate table
        games = list_games(self.config)
        for game_id, game_info in games:
            name = game_info.get("name", game_id)
            save_path = game_info.get("save_path", "")
            backup_path = game_info.get("backup_path", "")
            description = game_info.get("description", "")
            
            with dpg.table_row(parent="games_table"):
                dpg.add_selectable(label=game_id, 
                                 callback=lambda s, a, u: self.on_game_config_selected(u),
                                 user_data=game_id)
                dpg.add_text(name)
                dpg.add_text(save_path)
                dpg.add_text(backup_path)
                dpg.add_text(description)
        
        # Update game dropdown
        self.update_game_list()
    
    def on_game_config_selected(self, game_id):
        """Handle game configuration selection"""
        self.selected_game_id = game_id
        dpg.configure_item("edit_game_btn", enabled=True)
        dpg.configure_item("remove_game_btn", enabled=True)
    
    def show_add_game_dialog(self):
        """Show dialog to add a new game"""
        self.show_game_config_dialog("Add Game")
    
    def show_edit_game_dialog(self):
        """Show dialog to edit the selected game"""
        if hasattr(self, 'selected_game_id'):
            game_info = self.config.get("games", {}).get(self.selected_game_id, {})
            self.show_game_config_dialog("Edit Game", self.selected_game_id, game_info)
    
    def show_game_config_dialog(self, title, game_id="", game_info=None):
        """Show game configuration dialog"""
        if game_info is None:
            game_info = {}
        
        with dpg.window(label=title, modal=True, tag="game_config_dialog", width=600, height=500):
            
            dpg.add_text("Game ID (short name, no spaces):")
            dpg.add_input_text(tag="dialog_game_id", default_value=game_id, width=400)
            
            dpg.add_spacer(height=10)
            
            dpg.add_text("Game Name:")
            dpg.add_input_text(tag="dialog_game_name", default_value=game_info.get("name", ""), width=400)
            
            dpg.add_spacer(height=10)
            
            dpg.add_text("Save Directory Path:")
            dpg.add_input_text(tag="dialog_save_path", default_value=game_info.get("save_path", ""), width=400)
            dpg.add_button(label="Browse Save Path", callback=self.browse_save_path)
            
            dpg.add_spacer(height=10)
            
            dpg.add_text("Backup Directory Path (optional):")
            dpg.add_input_text(tag="dialog_backup_path", default_value=game_info.get("backup_path", ""), width=400)
            dpg.add_button(label="Browse Backup Path", callback=self.browse_game_backup_path)
            
            dpg.add_spacer(height=10)
            
            dpg.add_text("Description (optional):")
            dpg.add_input_text(tag="dialog_description", default_value=game_info.get("description", ""), 
                              width=400, multiline=True, height=80)
            
            dpg.add_spacer(height=20)
            
            with dpg.group(horizontal=True):
                dpg.add_button(label="OK", callback=lambda: self.save_game_config(title, game_id))
                dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("game_config_dialog"))
    
    def browse_save_path(self):
        """Browse for save directory path"""
        # Note: DearPyGui doesn't have built-in file dialogs, so we'll use a simple text input for now
        # In a production app, you might want to use tkinter.filedialog or a system call
        pass
    
    def browse_game_backup_path(self):
        """Browse for game backup directory path"""
        # Note: DearPyGui doesn't have built-in file dialogs, so we'll use a simple text input for now
        pass
    
    def browse_backup_path(self):
        """Browse for default backup path"""
        # Note: DearPyGui doesn't have built-in file dialogs, so we'll use a simple text input for now
        pass
    
    def save_game_config(self, dialog_title, original_game_id):
        """Save game configuration from dialog"""
        game_id = dpg.get_value("dialog_game_id").strip()
        name = dpg.get_value("dialog_game_name").strip()
        save_path = dpg.get_value("dialog_save_path").strip()
        backup_path = dpg.get_value("dialog_backup_path").strip()
        description = dpg.get_value("dialog_description").strip()
        
        # Validate input
        if not game_id:
            self.show_error_dialog("Error", "Game ID is required")
            return
        
        if ' ' in game_id:
            self.show_error_dialog("Error", "Game ID cannot contain spaces")
            return
        
        if not name:
            self.show_error_dialog("Error", "Game name is required")
            return
        
        if not save_path:
            self.show_error_dialog("Error", "Save path is required")
            return
        
        # Check if game ID already exists (only for new games or changed IDs)
        if dialog_title == "Add Game" or (original_game_id != game_id):
            if game_id in self.config.get("games", {}):
                self.show_error_dialog("Error", f"Game ID '{game_id}' already exists")
                return
        
        # Save to config
        if "games" not in self.config:
            self.config["games"] = {}
        
        # If editing and ID changed, remove old entry
        if dialog_title == "Edit Game" and original_game_id != game_id:
            if original_game_id in self.config["games"]:
                del self.config["games"][original_game_id]
        
        self.config["games"][game_id] = {
            "name": name,
            "save_path": save_path,
            "backup_path": backup_path,
            "description": description
        }
        
        save_games_config(self.config_path, self.config)
        
        action = "added" if dialog_title == "Add Game" else "updated"
        self.show_info_dialog("Success", f"Game '{name}' {action} successfully!")
        
        dpg.delete_item("game_config_dialog")
        self.update_games_table()
    
    def remove_game(self):
        """Remove the selected game configuration"""
        if not hasattr(self, 'selected_game_id'):
            return
        
        game_info = self.config.get("games", {}).get(self.selected_game_id, {})
        game_name = game_info.get("name", self.selected_game_id)
        
        def do_remove():
            del self.config["games"][self.selected_game_id]
            save_games_config(self.config_path, self.config)
            
            self.show_info_dialog("Success", f"Game '{game_name}' removed successfully!")
            self.update_games_table()
            
            # Reset selection
            dpg.configure_item("edit_game_btn", enabled=False)
            dpg.configure_item("remove_game_btn", enabled=False)
        
        self.show_confirmation_dialog(
            "Confirm Remove",
            f"Are you sure you want to remove '{game_name}' from the configuration?",
            do_remove
        )
    
    def save_settings(self):
        """Save global settings"""
        try:
            max_backups = dpg.get_value("max_backups_input")
            backup_path = dpg.get_value("backup_path_input").strip()
            
            if "settings" not in self.config:
                self.config["settings"] = {}
            
            self.config["settings"]["default_max_backups"] = max_backups
            self.config["settings"]["default_backup_path"] = backup_path
            
            save_games_config(self.config_path, self.config)
            
            self.show_info_dialog("Success", "Settings saved successfully!")
            
            # Reinitialize backup manager if needed
            if self.manager:
                self.manager.max_backups = max_backups
            
        except Exception as e:
            self.show_error_dialog("Error", f"Failed to save settings: {e}")
    
    def start_periodic_refresh(self):
        """Start periodic refresh of backup list"""
        def refresh_periodically():
            while True:
                time.sleep(30)  # Refresh every 30 seconds
                if self.manager:
                    try:
                        # We can't safely call GUI functions from threads in DearPyGui
                        # So we'll skip the periodic refresh for now
                        pass
                    except:
                        pass  # GUI might be shutting down
        
        threading.Thread(target=refresh_periodically, daemon=True).start()
    
    def run(self):
        """Run the GUI application"""
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


def main():
    app = BackupManagerGUI()
    app.run()


if __name__ == "__main__":
    main()
