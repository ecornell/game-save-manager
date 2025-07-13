import os
import shutil
import datetime
import glob
import argparse
import sys
import time
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

# Color codes for better terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_colored(text: str, color: str = Colors.WHITE, bold: bool = False):
    """Print colored text to terminal"""
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Colors.END}")

def print_header(text: str):
    """Print a formatted header"""
    print_colored(f"\n{'='*50}", Colors.CYAN)
    print_colored(f" {text} ", Colors.CYAN, bold=True)
    print_colored(f"{'='*50}", Colors.CYAN)

def print_success(text: str):
    """Print success message"""
    print_colored(f"✓ {text}", Colors.GREEN, bold=True)

def print_error(text: str):
    """Print error message"""
    print_colored(f"✗ {text}", Colors.RED, bold=True)

def print_warning(text: str):
    """Print warning message"""
    print_colored(f"⚠ {text}", Colors.YELLOW, bold=True)

def print_info(text: str):
    """Print info message"""
    print_colored(f"ℹ {text}", Colors.BLUE)

def show_progress(current: int, total: int, prefix: str = "Progress"):
    """Show a simple progress indicator"""
    percent = (current / total) * 100
    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f"\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})", end='', flush=True)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def get_directory_size(path: Path) -> int:
    """Calculate total size of directory"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        pass
    return total_size

def load_games_config(config_path: Path) -> Dict[str, Any]:
    """Load games configuration from JSON file"""
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                "games": {
                    "example_game": {
                        "name": "Example Game",
                        "save_path": "C:\\Users\\{username}\\Documents\\Example Game\\Saves",
                        "description": "Example game configuration"
                    }
                },
                "settings": {
                    "default_max_backups": 10,
                    "auto_expand_paths": True
                }
            }
            save_games_config(config_path, default_config)
            return default_config
    except Exception as e:
        print_error(f"Failed to load config file: {e}")
        return {"games": {}, "settings": {"default_max_backups": 10}}

def save_games_config(config_path: Path, config: Dict[str, Any]):
    """Save games configuration to JSON file"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print_error(f"Failed to save config file: {e}")

def expand_path(path_str: str) -> str:
    """Expand environment variables and user paths"""
    # Expand environment variables
    expanded = os.path.expandvars(path_str)
    # Expand user home directory
    expanded = os.path.expanduser(expanded)
    return expanded

def list_games(config: Dict[str, Any]) -> List[tuple]:
    """List available games from config"""
    games = []
    for game_id, game_info in config.get("games", {}).items():
        games.append((game_id, game_info))
    return games

def select_game(config: Dict[str, Any]) -> Optional[tuple]:
    """Interactive game selection"""
    games = list_games(config)
    
    if not games:
        print_warning("No games configured. Please add games to the config file first.")
        return None
    
    print_header("Select Game")
    
    for i, (game_id, game_info) in enumerate(games, 1):
        name = game_info.get("name", game_id)
        save_path = game_info.get("save_path", "Unknown")
        description = game_info.get("description", "")
        
        print_colored(f"{i:2d}. ", Colors.CYAN, bold=True)
        print_colored(f"{name}", Colors.WHITE, bold=True)
        print_colored(f"    📁 {save_path}", Colors.BLUE)
        if description:
            print_colored(f"    📝 {description}", Colors.MAGENTA)
    
    try:
        choice = input(f"\n{Colors.YELLOW}Select game number (1-{len(games)}) or 'q' to quit: {Colors.END}")
        if choice.lower() == 'q':
            return None
        
        choice = int(choice) - 1
        if 0 <= choice < len(games):
            return games[choice]
        else:
            print_error("Invalid choice.")
            return None
    except (ValueError, IndexError):
        print_error("Invalid input.")
        return None

