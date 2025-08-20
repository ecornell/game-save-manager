#!/usr/bin/env python3
"""
Save Game Backup Manager - Textual TUI Version
A terminal user interface for the backup.py CLI tool using Textual
"""

import os
import sys
import threading
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import asyncio

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Button, Select, Static, Input, TextArea, 
    DataTable, Label, ProgressBar,
    TabbedContent, TabPane
)
from textual.binding import Binding
from textual.message import Message
from textual.screen import ModalScreen
from textual import on
from textual.validation import Number
from textual.reactive import reactive

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


class ConfirmDialog(ModalScreen[bool]):
    """A modal confirmation dialog."""
    
    def __init__(self, title: str, message: str, confirm_text: str = "Yes", cancel_text: str = "No"):
        super().__init__()
        self.title = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.title or "Dialog", classes="dialog-title"),
            Static(self.message, classes="dialog-message"),
            Horizontal(
                Button(self.cancel_text, variant="default", id="cancel"),
                Button(self.confirm_text, variant="error", id="confirm"),
                classes="dialog-buttons"
            ),
            classes="dialog"
        )
    
    @on(Button.Pressed, "#confirm")
    def on_confirm(self):
        self.dismiss(True)
    
    @on(Button.Pressed, "#cancel") 
    def on_cancel(self):
        self.dismiss(False)


class GameConfigDialog(ModalScreen[Optional[tuple]]):
    """Modal dialog for adding/editing game configuration."""
    
    def __init__(self, title: str, game_id: str = "", game_info: Optional[Dict] = None):
        super().__init__()
        self.dialog_title = title
        self.game_id = game_id
        self.game_info = game_info or {}
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.dialog_title, classes="dialog-title"),
            
            Label("Game ID (short name, no spaces):"),
            Input(
                value=self.game_id,
                placeholder="e.g., grim_dawn",
                id="game_id"
            ),
            
            Label("Game Name:"),
            Input(
                value=self.game_info.get("name", ""),
                placeholder="e.g., Grim Dawn",
                id="game_name"
            ),
            
            Label("Save Directory Path:"),
            Input(
                value=self.game_info.get("save_path", ""),
                placeholder="e.g., C:/Users/Username/Documents/My Games/Grim Dawn/save",
                id="save_path"
            ),
            
            Label("Backup Directory Path (optional):"),
            Input(
                value=self.game_info.get("backup_path", ""),
                placeholder="Leave empty to use default",
                id="backup_path"
            ),
            
            Label("Description (optional):"),
            TextArea(
                text=self.game_info.get("description", ""),
                id="description"
            ),
            
            Horizontal(
                Button("Cancel", variant="default", id="cancel"),
                Button("OK", variant="primary", id="ok"),
                classes="dialog-buttons"
            ),
            classes="dialog config-dialog"
        )
    
    @on(Button.Pressed, "#ok")
    def on_ok(self):
        game_id = self.query_one("#game_id", Input).value.strip()
        name = self.query_one("#game_name", Input).value.strip()
        save_path = self.query_one("#save_path", Input).value.strip()
        backup_path = self.query_one("#backup_path", Input).value.strip()
        description = self.query_one("#description", TextArea).text.strip()
        
        # Validate input
        if not game_id:
            self.notify("Game ID is required", severity="error")
            return
        
        if ' ' in game_id:
            self.notify("Game ID cannot contain spaces", severity="error")
            return
        
        if not name:
            self.notify("Game name is required", severity="error")
            return
        
        if not save_path:
            self.notify("Save path is required", severity="error")
            return
        
        result = (game_id, {
            "name": name,
            "save_path": save_path,
            "backup_path": backup_path,
            "description": description
        })
        
        self.dismiss(result)
    
    @on(Button.Pressed, "#cancel")
    def on_cancel(self):
        self.dismiss(None)


