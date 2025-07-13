import os
import shutil
import datetime
import glob
import argparse
from pathlib import Path

class SaveBackupManager:
    def __init__(self, save_dir=None, backup_dir=None):
        # Default to current directory if not specified
        self.save_dir = Path(save_dir) if save_dir else Path.cwd()
        self.backup_dir = Path(backup_dir) if backup_dir else self.save_dir / "backups"
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)

        print(f"Save directory: {self.save_dir}")
        print(f"Backup directory: {self.backup_dir}")
    
    def create_backup(self):
        """Create a timestamped backup of the save directory"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            print(f"Creating backup: {backup_name}")
            shutil.copytree(self.save_dir, backup_path, ignore=shutil.ignore_patterns("backups", "*.pyc", "__pycache__"))
            print(f"Backup created successfully at: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def list_backups(self):
        """List all available backups"""
        backup_pattern = self.backup_dir / "backup_*"
        backups = sorted(glob.glob(str(backup_pattern)), reverse=True)
        
        if not backups:
            print("No backups found.")
            return []
        
        print("Available backups:")
        for i, backup in enumerate(backups, 1):
            backup_name = Path(backup).name
            # Extract timestamp from backup name
            timestamp_str = backup_name.replace("backup_", "")
            try:
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i}. {backup_name} ({formatted_time})")
            except ValueError:
                print(f"{i}. {backup_name}")
        
        return backups
    
    def restore_backup(self, backup_choice=None):
        """Restore a backup to the save directory"""
        backups = self.list_backups()
        
        if not backups:
            return False
        
        if backup_choice is None:
            try:
                choice = int(input("\nEnter backup number to restore: ")) - 1
                if choice < 0 or choice >= len(backups):
                    print("Invalid choice.")
                    return False
                backup_path = backups[choice]
            except (ValueError, IndexError):
                print("Invalid input.")
                return False
        else:
            if backup_choice < 1 or backup_choice > len(backups):
                print("Invalid backup number.")
                return False
            backup_path = backups[backup_choice - 1]
        
        backup_name = Path(backup_path).name
        
        # Confirm restoration
        confirm = input(f"Are you sure you want to restore '{backup_name}'? This will overwrite current saves (y/N): ")
        if confirm.lower() != 'y':
            print("Restoration cancelled.")
            return False
        
        try:
            # Create a backup of current state before restoring
            print("Creating backup of current state before restoration...")
            current_backup = self.create_backup()
            
            # Remove current save files (except backup folder)
            for item in self.save_dir.iterdir():
                if item.name != "backups" and item != Path(__file__):
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # Copy backup contents to save directory
            for item in Path(backup_path).iterdir():
                dest = self.save_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            
            print(f"Backup '{backup_name}' restored successfully!")
            if current_backup:
                print(f"Previous state backed up as: {current_backup.name}")
            return True
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def delete_backup(self, backup_choice=None):
        """Delete a specific backup"""
        backups = self.list_backups()
        
        if not backups:
            return False
        
        if backup_choice is None:
            try:
                choice = int(input("\nEnter backup number to delete: ")) - 1
                if choice < 0 or choice >= len(backups):
                    print("Invalid choice.")
                    return False
                backup_path = backups[choice]
            except (ValueError, IndexError):
                print("Invalid input.")
                return False
        else:
            if backup_choice < 1 or backup_choice > len(backups):
                print("Invalid backup number.")
                return False
            backup_path = backups[backup_choice - 1]
        
        backup_name = Path(backup_path).name
        
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete '{backup_name}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled.")
            return False
        
        try:
            shutil.rmtree(backup_path)
            print(f"Backup '{backup_name}' deleted successfully!")
            return True
        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Save Game Backup Manager")
    parser.add_argument("--save-dir", help="Path to save directory (default: current directory)")
    parser.add_argument("--backup-dir", help="Path to backup directory (default: ./backups)")
    parser.add_argument("--backup", action="store_true", help="Create a backup")
    parser.add_argument("--restore", type=int, help="Restore backup by number")
    parser.add_argument("--list", action="store_true", help="List all backups")
    parser.add_argument("--delete", type=int, help="Delete backup by number")
    
    args = parser.parse_args()
    
    # Initialize backup manager
    manager = SaveBackupManager(args.save_dir, args.backup_dir)
    
    # Handle command line arguments
    if args.backup:
        manager.create_backup()
    elif args.restore:
        manager.restore_backup(args.restore)
    elif args.list:
        manager.list_backups()
    elif args.delete:
        manager.delete_backup(args.delete)
    else:
        # Interactive mode
        while True:
            print("\n=== Save Game Backup Manager ===")
            print("1. Create backup")
            print("2. List backups")
            print("3. Restore backup")
            print("4. Delete backup")
            print("5. Exit")
            
            try:
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == "1":
                    manager.create_backup()
                elif choice == "2":
                    manager.list_backups()
                elif choice == "3":
                    manager.restore_backup()
                elif choice == "4":
                    manager.delete_backup()
                elif choice == "5":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please enter 1-5.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()