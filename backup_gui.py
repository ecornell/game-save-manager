#!/usr/bin/env python3
"""
Save Game Backup Manager - GUI Version
A user-friendly graphical interface for the backup.py CLI tool
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import sys
import threading
import datetime
from pathlib import Path
from typing import Optional, Dict, Any

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
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Save Game Backup Manager")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Load configuration
        self.config_path = Path(__file__).parent / "games_config.json"
        self.config = load_games_config(self.config_path)
        
        # Current manager instance
        self.manager = None
        self.current_game_id = None
        self.current_game_info = None
        
        # Setup UI
        self.setup_styles()
        self.create_widgets()
        self.update_game_list()
        
        # Setup periodic refresh for backup list
        self.refresh_backups_periodically()
    
    def setup_styles(self):
        """Configure custom styles for the GUI"""
        style = ttk.Style()
        
        # Configure button styles
        style.configure("Success.TButton", foreground="green")
        style.configure("Warning.TButton", foreground="orange")
        style.configure("Danger.TButton", foreground="red")
        style.configure("Primary.TButton", foreground="blue")
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_backup_tab()
        self.create_config_tab()
        
    def create_backup_tab(self):
        """Create the main backup management tab"""
        self.backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_frame, text="Backup Manager")
        
        # Game selection frame
        game_frame = ttk.LabelFrame(self.backup_frame, text="Game Selection", padding=10)
        game_frame.pack(fill="x", padx=10, pady=5)
        
        # Game dropdown
        ttk.Label(game_frame, text="Select Game:").pack(anchor="w")
        self.game_var = tk.StringVar()
        self.game_dropdown = ttk.Combobox(game_frame, textvariable=self.game_var, 
                                         state="readonly", width=50)
        self.game_dropdown.pack(fill="x", pady=(5, 0))
        self.game_dropdown.bind("<<ComboboxSelected>>", self.on_game_selected)
        
        # Game info frame
        self.info_frame = ttk.LabelFrame(self.backup_frame, text="Game Information", padding=10)
        self.info_frame.pack(fill="x", padx=10, pady=5)
        
        self.info_text = tk.Text(self.info_frame, height=4, state="disabled", 
                                bg=self.root.cget("bg"), relief="flat")
        self.info_text.pack(fill="x")
        
        # Action buttons frame
        action_frame = ttk.LabelFrame(self.backup_frame, text="Actions", padding=10)
        action_frame.pack(fill="x", padx=10, pady=5)
        
        # Backup controls
        backup_controls = ttk.Frame(action_frame)
        backup_controls.pack(fill="x", pady=(0, 10))
        
        ttk.Label(backup_controls, text="Backup Description (optional):").pack(anchor="w")
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(backup_controls, textvariable=self.description_var)
        self.description_entry.pack(fill="x", pady=(5, 10))
        
        self.backup_btn = ttk.Button(backup_controls, text="💾 Create Backup", 
                                    command=self.create_backup, style="Success.TButton")
        self.backup_btn.pack(side="left", padx=(0, 10))
        
        self.refresh_btn = ttk.Button(backup_controls, text="🔄 Refresh", 
                                     command=self.refresh_backup_list)
        self.refresh_btn.pack(side="left")
        
        # Backup list frame
        list_frame = ttk.LabelFrame(self.backup_frame, text="Available Backups", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Backup list with scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill="both", expand=True)
        
        # Treeview for backup list
        columns = ("Date", "Time", "Age", "Size", "Description")
        self.backup_tree = ttk.Treeview(list_container, columns=columns, show="tree headings")
        
        # Configure columns
        self.backup_tree.heading("#0", text="Backup Name")
        self.backup_tree.column("#0", width=150)
        
        for col in columns:
            self.backup_tree.heading(col, text=col)
            if col == "Date":
                self.backup_tree.column(col, width=100)
            elif col == "Time":
                self.backup_tree.column(col, width=80)
            elif col == "Age":
                self.backup_tree.column(col, width=100)
            elif col == "Size":
                self.backup_tree.column(col, width=80)
            else:  # Description
                self.backup_tree.column(col, width=200)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.backup_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_container, orient="horizontal", command=self.backup_tree.xview)
        self.backup_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Bind selection event to update button states
        self.backup_tree.bind("<<TreeviewSelect>>", self.on_backup_selected)
        
        # Pack treeview and scrollbars
        self.backup_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Backup action buttons
        backup_btn_frame = ttk.Frame(list_frame)
        backup_btn_frame.pack(fill="x", pady=(10, 0))
        
        self.restore_btn = ttk.Button(backup_btn_frame, text="🔄 Restore Selected", 
                                     command=self.restore_backup, style="Warning.TButton")
        self.restore_btn.pack(side="left", padx=(0, 10))
        
        self.delete_btn = ttk.Button(backup_btn_frame, text="🗑️ Delete Selected", 
                                    command=self.delete_backup, style="Danger.TButton")
        self.delete_btn.pack(side="left", padx=(0, 10))
        
        self.cleanup_btn = ttk.Button(backup_btn_frame, text="🧹 Cleanup Old Backups", 
                                     command=self.cleanup_backups, style="Primary.TButton")
        self.cleanup_btn.pack(side="left")
        
        # Progress bar (initially hidden)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.backup_frame, variable=self.progress_var, 
                                           mode="determinate")
        self.progress_label = ttk.Label(self.backup_frame, text="")
        
        # Initially disable buttons
        self.update_button_states()
    
    def create_config_tab(self):
        """Create the configuration management tab"""
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Game Configuration")
        
        # Games list frame
        games_frame = ttk.LabelFrame(self.config_frame, text="Configured Games", padding=10)
        games_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Games treeview
        games_container = ttk.Frame(games_frame)
        games_container.pack(fill="both", expand=True)
        
        game_columns = ("Name", "Save Path", "Backup Path", "Description")
        self.games_tree = ttk.Treeview(games_container, columns=game_columns, show="tree headings")
        
        self.games_tree.heading("#0", text="Game ID")
        self.games_tree.column("#0", width=100)
        
        for col in game_columns:
            self.games_tree.heading(col, text=col)
            if col == "Name":
                self.games_tree.column(col, width=150)
            elif col in ["Save Path", "Backup Path"]:
                self.games_tree.column(col, width=200)
            else:  # Description
                self.games_tree.column(col, width=150)
        
        # Scrollbars for games tree
        games_v_scrollbar = ttk.Scrollbar(games_container, orient="vertical", 
                                         command=self.games_tree.yview)
        games_h_scrollbar = ttk.Scrollbar(games_container, orient="horizontal", 
                                         command=self.games_tree.xview)
        self.games_tree.configure(yscrollcommand=games_v_scrollbar.set, 
                                 xscrollcommand=games_h_scrollbar.set)
        
        self.games_tree.pack(side="left", fill="both", expand=True)
        games_v_scrollbar.pack(side="right", fill="y")
        games_h_scrollbar.pack(side="bottom", fill="x")
        
        # Config action buttons
        config_btn_frame = ttk.Frame(games_frame)
        config_btn_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(config_btn_frame, text="➕ Add Game", 
                  command=self.add_game).pack(side="left", padx=(0, 10))
        ttk.Button(config_btn_frame, text="✏️ Edit Selected", 
                  command=self.edit_game).pack(side="left", padx=(0, 10))
        ttk.Button(config_btn_frame, text="🗑️ Remove Selected", 
                  command=self.remove_game).pack(side="left", padx=(0, 10))
        ttk.Button(config_btn_frame, text="🔄 Refresh", 
                  command=self.update_games_tree).pack(side="left")
        
        # Settings frame
        settings_frame = ttk.LabelFrame(self.config_frame, text="Global Settings", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        settings_grid = ttk.Frame(settings_frame)
        settings_grid.pack(fill="x")
        
        # Max backups setting
        ttk.Label(settings_grid, text="Default Max Backups:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.max_backups_var = tk.StringVar(value=str(self.config.get("settings", {}).get("default_max_backups", 10)))
        max_backups_spinbox = ttk.Spinbox(settings_grid, from_=1, to=100, width=10, 
                                         textvariable=self.max_backups_var)
        max_backups_spinbox.grid(row=0, column=1, sticky="w")
        
        # Default backup path setting
        ttk.Label(settings_grid, text="Default Backup Path:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.backup_path_var = tk.StringVar(value=self.config.get("settings", {}).get("default_backup_path", ""))
        backup_path_frame = ttk.Frame(settings_grid)
        backup_path_frame.grid(row=1, column=1, sticky="ew", pady=(10, 0))
        backup_path_entry = ttk.Entry(backup_path_frame, textvariable=self.backup_path_var, width=40)
        backup_path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(backup_path_frame, text="Browse", 
                  command=self.browse_backup_path).pack(side="right", padx=(5, 0))
        
        # Save settings button
        ttk.Button(settings_frame, text="💾 Save Settings", 
                  command=self.save_settings).pack(pady=(10, 0))
        
        # Update the games tree
        self.update_games_tree()
    
    def update_game_list(self):
        """Update the game dropdown list"""
        games = list_games(self.config)
        game_names = [f"{game_info.get('name', game_id)} ({game_id})" 
                     for game_id, game_info in games]
        
        self.game_dropdown['values'] = game_names
        
        if game_names and not self.game_var.get():
            self.game_var.set(game_names[0])
            self.on_game_selected()
    
    def on_game_selected(self, event=None):
        """Handle game selection"""
        selection = self.game_var.get()
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
    
    def on_backup_selected(self, event=None):
        """Handle backup selection in the tree"""
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
        
        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
        self.info_text.config(state="disabled")
    
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
            messagebox.showerror("Error", f"Failed to initialize backup manager: {e}")
            self.manager = None
    
    def update_button_states(self):
        """Update the state of action buttons"""
        has_manager = self.manager is not None
        has_selection = len(self.backup_tree.selection()) > 0
        
        self.backup_btn.config(state="normal" if has_manager else "disabled")
        self.restore_btn.config(state="normal" if has_manager and has_selection else "disabled")
        self.delete_btn.config(state="normal" if has_manager and has_selection else "disabled")
        self.cleanup_btn.config(state="normal" if has_manager else "disabled")
        self.refresh_btn.config(state="normal" if has_manager else "disabled")
    
    def refresh_backup_list(self):
        """Refresh the backup list display"""
        # Clear current items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
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
                
                # Insert into tree
                self.backup_tree.insert("", "end", text=backup_name, 
                                       values=(date_str, time_str, age_str, size_str, description),
                                       tags=(backup_path,))
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh backup list: {e}")
        
        self.update_button_states()
    
    def create_backup(self):
        """Create a new backup"""
        if not self.manager:
            messagebox.showerror("Error", "No game selected")
            return
        
        description = self.description_var.get().strip() or None
        
        def backup_thread():
            try:
                if not self.manager:
                    return
                self.show_progress("Creating backup...")
                result = self.manager.create_backup(description)
                self.hide_progress()
                
                if result:
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Backup created successfully!"))
                    self.root.after(0, self.refresh_backup_list)
                    self.root.after(0, lambda: self.description_var.set(""))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to create backup"))
            except Exception as e:
                self.hide_progress()
                self.root.after(0, lambda: messagebox.showerror("Error", f"Backup failed: {e}"))
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def restore_backup(self):
        """Restore the selected backup"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a backup to restore")
            return
        
        if not self.manager:
            messagebox.showerror("Error", "No game selected")
            return
        
        item = selection[0]
        backup_name = self.backup_tree.item(item, "text")
        
        # Confirm restoration
        result = messagebox.askyesno(
            "Confirm Restore", 
            f"This will overwrite your current save files with '{backup_name}'.\n\nAre you sure you want to continue?",
            icon="warning"
        )
        
        if not result:
            return
        
        def restore_thread():
            try:
                if not self.manager:
                    return
                self.show_progress("Restoring backup...")
                
                # Get backup index
                backups = self.manager._get_backup_list()
                backup_tags = self.backup_tree.item(item, "tags")
                if backup_tags:
                    backup_path = backup_tags[0]
                    try:
                        backup_index = backups.index(backup_path) + 1  # Convert to 1-based index
                        
                        success = self.manager.restore_backup(backup_index, skip_confirmation=True)
                        self.hide_progress()
                        
                        if success:
                            self.root.after(0, lambda: messagebox.showinfo("Success", "Backup restored successfully!"))
                        else:
                            self.root.after(0, lambda: messagebox.showerror("Error", "Failed to restore backup"))
                    except ValueError:
                        self.hide_progress()
                        self.root.after(0, lambda: messagebox.showerror("Error", "Could not find backup in list"))
                else:
                    self.hide_progress()
                    self.root.after(0, lambda: messagebox.showerror("Error", "Could not find backup to restore"))
                    
            except Exception as e:
                self.hide_progress()
                self.root.after(0, lambda: messagebox.showerror("Error", f"Restore failed: {e}"))
        
        threading.Thread(target=restore_thread, daemon=True).start()
    
    def delete_backup(self):
        """Delete the selected backup"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a backup to delete")
            return
        
        if not self.manager:
            messagebox.showerror("Error", "No game selected")
            return
        
        item = selection[0]
        backup_name = self.backup_tree.item(item, "text")
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to permanently delete '{backup_name}'?",
            icon="warning"
        )
        
        if not result:
            return
        
        def delete_thread():
            try:
                if not self.manager:
                    return
                # Get backup index
                backups = self.manager._get_backup_list()
                backup_tags = self.backup_tree.item(item, "tags")
                if backup_tags:
                    backup_path = backup_tags[0]
                    try:
                        backup_index = backups.index(backup_path) + 1  # Convert to 1-based index
                        
                        success = self.manager.delete_backup(backup_index, skip_confirmation=True)
                        
                        if success:
                            self.root.after(0, lambda: messagebox.showinfo("Success", "Backup deleted successfully!"))
                            self.root.after(0, self.refresh_backup_list)
                        else:
                            self.root.after(0, lambda: messagebox.showerror("Error", "Failed to delete backup"))
                    except ValueError:
                        self.root.after(0, lambda: messagebox.showerror("Error", "Could not find backup in list"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Could not find backup to delete"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Delete failed: {e}"))
        
        threading.Thread(target=delete_thread, daemon=True).start()
    
    def cleanup_backups(self):
        """Clean up old backups"""
        if not self.manager:
            messagebox.showerror("Error", "No game selected")
            return
        
        # Get current backup count
        backups = self.manager._get_backup_list()
        max_backups = self.manager.max_backups
        
        if len(backups) <= max_backups:
            messagebox.showinfo("Info", f"Only {len(backups)} backup(s) found. No cleanup needed.")
            return
        
        to_delete = len(backups) - max_backups
        result = messagebox.askyesno(
            "Confirm Cleanup", 
            f"This will delete {to_delete} old backup(s), keeping the {max_backups} most recent.\n\nContinue?",
            icon="warning"
        )
        
        if not result:
            return
        
        def cleanup_thread():
            try:
                if not self.manager:
                    return
                self.manager.cleanup_backups()
                self.root.after(0, lambda: messagebox.showinfo("Success", "Old backups cleaned up successfully!"))
                self.root.after(0, self.refresh_backup_list)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Cleanup failed: {e}"))
        
        threading.Thread(target=cleanup_thread, daemon=True).start()
    
    def show_progress(self, message):
        """Show progress bar with message"""
        self.progress_label.config(text=message)
        self.progress_label.pack(pady=(10, 5))
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start()
        self.root.update()
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        self.root.update()
    
    def refresh_backups_periodically(self):
        """Refresh backup list every 30 seconds"""
        self.refresh_backup_list()
        self.root.after(30000, self.refresh_backups_periodically)
    
    def update_games_tree(self):
        """Update the games configuration tree"""
        # Clear current items
        for item in self.games_tree.get_children():
            self.games_tree.delete(item)
        
        # Reload config
        self.config = load_games_config(self.config_path)
        
        # Populate tree
        games = list_games(self.config)
        for game_id, game_info in games:
            name = game_info.get("name", game_id)
            save_path = game_info.get("save_path", "")
            backup_path = game_info.get("backup_path", "")
            description = game_info.get("description", "")
            
            self.games_tree.insert("", "end", text=game_id, 
                                  values=(name, save_path, backup_path, description))
        
        # Update game dropdown
        self.update_game_list()
    
    def add_game(self):
        """Add a new game configuration"""
        dialog = GameConfigDialog(self.root, "Add Game")
        if dialog.result:
            game_id, game_data = dialog.result
            
            # Check if game ID already exists
            if game_id in self.config.get("games", {}):
                messagebox.showerror("Error", f"Game ID '{game_id}' already exists")
                return
            
            # Add to config
            if "games" not in self.config:
                self.config["games"] = {}
            
            self.config["games"][game_id] = game_data
            save_games_config(self.config_path, self.config)
            
            messagebox.showinfo("Success", f"Game '{game_data['name']}' added successfully!")
            self.update_games_tree()
    
    def edit_game(self):
        """Edit the selected game configuration"""
        selection = self.games_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a game to edit")
            return
        
        item = selection[0]
        game_id = self.games_tree.item(item, "text")
        game_info = self.config.get("games", {}).get(game_id, {})
        
        dialog = GameConfigDialog(self.root, "Edit Game", game_id, game_info)
        if dialog.result:
            new_game_id, game_data = dialog.result
            
            # If game ID changed, remove old and add new
            if new_game_id != game_id:
                if new_game_id in self.config.get("games", {}):
                    messagebox.showerror("Error", f"Game ID '{new_game_id}' already exists")
                    return
                del self.config["games"][game_id]
                self.config["games"][new_game_id] = game_data
            else:
                self.config["games"][game_id] = game_data
            
            save_games_config(self.config_path, self.config)
            
            messagebox.showinfo("Success", f"Game '{game_data['name']}' updated successfully!")
            self.update_games_tree()
    
    def remove_game(self):
        """Remove the selected game configuration"""
        selection = self.games_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a game to remove")
            return
        
        item = selection[0]
        game_id = self.games_tree.item(item, "text")
        game_info = self.config.get("games", {}).get(game_id, {})
        game_name = game_info.get("name", game_id)
        
        result = messagebox.askyesno(
            "Confirm Remove", 
            f"Are you sure you want to remove '{game_name}' from the configuration?",
            icon="warning"
        )
        
        if result:
            del self.config["games"][game_id]
            save_games_config(self.config_path, self.config)
            
            messagebox.showinfo("Success", f"Game '{game_name}' removed successfully!")
            self.update_games_tree()
    
    def browse_backup_path(self):
        """Browse for default backup path"""
        path = filedialog.askdirectory(title="Select Default Backup Directory")
        if path:
            self.backup_path_var.set(path)
    
    def save_settings(self):
        """Save global settings"""
        try:
            max_backups = int(self.max_backups_var.get())
            backup_path = self.backup_path_var.get().strip()
            
            if "settings" not in self.config:
                self.config["settings"] = {}
            
            self.config["settings"]["default_max_backups"] = max_backups
            self.config["settings"]["default_backup_path"] = backup_path
            
            save_games_config(self.config_path, self.config)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            
            # Reinitialize backup manager if needed
            if self.manager:
                self.manager.max_backups = max_backups
            
        except ValueError:
            messagebox.showerror("Error", "Invalid value for max backups")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")


class GameConfigDialog:
    def __init__(self, parent, title, game_id="", game_info=None):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        # Initialize values
        game_info = game_info or {}
        
        # Create form
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill="both", expand=True)
        
        # Game ID
        ttk.Label(frame, text="Game ID (short name, no spaces):").pack(anchor="w")
        self.game_id_var = tk.StringVar(value=game_id)
        self.game_id_entry = ttk.Entry(frame, textvariable=self.game_id_var)
        self.game_id_entry.pack(fill="x", pady=(5, 15))
        
        # Game Name
        ttk.Label(frame, text="Game Name:").pack(anchor="w")
        self.name_var = tk.StringVar(value=game_info.get("name", ""))
        self.name_entry = ttk.Entry(frame, textvariable=self.name_var)
        self.name_entry.pack(fill="x", pady=(5, 15))
        
        # Save Path
        ttk.Label(frame, text="Save Directory Path:").pack(anchor="w")
        save_path_frame = ttk.Frame(frame)
        save_path_frame.pack(fill="x", pady=(5, 15))
        self.save_path_var = tk.StringVar(value=game_info.get("save_path", ""))
        self.save_path_entry = ttk.Entry(save_path_frame, textvariable=self.save_path_var)
        self.save_path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(save_path_frame, text="Browse", 
                  command=self.browse_save_path).pack(side="right", padx=(5, 0))
        
        # Backup Path
        ttk.Label(frame, text="Backup Directory Path (optional):").pack(anchor="w")
        backup_path_frame = ttk.Frame(frame)
        backup_path_frame.pack(fill="x", pady=(5, 15))
        self.backup_path_var = tk.StringVar(value=game_info.get("backup_path", ""))
        self.backup_path_entry = ttk.Entry(backup_path_frame, textvariable=self.backup_path_var)
        self.backup_path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(backup_path_frame, text="Browse", 
                  command=self.browse_backup_path).pack(side="right", padx=(5, 0))
        
        # Description
        ttk.Label(frame, text="Description (optional):").pack(anchor="w")
        self.description_text = tk.Text(frame, height=4)
        self.description_text.pack(fill="x", pady=(5, 15))
        self.description_text.insert(1.0, game_info.get("description", ""))
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side="right", padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side="right")
        
        # Focus on first entry
        self.game_id_entry.focus()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def browse_save_path(self):
        path = filedialog.askdirectory(title="Select Save Directory")
        if path:
            self.save_path_var.set(path)
    
    def browse_backup_path(self):
        path = filedialog.askdirectory(title="Select Backup Directory")
        if path:
            self.backup_path_var.set(path)
    
    def ok_clicked(self):
        # Validate input
        game_id = self.game_id_var.get().strip()
        name = self.name_var.get().strip()
        save_path = self.save_path_var.get().strip()
        backup_path = self.backup_path_var.get().strip()
        description = self.description_text.get(1.0, tk.END).strip()
        
        if not game_id:
            messagebox.showerror("Error", "Game ID is required")
            return
        
        if ' ' in game_id:
            messagebox.showerror("Error", "Game ID cannot contain spaces")
            return
        
        if not name:
            messagebox.showerror("Error", "Game name is required")
            return
        
        if not save_path:
            messagebox.showerror("Error", "Save path is required")
            return
        
        self.result = (game_id, {
            "name": name,
            "save_path": save_path,
            "backup_path": backup_path,
            "description": description
        })
        
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.dialog.destroy()


def main():
    root = tk.Tk()
    app = BackupManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