def add_game_to_config(config_path: Path, config: Dict[str, Any]):
    """Interactive function to add a new game to config"""
    print_header("Add New Game")
    
    game_id = get_user_input_with_prompt("Game ID (short name, no spaces)")
    if not game_id or ' ' in game_id:
        print_error("Invalid game ID. Must not contain spaces.")
        return
    
    if game_id in config.get("games", {}):
        print_error(f"Game '{game_id}' already exists in config.")
        return
    
    name = get_user_input_with_prompt("Game name")
    if not name:
        print_error("Game name is required.")
        return
    
    save_path = get_user_input_with_prompt("Save directory path")
    if not save_path:
        print_error("Save path is required.")
        return
    
    description = get_user_input_with_prompt("Description (optional)")
    
    # Validate path exists (after expansion)
    expanded_path = expand_path(save_path)
    if not os.path.exists(expanded_path):
        print_warning(f"Path does not exist: {expanded_path}")
        confirm = input(f"{Colors.YELLOW}Add anyway? (y/N): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Game not added.")
            return
    
    # Add to config
    if "games" not in config:
        config["games"] = {}
    
    config["games"][game_id] = {
        "name": name,
        "save_path": save_path,
        "description": description
    }
    
    save_games_config(config_path, config)
    print_success(f"Game '{name}' added to config!")

def edit_game_config(config_path: Path, config: Dict[str, Any]):
    """Interactive function to edit a game in config"""
    games = list_games(config)
    if not games:
        print_warning("No games configured.")
        return
    
    print_header("Edit Game Configuration")
    
    # Show games and let user select
    for i, (game_id, game_info) in enumerate(games, 1):
        name = game_info.get("name", game_id)
        print_colored(f"{i:2d}. {name}", Colors.WHITE)
    
    try:
        choice = input(f"\n{Colors.YELLOW}Select game to edit (1-{len(games)}) or 'q' to quit: {Colors.END}")
        if choice.lower() == 'q':
            return
        
        choice = int(choice) - 1
        if not (0 <= choice < len(games)):
            print_error("Invalid choice.")
            return
        
        game_id, game_info = games[choice]
        
        print_info(f"Editing: {game_info.get('name', game_id)}")
        
        # Edit fields
        new_name = get_user_input_with_prompt("Game name", game_info.get("name"))
        new_path = get_user_input_with_prompt("Save directory path", game_info.get("save_path"))
        new_desc = get_user_input_with_prompt("Description", game_info.get("description", ""))
        
        # Update config
        config["games"][game_id].update({
            "name": new_name,
            "save_path": new_path,
            "description": new_desc
        })
        
        save_games_config(config_path, config)
        print_success(f"Game '{new_name}' updated!")
        
    except (ValueError, IndexError):
        print_error("Invalid input.")

def remove_game_from_config(config_path: Path, config: Dict[str, Any]):
    """Interactive function to remove a game from config"""
    games = list_games(config)
    if not games:
        print_warning("No games configured.")
        return
    
    print_header("Remove Game")
    
    # Show games and let user select
    for i, (game_id, game_info) in enumerate(games, 1):
        name = game_info.get("name", game_id)
        print_colored(f"{i:2d}. {name}", Colors.WHITE)
    
    try:
        choice = input(f"\n{Colors.YELLOW}Select game to remove (1-{len(games)}) or 'q' to quit: {Colors.END}")
        if choice.lower() == 'q':
            return
        
        choice = int(choice) - 1
        if not (0 <= choice < len(games)):
            print_error("Invalid choice.")
            return
        
        game_id, game_info = games[choice]
        game_name = game_info.get("name", game_id)
        
        confirm = input(f"\n{Colors.RED}Are you sure you want to remove '{game_name}'? (y/N): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Removal cancelled.")
            return
        
        del config["games"][game_id]
        save_games_config(config_path, config)
        print_success(f"Game '{game_name}' removed from config!")
        
    except (ValueError, IndexError):
        print_error("Invalid input.")