class BackupManagerApp(App):
    """Main Textual application for backup management."""
    
    CSS = """
    .dialog {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        margin: 2;
        padding: 1;
    }
    
    .config-dialog {
        width: 80;
        height: 25;
    }
    
    .dialog-title {
        dock: top;
        height: 1;
        content-align: center middle;
        text-style: bold;
        color: $primary;
    }
    
    .dialog-message {
        margin: 1 0;
    }
    
    .dialog-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
    }
    
    .dialog-buttons Button {
        margin: 0 1;
    }
    
    .section-header {
        text-style: bold;
        color: $primary;
        margin: 1 0 0 0;
        padding: 0 0 1 0;
        border-bottom: solid $primary;
    }
    
    .action-buttons, .backup-buttons, .config-buttons {
        height: 3;
        align: left middle;
        margin: 1 0;
    }
    
    .action-buttons Button, .backup-buttons Button, .config-buttons Button {
        margin: 0 1 0 0;
    }
    
    .setting-row {
        height: 3;
        align: left middle;
        margin: 0 0 1 0;
    }
    
    .setting-row Label {
        width: 20;
    }
    
    .setting-row Input {
        width: 30;
        margin: 0 1;
    }
    
    DataTable {
        height: 1fr;
        margin: 1 0;
    }
    
    Input {
        margin: 0 0 1 0;
    }
    
    TextArea {
        height: 5;
        margin: 0 0 1 0;
    }
    
    ProgressBar {
        margin: 1 0;
    }
    
    #progress_label {
        text-align: center;
        margin: 0 0 1 0;
    }
    
    #game_info {
        margin: 1 0;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("c", "create_backup", "Create Backup"),
        Binding("d", "delete_backup", "Delete Backup"),
    ]
    
    def __init__(self):
        super().__init__()
        self.title = "🎮 Save Game Backup Manager"
        self.sub_title = "Terminal UI for managing game save backups"
        
        # Load configuration
        self.config_path = Path(__file__).parent / "games_config.json"
        self.config = load_games_config(self.config_path)
        
        # Current state
        self.manager = None
        self.current_game_id = None
        self.current_game_info = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="backup_tab", id="tabs"):
            with TabPane("🎮 Backup Manager", id="backup_tab"):
                yield Vertical(
                    # Game Selection Section
                    Static("🎮 Game Selection", classes="section-header"),
                    Label("Select Game:"),
                    Select(
                        options=[("No games configured", None)],
                        prompt="Choose a game...",
                        id="game_select",
                        allow_blank=True
                    ),
                    Static("", id="game_info"),
                    
                    # Backup Actions Section  
                    Static("📁 Backup Actions", classes="section-header"),
                    Label("Backup Description (optional):"),
                    Input(placeholder="Enter backup description...", id="backup_description"),
                    Horizontal(
                        Button("💾 Create Backup", variant="success", id="create_backup"),
                        Button("🔄 Refresh", variant="default", id="refresh_backups"),
                        classes="action-buttons"
                    ),
                    
                    # Backup List Section
                    Static("📋 Available Backups", classes="section-header"),
                    DataTable(id="backup_table"),
                    Horizontal(
                        Button("🔄 Restore Selected", variant="warning", id="restore_backup"),
                        Button("X Delete Selected", variant="error", id="delete_backup"),
                        Button("🧹 Cleanup Old Backups", variant="primary", id="cleanup_backups"),
                        classes="backup-buttons"
                    ),
                    ProgressBar(total=100, show_eta=True, id="progress_bar"),
                    Static("", id="progress_label"),
                    
                    classes="backup-tab"
                )
            with TabPane("⚙️ Configuration", id="config_tab"):
                yield Vertical(
                    # Games Configuration Section
                    Static("🎮 Configured Games", classes="section-header"),
                    DataTable(id="games_table"),
                    Horizontal(
                        Button("➕ Add Game", variant="success", id="add_game"),
                        Button("✏️ Edit Selected", variant="primary", id="edit_game"),
                        Button("X Remove Selected", variant="error", id="remove_game"),
                        Button("🔄 Refresh", variant="default", id="refresh_games"),
                        classes="config-buttons"
                    ),
                    
                    # Global Settings Section
                    Static("⚙️ Global Settings", classes="section-header"),
                    Horizontal(
                        Label("Default Max Backups:"),
                        Input(
                            value="10",
                            placeholder="10",
                            id="max_backups",
                            validators=[Number(minimum=1, maximum=100)]
                        ),
                        classes="setting-row"
                    ),
                    Horizontal(
                        Label("Default Backup Path:"),
                        Input(
                            placeholder="Leave empty for default",
                            id="backup_path"
                        ),
                        classes="setting-row"
                    ),
                    Button("💾 Save Settings", variant="primary", id="save_settings"),
                    
                    classes="config-tab"
                )
        yield Footer()
    
    def on_mount(self):
        """Initialize the application on mount."""
        # Setup table columns
        backup_table = self.query_one("#backup_table", DataTable)
        backup_table.add_columns("Backup Name", "Date", "Time", "Age", "Size", "Description")
        backup_table.cursor_type = "row"
        
        games_table = self.query_one("#games_table", DataTable)
        games_table.add_columns("Game ID", "Name", "Save Path", "Backup Path", "Description")
        games_table.cursor_type = "row"
        
        # Hide progress bar initially
        self.query_one("#progress_bar", ProgressBar).display = False
        self.query_one("#progress_label", Static).display = False
        
        # Load data
        self.update_game_list()
        self.update_games_table()
        self.load_settings()
    
    def update_game_list(self):
        """Update the game selection dropdown."""
        select = self.query_one("#game_select", Select)
        games = list_games(self.config)
        
        if games:
            options = [(f"{game_info.get('name', game_id)} ({game_id})", game_id) 
                      for game_id, game_info in games]
            select.set_options(options)
            
            # Select first game if none selected
            if not select.value and options:
                select.value = options[0][1]
        else:
            # No games configured
            select.set_options([("No games configured - Add games in Configuration tab", None)])
            select.value = None
    
    @on(Select.Changed, "#game_select")
    def on_game_selected(self, event: Select.Changed):
        """Handle game selection change."""
        if event.value and event.value != None:  # Check for valid game selection
            self.current_game_id = event.value
            self.current_game_info = self.config.get("games", {}).get(event.value)
            self.update_game_info()
            self.initialize_backup_manager()
            self.refresh_backup_list()
        else:
            # Clear selection
            self.current_game_id = None
            self.current_game_info = None
            self.manager = None
            self.update_game_info()
            # Clear backup list
            table = self.query_one("#backup_table", DataTable)
            table.clear()
    
    def update_game_info(self):
        """Update the game information display."""
        info_widget = self.query_one("#game_info", Static)
        
        if not self.current_game_info:
            info_widget.update("No game selected")
            return
        
        name = self.current_game_info.get("name", "Unknown")
        save_path = self.current_game_info.get("save_path", "Not set")
        backup_path = self.current_game_info.get("backup_path", "Default")
        description = self.current_game_info.get("description", "No description")
        
        info_text = f"""[bold]Name:[/bold] {name}
