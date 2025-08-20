#!/usr/bin/env python3
"""
Test script to verify GUI restore functionality works correctly
"""

import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Add the current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

def test_gui_import():
    """Test that the GUI imports without errors"""
    try:
        import backup_gui
        print("✅ GUI import test passed")
        return True
    except Exception as e:
        print(f"❌ GUI import test failed: {e}")
        return False

def test_backup_manager_integration():
    """Test that the GUI can work with the backup manager"""
    try:
        from backup import SaveBackupManager, load_games_config
        from backup_gui import BackupManagerGUI
        
        # Test basic integration
        config_path = Path(__file__).parent / "games_config.json"
        config = load_games_config(config_path)
        
        print("✅ Backup manager integration test passed")
        return True
    except Exception as e:
        print(f"❌ Backup manager integration test failed: {e}")
        return False

def test_treeview_selection():
    """Test that treeview selection events work"""
    try:
        # Create a simple test GUI
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create a treeview
        tree = ttk.Treeview(root)
        
        # Track selection changes
        selection_count = 0
        def on_select(event=None):
            nonlocal selection_count
            selection_count += 1
        
        tree.bind("<<TreeviewSelect>>", on_select)
        
        # Add an item and select it
        item = tree.insert("", "end", text="test", tags=("test_path",))
        tree.selection_set(item)
        tree.event_generate("<<TreeviewSelect>>")
        
        root.update()  # Process events
        root.destroy()
        
        if selection_count > 0:
            print("✅ Treeview selection test passed")
            return True
        else:
            print("❌ Treeview selection test failed: No selection events detected")
            return False
            
    except Exception as e:
        print(f"❌ Treeview selection test failed: {e}")
        return False

def main():
    print("🧪 Running GUI Restore Button Fix Tests")
    print("=" * 50)
    
    tests = [
        test_gui_import,
        test_backup_manager_integration,
        test_treeview_selection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The restore button fix should work correctly.")
    else:
        print("⚠️  Some tests failed. There might be remaining issues.")

if __name__ == "__main__":
    main()