class SaveBackupManager:
    def __init__(self, save_dir=None, backup_dir=None, max_backups=10, game_name=None):
        # Default to current directory if not specified
        self.save_dir = Path(save_dir) if save_dir else Path.cwd()
        self.backup_dir = Path(backup_dir) if backup_dir else self.save_dir / "backups"
        self.max_backups = max_backups
        self.game_name = game_name
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)

        print_info(f"Game: {self.game_name or 'Custom'}")
        print_info(f"Save directory: {self.save_dir}")
        print_info(f"Backup directory: {self.backup_dir}")
        print_info(f"Maximum backups: {self.max_backups}")
    
    def _get_save_size(self) -> str:
        """Get the size of the save directory"""
        try:
            size = get_directory_size(self.save_dir)
            return format_file_size(size)
        except Exception:
            return "Unknown"
    
    def _cleanup_old_backups(self):
        """Remove old backups if we exceed max_backups"""
        backups = self._get_backup_list()
        if len(backups) > self.max_backups:
            backups_to_delete = backups[self.max_backups:]
            print_warning(f"Cleaning up {len(backups_to_delete)} old backup(s)...")
            for backup_path in backups_to_delete:
                try:
                    shutil.rmtree(backup_path)
                    backup_name = Path(backup_path).name
                    print_info(f"Deleted old backup: {backup_name}")
                except Exception as e:
                    print_error(f"Failed to delete {backup_path}: {e}")
    
    def _get_backup_list(self) -> List[str]:
        """Get sorted list of backup directories"""
        backup_pattern = self.backup_dir / "backup_*"
        return sorted(glob.glob(str(backup_pattern)), reverse=True)
    
    def create_backup(self, description: str = None) -> Optional[Path]:
        """Create a timestamped backup of the save directory"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        save_size = self._get_save_size()
        
        try:
            print_info(f"Creating backup: {backup_name}")
            print_info(f"Save directory size: {save_size}")
            
            if description:
                print_info(f"Description: {description}")
            
            # Count files for progress
            file_count = sum(len(files) for _, _, files in os.walk(self.save_dir))
            if file_count == 0:
                print_warning("No files found in save directory")
                return None
            
            print_info(f"Backing up {file_count} files...")
            
            # Show progress during backup
            start_time = time.time()
            
            def copy_with_progress(src, dst, *, follow_symlinks=True):
                files_copied = getattr(copy_with_progress, 'counter', 0)
                copy_with_progress.counter = files_copied + 1
                show_progress(copy_with_progress.counter, file_count, "Copying files")
                return shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
            
            # Backup with progress
            shutil.copytree(
                self.save_dir, 
                backup_path, 
                ignore=shutil.ignore_patterns("backups", "*.pyc", "__pycache__", "*.tmp"),
                copy_function=copy_with_progress
            )
            
            print()  # New line after progress bar
            elapsed_time = time.time() - start_time
            
            # Save description if provided
            if description:
                desc_file = backup_path / ".backup_description"
                desc_file.write_text(description, encoding='utf-8')
            
            print_success(f"Backup created successfully in {elapsed_time:.1f}s")
            print_info(f"Location: {backup_path}")
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            print_error(f"Failed to create backup: {e}")
            return None
    
    def list_backups(self) -> List[str]:
        """List all available backups with enhanced formatting"""
        backups = self._get_backup_list()
        
        if not backups:
            print_warning("No backups found.")
            return []
        
        print_header("Available Backups")
        
        for i, backup in enumerate(backups, 1):
            backup_path = Path(backup)
            backup_name = backup_path.name
            
            # Extract timestamp from backup name
            timestamp_str = backup_name.replace("backup_", "")
            try:
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
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
                
                # Get backup size
                backup_size = format_file_size(get_directory_size(backup_path))
                
                # Check for description
                desc_file = backup_path / ".backup_description"
                description = ""
                if desc_file.exists():
                    try:
                        description = f" - {desc_file.read_text(encoding='utf-8').strip()}"
                    except Exception:
                        pass
                
                print_colored(f"{i:2d}. ", Colors.CYAN, bold=True)
                print_colored(f"{backup_name}", Colors.WHITE, bold=True)
                print_colored(f"    📅 {formatted_time} ({age_str})", Colors.BLUE)
                print_colored(f"    📦 Size: {backup_size}{description}", Colors.MAGENTA)
                
            except ValueError:
                print_colored(f"{i:2d}. {backup_name}", Colors.WHITE)
        
        return backups
    
    def restore_backup(self, backup_choice: Optional[int] = None) -> bool:
        """Restore a backup to the save directory"""
        backups = self._get_backup_list()
        
        if not backups:
            print_warning("No backups available to restore.")
            return False
        
        if backup_choice is None:
            self.list_backups()
            try:
                choice = input(f"\n{Colors.YELLOW}Enter backup number to restore (1-{len(backups)}) or 'q' to quit: {Colors.END}")
                if choice.lower() == 'q':
                    print_info("Restore cancelled.")
                    return False
                    
                choice = int(choice) - 1
                if choice < 0 or choice >= len(backups):
                    print_error("Invalid choice.")
                    return False
                backup_path = backups[choice]
            except (ValueError, IndexError):
                print_error("Invalid input.")
                return False
        else:
            if backup_choice < 1 or backup_choice > len(backups):
                print_error("Invalid backup number.")
                return False
            backup_path = backups[backup_choice - 1]
        
        backup_name = Path(backup_path).name
        
        # Show backup info
        print_header("Restore Backup")
        print_info(f"Selected backup: {backup_name}")
        
        # Check for description
        desc_file = Path(backup_path) / ".backup_description"
        if desc_file.exists():
            try:
                description = desc_file.read_text(encoding='utf-8').strip()
                print_info(f"Description: {description}")
            except Exception:
                pass
        
        # Confirm restoration
        print_warning("This will overwrite your current save files!")
        confirm = input(f"\n{Colors.YELLOW}Are you sure you want to restore '{backup_name}'? (y/N): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Restoration cancelled.")
            return False
        
        try:
            # Create a backup of current state before restoring
            print_info("Creating safety backup of current state...")
            current_backup = self.create_backup("Pre-restore safety backup")
            
            # Remove current save files (except backup folder)
            print_info("Removing current save files...")
            for item in self.save_dir.iterdir():
                if item.name != "backups" and item != Path(__file__):
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # Copy backup contents to save directory
            print_info("Restoring backup files...")
            backup_path_obj = Path(backup_path)
            files_to_restore = sum(len(files) for _, _, files in os.walk(backup_path_obj))
            
            files_restored = 0
            for item in backup_path_obj.iterdir():
                if item.name == ".backup_description":
                    continue
                    
                dest = self.save_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                    # Count files in directory
                    files_restored += sum(len(files) for _, _, files in os.walk(item))
                else:
                    shutil.copy2(item, dest)
                    files_restored += 1
                
                show_progress(files_restored, files_to_restore, "Restoring")
            
            print()  # New line after progress bar
            print_success(f"Backup '{backup_name}' restored successfully!")
            if current_backup:
                print_info(f"Previous state backed up as: {current_backup.name}")
            return True
            
        except Exception as e:
            print_error(f"Failed to restore backup: {e}")
            return False
    
    def delete_backup(self, backup_choice: Optional[int] = None) -> bool:
        """Delete a specific backup"""
        backups = self._get_backup_list()
        
        if not backups:
            print_warning("No backups available to delete.")
            return False
        
        if backup_choice is None:
            self.list_backups()
            try:
                choice = input(f"\n{Colors.YELLOW}Enter backup number to delete (1-{len(backups)}) or 'q' to quit: {Colors.END}")
                if choice.lower() == 'q':
                    print_info("Delete cancelled.")
                    return False
                    
                choice = int(choice) - 1
                if choice < 0 or choice >= len(backups):
                    print_error("Invalid choice.")
                    return False
                backup_path = backups[choice]
            except (ValueError, IndexError):
                print_error("Invalid input.")
                return False
        else:
            if backup_choice < 1 or backup_choice > len(backups):
                print_error("Invalid backup number.")
                return False
            backup_path = backups[backup_choice - 1]
        
        backup_name = Path(backup_path).name
        
        # Show backup info
        print_header("Delete Backup")
        print_warning(f"Selected backup: {backup_name}")
        
        # Confirm deletion
        confirm = input(f"\n{Colors.RED}Are you sure you want to permanently delete '{backup_name}'? (y/N): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Deletion cancelled.")
            return False
        
        try:
            shutil.rmtree(backup_path)
            print_success(f"Backup '{backup_name}' deleted successfully!")
            return True
        except Exception as e:
            print_error(f"Failed to delete backup: {e}")
            return False
    
    def cleanup_backups(self, keep_count: int = None):
        """Manual cleanup of old backups"""
        if keep_count is None:
            keep_count = self.max_backups
            
        backups = self._get_backup_list()
        if len(backups) <= keep_count:
            print_info(f"Only {len(backups)} backup(s) found. No cleanup needed.")
            return
        
        backups_to_delete = backups[keep_count:]
        print_warning(f"Will delete {len(backups_to_delete)} old backup(s), keeping the {keep_count} most recent.")
        
        confirm = input(f"\n{Colors.YELLOW}Continue? (y/N): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Cleanup cancelled.")
            return
        
        for backup_path in backups_to_delete:
            try:
                shutil.rmtree(backup_path)
                backup_name = Path(backup_path).name
                print_success(f"Deleted: {backup_name}")
            except Exception as e:
                print_error(f"Failed to delete {backup_path}: {e}")

def get_user_input_with_prompt(prompt: str, default: str = None) -> str:
    """Get user input with colored prompt"""
    if default:
        full_prompt = f"{Colors.CYAN}{prompt} [{default}]: {Colors.END}"
    else:
        full_prompt = f"{Colors.CYAN}{prompt}: {Colors.END}"
    
    response = input(full_prompt).strip()
    return response if response else default

def main():
    parser = argparse.ArgumentParser(
        description="🎮 Save Game Backup Manager - Keep your saves safe!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""":