[bold]Save Path:[/bold] {save_path}
[bold]Backup Path:[/bold] {backup_path}
[bold]Description:[/bold] {description}"""
        
        info_widget.update(info_text)
    
    def initialize_backup_manager(self):
        """Initialize the backup manager for the selected game."""
        if not self.current_game_id or not self.current_game_info:
            self.manager = None
            return
        
        try:
            game_config = self.current_game_info.copy()
            
            # Use default backup path if not specified
            if not game_config.get("backup_path"):
                default_backup_path = self.config.get("settings", {}).get("default_backup_path", "")
                if default_backup_path and self.current_game_id:
                    game_config["backup_path"] = os.path.join(default_backup_path, str(self.current_game_id))
            
            # Get max backups setting
            max_backups = self.config.get("settings", {}).get("default_max_backups", 10)
            
            self.manager = SaveBackupManager(
                save_dir=game_config["save_path"],
                backup_dir=game_config.get("backup_path"),
                max_backups=max_backups,
                game_name=self.current_game_info.get("name")
            )
            
        except Exception as e:
            self.notify(f"Failed to initialize backup manager: {e}", severity="error")
            self.manager = None
    
    def refresh_backup_list(self):
        """Refresh the backup list display."""
        table = self.query_one("#backup_table", DataTable)
        table.clear()
        
        if not self.manager:
            return
        
        try:
            backups = self.manager._get_backup_list()
            
            for backup_path in backups:
                backup_path_obj = Path(backup_path)
                backup_name = backup_path_obj.name
                
                # Parse timestamp from backup name
                try:
                    timestamp_str = backup_name.replace("backup_", "")
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    date_str = timestamp.strftime("%Y-%m-%d")
                    time_str = timestamp.strftime("%H:%M:%S")
                    
                    # Calculate age
                    age = datetime.datetime.now() - timestamp
                    if age.days > 0:
                        age_str = f"{age.days}d ago"
                    elif age.seconds > 3600:
                        hours = age.seconds // 3600
                        age_str = f"{hours}h ago"
                    else:
                        minutes = age.seconds // 60
                        age_str = f"{minutes}m ago"
                        
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
                
                # Add row to table
                table.add_row(backup_name, date_str, time_str, age_str, size_str, description)
        
        except Exception as e:
            self.notify(f"Failed to refresh backup list: {e}", severity="error")
    
    @on(Button.Pressed, "#create_backup")
    def on_create_backup(self):
        """Create a new backup."""
        if not self.manager:
            self.notify("No game selected", severity="error")
            return
        
        description_input = self.query_one("#backup_description", Input)
        description = description_input.value.strip() or None
        
        # Show progress
        self.show_progress("Creating backup...")
        
        def backup_worker():
            try:
                if not self.manager:
                    return
                result = self.manager.create_backup(description)
                self.call_from_thread(self.on_backup_complete, result is not None, description_input)
            except Exception as e:
                self.call_from_thread(self.on_backup_error, str(e))
        
        thread = threading.Thread(target=backup_worker, daemon=True)
        thread.start()
    
    def on_backup_complete(self, result: bool, description_input: Input):
        """Handle backup completion."""
        self.hide_progress()
        
        if result:
            self.notify("Backup created successfully!", severity="information")
            description_input.value = ""
            self.refresh_backup_list()
        else:
            self.notify("Failed to create backup", severity="error")
    
    def on_backup_error(self, error: str):
        """Handle backup error."""
        self.hide_progress()
        self.notify(f"Backup failed: {error}", severity="error")
    
    @on(Button.Pressed, "#restore_backup")
    def on_restore_backup(self):
        """Restore the selected backup."""
        table = self.query_one("#backup_table", DataTable)
        
        if table.cursor_row is None or table.cursor_row >= table.row_count:
            self.notify("Please select a backup to restore", severity="warning")
            return
        
        if not self.manager:
            self.notify("No game selected", severity="error")
            return
        
        # Get selected backup name
        row_key = table.get_row_at(table.cursor_row)
        backup_name = row_key[0]
        
        # Show confirmation dialog
        def handle_restore_confirmation(confirmed: bool | None):
            if confirmed:
                self.perform_restore(backup_name, table.cursor_row)
        
        self.push_screen(
            ConfirmDialog(
                "Confirm Restore",
                f"This will overwrite your current save files with '{backup_name}'.\n\nAre you sure you want to continue?",
                "Restore",
                "Cancel"
            ),
            handle_restore_confirmation
        )
    
    def perform_restore(self, backup_name: str, cursor_row: int):
        """Perform the actual restore operation."""
        # Show progress
        self.show_progress("Restoring backup...")
        
        def restore_worker():
            try:
                if not self.manager:
                    return
                backups = self.manager._get_backup_list()
                backup_index = cursor_row + 1  # Convert to 1-based index
                
                success = self.manager.restore_backup(backup_index, skip_confirmation=True)
                self.call_from_thread(self.on_restore_complete, success)
            except Exception as e:
                self.call_from_thread(self.on_restore_error, str(e))
        
        thread = threading.Thread(target=restore_worker, daemon=True)
        thread.start()
    
    def on_restore_complete(self, success: bool):
        """Handle restore completion."""
        self.hide_progress()
        
        if success:
            self.notify("Backup restored successfully!", severity="information")
        else:
            self.notify("Failed to restore backup", severity="error")
    
    def on_restore_error(self, error: str):
        """Handle restore error."""
        self.hide_progress()
        self.notify(f"Restore failed: {error}", severity="error")
    
    @on(Button.Pressed, "#delete_backup")
    def on_delete_backup(self):
        """Delete the selected backup."""
        table = self.query_one("#backup_table", DataTable)
        
        if table.cursor_row is None or table.cursor_row >= table.row_count:
            self.notify("Please select a backup to delete", severity="warning")
            return
        
        if not self.manager:
            self.notify("No game selected", severity="error")
            return
        
        # Get selected backup name
        row_key = table.get_row_at(table.cursor_row)
        backup_name = row_key[0]
        
        # Show confirmation dialog
        def handle_delete_confirmation(confirmed: bool | None):
            if confirmed:
                self.perform_delete(backup_name, table.cursor_row)
        
        self.push_screen(
            ConfirmDialog(
                "Confirm Delete",
                f"Are you sure you want to delete backup '{backup_name}'?\n\nThis action cannot be undone.",
                "Delete",
                "Cancel"
            ),
            handle_delete_confirmation
        )
    
    def perform_delete(self, backup_name: str, cursor_row: int):
        """Perform the actual delete operation."""
        if not self.manager:
            self.notify("No backup manager available", severity="error")
            return
            
        try:
            backup_index = cursor_row + 1  # Convert to 1-based index
            success = self.manager.delete_backup(backup_index, skip_confirmation=True)
            
            if success:
                self.notify("Backup deleted successfully!", severity="information")
                self.refresh_backup_list()
            else:
                self.notify("Failed to delete backup", severity="error")
                
        except Exception as e:
            self.notify(f"Delete failed: {e}", severity="error")
    
    @on(Button.Pressed, "#cleanup_backups")
    def on_cleanup_backups(self):
        """Cleanup old backups."""
        if not self.manager:
            self.notify("No game selected", severity="error")
            return
        
        # Show confirmation dialog
        def handle_cleanup_confirmation(confirmed: bool | None):
            if confirmed:
                self.perform_cleanup()
        
        self.push_screen(
            ConfirmDialog(
                "Confirm Cleanup",
                f"This will remove old backups beyond the configured limit.\n\nContinue?",
                "Cleanup",
                "Cancel"
            ),
            handle_cleanup_confirmation
        )
    
    def perform_cleanup(self):
        """Perform the actual cleanup operation."""
        if not self.manager:
            self.notify("No backup manager available", severity="error")
            return
            
        try:
            # Call the private cleanup method
            initial_count = len(self.manager._get_backup_list())
            self.manager._cleanup_old_backups()
            final_count = len(self.manager._get_backup_list())
            removed_count = initial_count - final_count
            
            if removed_count > 0:
                self.notify(f"Cleaned up {removed_count} old backup(s)", severity="information")
                self.refresh_backup_list()
            else:
                self.notify("No old backups to clean up", severity="information")
                
        except Exception as e:
            self.notify(f"Cleanup failed: {e}", severity="error")
    
    @on(Button.Pressed, "#refresh_backups")
    def on_refresh_backups(self):
        """Refresh the backup list."""
        self.refresh_backup_list()
    
    def update_games_table(self):
        """Update the games configuration table."""
        table = self.query_one("#games_table", DataTable)
        table.clear()
        
        games = self.config.get("games", {})
        
        for game_id, game_info in games.items():
            name = game_info.get("name", "")
            save_path = game_info.get("save_path", "")
            backup_path = game_info.get("backup_path", "Default")
            description = game_info.get("description", "")
            
            table.add_row(game_id, name, save_path, backup_path, description)
    
    @on(Button.Pressed, "#add_game")
    def on_add_game(self):
        """Add a new game configuration."""
        def handle_add_game_result(result: tuple | None):
            if result:
                game_id, game_info = result
                
                if game_id in self.config.get("games", {}):
                    self.notify(f"Game '{game_id}' already exists", severity="error")
                    return
                
                if "games" not in self.config:
                    self.config["games"] = {}
                
                self.config["games"][game_id] = game_info
                save_games_config(self.config_path, self.config)
                
                self.notify(f"Game '{game_info['name']}' added successfully!", severity="information")
                self.update_games_table()
                self.update_game_list()
        
        self.push_screen(
            GameConfigDialog("Add New Game"),
            handle_add_game_result
        )
    
    @on(Button.Pressed, "#edit_game")
    def on_edit_game(self):
        """Edit the selected game configuration."""
        table = self.query_one("#games_table", DataTable)
        
        if table.cursor_row is None or table.cursor_row >= table.row_count:
            self.notify("Please select a game to edit", severity="warning")
            return
        
        # Get selected game
        row_key = table.get_row_at(table.cursor_row)
        game_id = row_key[0]
        game_info = self.config.get("games", {}).get(game_id, {})
        
        def handle_edit_game_result(result: tuple | None):
            if result:
                new_game_id, new_game_info = result
                
                # If game ID changed, remove old and add new
                if new_game_id != game_id:
                    if new_game_id in self.config.get("games", {}):
                        self.notify(f"Game '{new_game_id}' already exists", severity="error")
                        return
                    
                    del self.config["games"][game_id]
                    self.config["games"][new_game_id] = new_game_info
                else:
                    self.config["games"][game_id] = new_game_info
                
                save_games_config(self.config_path, self.config)
                
                self.notify(f"Game '{new_game_info['name']}' updated successfully!", severity="information")
                self.update_games_table()
                self.update_game_list()
        
        self.push_screen(
            GameConfigDialog("Edit Game", game_id, game_info),
            handle_edit_game_result
        )
    
    @on(Button.Pressed, "#remove_game")
    def on_remove_game(self):
        """Remove the selected game configuration."""
        table = self.query_one("#games_table", DataTable)
        
        if table.cursor_row is None or table.cursor_row >= table.row_count:
            self.notify("Please select a game to remove", severity="warning")
            return
        
        # Get selected game
        row_key = table.get_row_at(table.cursor_row)
        game_id = row_key[0]
        game_info = self.config.get("games", {}).get(game_id, {})
        game_name = game_info.get("name", game_id)
        
        # Show confirmation dialog
        def handle_remove_confirmation(confirmed: bool | None):
            if confirmed:
                del self.config["games"][game_id]
                save_games_config(self.config_path, self.config)
                
                self.notify(f"Game '{game_name}' removed successfully!", severity="information")
                self.update_games_table()
                self.update_game_list()
        
        self.push_screen(
            ConfirmDialog(
                "Confirm Remove",
                f"Are you sure you want to remove '{game_name}' from the configuration?",
                "Remove",
                "Cancel"
            ),
            handle_remove_confirmation
        )
    
    @on(Button.Pressed, "#refresh_games")
    def on_refresh_games(self):
        """Refresh the games table."""
        self.update_games_table()
    
    def load_settings(self):
        """Load global settings into the UI."""
        settings = self.config.get("settings", {})
        
        max_backups_input = self.query_one("#max_backups", Input)
        max_backups_input.value = str(settings.get("default_max_backups", 10))
        
        backup_path_input = self.query_one("#backup_path", Input)
        backup_path_input.value = settings.get("default_backup_path", "")
    
    @on(Button.Pressed, "#save_settings")
    def on_save_settings(self):
        """Save global settings."""
        try:
            max_backups_input = self.query_one("#max_backups", Input)
            backup_path_input = self.query_one("#backup_path", Input)
            
            max_backups = int(max_backups_input.value) if max_backups_input.value else 10
            backup_path = backup_path_input.value.strip()
            
            if "settings" not in self.config:
                self.config["settings"] = {}
            
            self.config["settings"]["default_max_backups"] = max_backups
            self.config["settings"]["default_backup_path"] = backup_path
            
            save_games_config(self.config_path, self.config)
            
            self.notify("Settings saved successfully!", severity="information")
            
            # Reinitialize backup manager if needed
            if self.manager:
                self.manager.max_backups = max_backups
            
        except ValueError:
            self.notify("Invalid value for max backups", severity="error")
        except Exception as e:
            self.notify(f"Failed to save settings: {e}", severity="error")
    
    def show_progress(self, message: str):
        """Show progress bar with message."""
        progress_bar = self.query_one("#progress_bar", ProgressBar)
        progress_label = self.query_one("#progress_label", Static)
        
        progress_bar.display = True
        progress_label.display = True
        progress_label.update(message)
        
        # Set indeterminate progress
        progress_bar.advance(0)
    
    def hide_progress(self):
        """Hide progress bar."""
        progress_bar = self.query_one("#progress_bar", ProgressBar)
        progress_label = self.query_one("#progress_label", Static)
        
        progress_bar.display = False
        progress_label.display = False
    
    def action_refresh(self):
        """Refresh current view."""
        self.refresh_backup_list()
    
    def action_create_backup(self):
        """Create backup via keyboard shortcut."""
        self.on_create_backup()
    
    def action_delete_backup(self):
        """Delete backup via keyboard shortcut."""
        self.on_delete_backup()


def main():
    """Run the Textual backup manager application."""
    app = BackupManagerApp()
    app.run()


if __name__ == "__main__":
    main()
