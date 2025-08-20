#!/usr/bin/env python3
"""
Test script to verify CLI confirmation bypass functionality
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add the current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

def test_confirmation_bypass():
    """Test that CLI methods can skip confirmation prompts"""
    try:
        from backup import SaveBackupManager
        
        # Create a temporary test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            save_dir = temp_path / "saves"
            backup_dir = temp_path / "backups"
            
            # Create test save directory
            save_dir.mkdir()
            test_file = save_dir / "test.txt"
            test_file.write_text("test content")
            
            # Initialize backup manager
            manager = SaveBackupManager(save_dir, backup_dir, max_backups=5, game_name="TestGame")
            
            # Create a test backup
            backup_path = manager.create_backup("Test backup")
            if not backup_path:
                print("❌ Failed to create test backup")
                return False
            
            # Test restore with skip_confirmation=True (should not hang)
            print("🧪 Testing restore with skip_confirmation=True...")
            success = manager.restore_backup(1, skip_confirmation=True)
            if not success:
                print("❌ Restore with skip_confirmation failed")
                return False
            
            # Create another backup for delete test
            backup_path2 = manager.create_backup("Test backup 2")
            if not backup_path2:
                print("❌ Failed to create second test backup")
                return False
            
            # Test delete with skip_confirmation=True (should not hang)
            print("🧪 Testing delete with skip_confirmation=True...")
            success = manager.delete_backup(1, skip_confirmation=True)
            if not success:
                print("❌ Delete with skip_confirmation failed")
                return False
            
            print("✅ Confirmation bypass test passed")
            return True
            
    except Exception as e:
        print(f"❌ Confirmation bypass test failed: {e}")
        return False

def test_backward_compatibility():
    """Test that CLI methods still work with default parameters"""
    try:
        from backup import SaveBackupManager
        
        # Create a temporary test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            save_dir = temp_path / "saves"
            backup_dir = temp_path / "backups"
            
            # Create test save directory
            save_dir.mkdir()
            test_file = save_dir / "test.txt"
            test_file.write_text("test content")
            
            # Initialize backup manager
            manager = SaveBackupManager(save_dir, backup_dir, max_backups=5, game_name="TestGame")
            
            # Create a test backup
            backup_path = manager.create_backup("Test backup")
            if not backup_path:
                print("❌ Failed to create test backup")
                return False
            
            # Test that methods can still be called without skip_confirmation parameter
            # (We can't actually test the interactive part, but we can test the method signature)
            print("🧪 Testing backward compatibility...")
            
            # Check that methods accept the old signature
            try:
                # These should not error due to parameter mismatch
                # We won't actually call them to avoid the input() prompt
                restore_method = manager.restore_backup
                delete_method = manager.delete_backup
                
                # Verify the methods exist and have the right signature
                import inspect
                restore_sig = inspect.signature(restore_method)
                delete_sig = inspect.signature(delete_method)
                
                # Check that skip_confirmation parameter exists and has default value
                if 'skip_confirmation' not in restore_sig.parameters:
                    print("❌ restore_backup missing skip_confirmation parameter")
                    return False
                    
                if restore_sig.parameters['skip_confirmation'].default != False:
                    print("❌ restore_backup skip_confirmation default is not False")
                    return False
                    
                if 'skip_confirmation' not in delete_sig.parameters:
                    print("❌ delete_backup missing skip_confirmation parameter")
                    return False
                    
                if delete_sig.parameters['skip_confirmation'].default != False:
                    print("❌ delete_backup skip_confirmation default is not False")
                    return False
                
                print("✅ Backward compatibility test passed")
                return True
                
            except Exception as e:
                print(f"❌ Method signature test failed: {e}")
                return False
            
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def main():
    print("🧪 Running CLI Confirmation Bypass Tests")
    print("=" * 50)
    
    tests = [
        test_confirmation_bypass,
        test_backward_compatibility
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
        print("🎉 All tests passed! CLI confirmation bypass is working correctly.")
    else:
        print("⚠️  Some tests failed. There might be remaining issues.")

if __name__ == "__main__":
    main()