Examples:
  python backup.py                          # Interactive mode with game selection
  python backup.py --game skyrim            # Use configured game 'skyrim'
  python backup.py --backup                 # Quick backup (current dir or selected game)
  python backup.py --backup -d "Before boss fight"  # Backup with description
  python backup.py --list                   # List all backups
  python backup.py --restore 1              # Restore backup #1
  python backup.py --config                 # Manage game configurations
        """
    )
    
    parser.add_argument("--save-dir", help="Path to save directory (overrides game config)")
    parser.add_argument("--backup-dir", help="Path to backup directory (default: ./backups)")
    parser.add_argument("--max-backups", type=int, help="Maximum number of backups to keep")
    parser.add_argument("--game", help="Game ID from config file")
    parser.add_argument("--config", action="store_true", help="Manage game configurations")
    parser.add_argument("--backup", action="store_true", help="Create a backup")
    parser.add_argument("-d", "--description", help="Description for the backup")
    parser.add_argument("--restore", type=int, help="Restore backup by number")
    parser.add_argument("--list", action="store_true", help="List all backups")
    parser.add_argument("--delete", type=int, help="Delete backup by number")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old backups")
    parser.add_argument("--keep", type=int, help="Number of backups to keep during cleanup")
    
    args = parser.parse_args()
    
    # Print welcome message
    print_header("🎮 Save Game Backup Manager")
    
    # Load config file
    config_path = Path(__file__).parent / "games_config.json"
    config = load_games_config(config_path)
    
    # Handle config management
    if args.config:
        while True:
            print_header("Game Configuration Manager")
            print_colored("1. 📋 List games", Colors.BLUE)
            print_colored("2. ➕ Add game", Colors.GREEN)
            print_colored("3. ✏️  Edit game", Colors.YELLOW)
            print_colored("4. 🗑️  Remove game", Colors.RED)
            print_colored("5. 🚪 Back to main menu", Colors.WHITE)
            
            choice = input(f"\n{Colors.CYAN}Enter your choice (1-5): {Colors.END}").strip()
            
            if choice == "1":
                games = list_games(config)
                if games:
                    print_header("Configured Games")
                    for i, (game_id, game_info) in enumerate(games, 1):
                        name = game_info.get("name", game_id)
                        save_path = game_info.get("save_path", "Unknown")
                        description = game_info.get("description", "")
                        
                        print_colored(f"{i:2d}. {name} (ID: {game_id})", Colors.WHITE, bold=True)
                        print_colored(f"    📁 {save_path}", Colors.BLUE)
                        if description:
                            print_colored(f"    📝 {description}", Colors.MAGENTA)
                else:
                    print_warning("No games configured.")
            elif choice == "2":
                add_game_to_config(config_path, config)
                config = load_games_config(config_path)  # Reload
            elif choice == "3":
                edit_game_config(config_path, config)
                config = load_games_config(config_path)  # Reload
            elif choice == "4":
                remove_game_from_config(config_path, config)
                config = load_games_config(config_path)  # Reload
            elif choice == "5":
                break
            else:
                print_error("Invalid choice. Please enter 1-5.")
            
            if choice in ["1", "2", "3", "4"]:
                input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")
    
    # Determine save directory and game info
    save_dir = args.save_dir
    game_name = None
    max_backups = args.max_backups or config.get("settings", {}).get("default_max_backups", 10)
    
    if args.game:
        # Use specified game from config
        game_info = config.get("games", {}).get(args.game)
        if game_info:
            save_dir = expand_path(game_info["save_path"])
            game_name = game_info["name"]
            print_success(f"Using configured game: {game_name}")
        else:
            print_error(f"Game '{args.game}' not found in config.")
            return
    elif not save_dir and not args.config:
        # Interactive game selection if no save dir specified
        selected = select_game(config)
        if selected:
            game_id, game_info = selected
            save_dir = expand_path(game_info["save_path"])
            game_name = game_info["name"]
            print_success(f"Selected game: {game_name}")
        else:
            print_info("No game selected, using current directory.")
    
    # Validate save directory exists
    if save_dir and not os.path.exists(save_dir):
        print_error(f"Save directory does not exist: {save_dir}")
        return
    
    # Initialize backup manager
    try:
        manager = SaveBackupManager(save_dir, args.backup_dir, max_backups, game_name)
    except Exception as e:
        print_error(f"Failed to initialize backup manager: {e}")
        sys.exit(1)
    
    # Handle command line arguments
    try:
        if args.backup:
            manager.create_backup(args.description)
        elif args.restore:
            manager.restore_backup(args.restore)
        elif args.list:
            manager.list_backups()
        elif args.delete:
            manager.delete_backup(args.delete)
        elif args.cleanup:
            manager.cleanup_backups(args.keep)
        elif not args.config:
            # Interactive mode
            while True:
                print_header("Main Menu")
                if game_name:
                    print_colored(f"🎮 Current Game: {game_name}", Colors.CYAN, bold=True)
                print_colored("1. 💾 Create backup", Colors.GREEN)
                print_colored("2. 📋 List backups", Colors.BLUE)
                print_colored("3. 🔄 Restore backup", Colors.YELLOW)
                print_colored("4. 🗑️  Delete backup", Colors.RED)
                print_colored("5. 🧹 Cleanup old backups", Colors.MAGENTA)
                print_colored("6. 🎮 Switch game", Colors.CYAN)
                print_colored("7. ⚙️  Manage games config", Colors.WHITE)
                print_colored("8. 🚪 Exit", Colors.WHITE)
                
                try:
                    choice = input(f"\n{Colors.CYAN}Enter your choice (1-8): {Colors.END}").strip()
                    
                    if choice == "1":
                        description = get_user_input_with_prompt("Backup description (optional)")
                        manager.create_backup(description if description else None)
                    elif choice == "2":
                        manager.list_backups()
                    elif choice == "3":
                        manager.restore_backup()
                    elif choice == "4":
                        manager.delete_backup()
                    elif choice == "5":
                        keep_count = get_user_input_with_prompt("Number of backups to keep", str(manager.max_backups))
                        try:
                            keep_count = int(keep_count)
                            manager.cleanup_backups(keep_count)
                        except ValueError:
                            print_error("Invalid number entered.")
                    elif choice == "6":
                        selected = select_game(config)
                        if selected:
                            game_id, game_info = selected
                            new_save_dir = expand_path(game_info["save_path"])
                            new_game_name = game_info["name"]
                            
                            if os.path.exists(new_save_dir):
                                manager = SaveBackupManager(new_save_dir, args.backup_dir, max_backups, new_game_name)
                                print_success(f"Switched to: {new_game_name}")
                            else:
                                print_error(f"Save directory does not exist: {new_save_dir}")
                    elif choice == "7":
                        # Jump to config management
                        args.config = True
                        break
                    elif choice == "8":
                        print_success("Thanks for using Save Game Backup Manager! 👋")
                        break
                    else:
                        print_error("Invalid choice. Please enter 1-8.")
                        
                except KeyboardInterrupt:
                    print_success("\nThanks for using Save Game Backup Manager! 👋")
                    break
                except Exception as e:
                    print_error(f"An error occurred: {e}")
                
                # Pause before showing menu again
                if choice not in ["7", "8"]:
                    input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")
                
    except KeyboardInterrupt:
        print_success("\nThanks for using Save Game Backup Manager! 👋")
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()