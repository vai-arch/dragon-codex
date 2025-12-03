"""
Cleanup Script for Case-Collision Duplicates
Finds duplicate files (case-variants), keeps the largest, deletes the rest.
If the kept file has _DUPLICATE_N in name, renames it to remove the suffix.

Usage:
    python cleanup_duplicates.py <wiki_directory>
    
Example:
    python cleanup_duplicates.py C:\path\to\data\raw\wiki
"""

import sys
from pathlib import Path
from collections import defaultdict
import re

from src.utils.config import Config
from src.utils.logger import get_logger

wiki_dir = Config().WIKI_PATH

def find_duplicate_groups(wiki_dir):
    """
    Find all files that are case-variants of each other.
    
    Args:
        wiki_dir: Path to wiki directory
        
    Returns:
        dict: {lowercase_name: [list of Path objects]}
    """
    wiki_path = Path(wiki_dir)
    
    # Group files by lowercase name (case-insensitive matching)
    groups = defaultdict(list)
    
    for file in wiki_path.glob('*.txt'):
        # Get name without extension
        name = file.stem
        
        # Strip _DUPLICATE_N suffix to group case-variants together
        # "Perrin_aybara_DUPLICATE_1" -> "Perrin_aybara"
        clean_name = re.sub(r'_DUPLICATE_\d+$', '', name)
        
        # Group by lowercase version of clean name
        groups[clean_name.lower()].append(file)
    
    # Filter to only groups with multiple files (duplicates)
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}
    
    return duplicate_groups


def analyze_duplicates(duplicate_groups):
    """
    Analyze duplicate groups and determine which to keep/delete.
    
    Args:
        duplicate_groups: Dict of {lowercase_name: [files]}
        
    Returns:
        list: Actions to take [{keep, delete, rename}]
    """
    actions = []
    
    for group_name, files in duplicate_groups.items():
        # Get file sizes
        file_info = []
        for file in files:
            size = file.stat().st_size
            has_duplicate_suffix = bool(re.search(r'_DUPLICATE_\d+$', file.stem))
            file_info.append({
                'path': file,
                'name': file.name,
                'size': size,
                'has_duplicate_suffix': has_duplicate_suffix
            })
        
        # Sort by size (largest first)
        file_info.sort(key=lambda x: x['size'], reverse=True)
        
        # Keep the largest
        largest = file_info[0]
        to_delete = file_info[1:]
        
        # Check if we need to rename the largest (if it has _DUPLICATE suffix)
        rename_action = None
        if largest['has_duplicate_suffix']:
            # Remove _DUPLICATE_N from name
            new_name = re.sub(r'_DUPLICATE_\d+', '', largest['path'].stem) + '.txt'
            new_path = largest['path'].parent / new_name
            rename_action = {
                'from': largest['path'],
                'to': new_path
            }
        
        actions.append({
            'group': group_name,
            'keep': largest,
            'delete': to_delete,
            'rename': rename_action
        })
    
    return actions


def print_analysis(actions):
    """
    Print analysis of what will be done.
    
    Args:
        actions: List of action dicts
    """
    print("\n" + "="*80)
    print("DUPLICATE ANALYSIS")
    print("="*80)
    
    total_groups = len(actions)
    total_to_delete = sum(len(a['delete']) for a in actions)
    total_to_rename = sum(1 for a in actions if a['rename'])
    
    print(f"\nFound {total_groups} duplicate groups")
    print(f"Will delete {total_to_delete} files")
    print(f"Will rename {total_to_rename} files")
    
    print("\n" + "-"*80)
    print("DETAILED BREAKDOWN")
    print("-"*80)
    
    for action in actions[:20]:  # Show first 20
        print(f"\nGroup: {action['group']}")
        print(f"  ✓ KEEP:   {action['keep']['name']:50s} ({action['keep']['size']:,} bytes)")
        
        for del_file in action['delete']:
            print(f"  ✗ DELETE: {del_file['name']:50s} ({del_file['size']:,} bytes)")
        
        if action['rename']:
            print(f"  ➜ RENAME: {action['rename']['from'].name}")
            print(f"         TO: {action['rename']['to'].name}")
    
    if len(actions) > 20:
        print(f"\n... and {len(actions) - 20} more groups")


def execute_cleanup(actions, output_dir):
    """
    Execute the cleanup actions.
    
    Args:
        actions: List of action dicts
        output_dir: Directory where files are located
    """
    print("\n" + "="*80)
    print("EXECUTING CLEANUP")
    print("="*80)
    
    # Create deletion log
    log_file = Path(output_dir) / 'cleanup_log.txt'
    
    deleted_count = 0
    renamed_count = 0
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("CLEANUP LOG\n")
        log.write("="*80 + "\n\n")
        
        for action in actions:
            log.write(f"\nGroup: {action['group']}\n")
            log.write(f"  Kept: {action['keep']['name']} ({action['keep']['size']:,} bytes)\n")
            
            # Delete smaller files
            for del_file in action['delete']:
                try:
                    del_file['path'].unlink()
                    deleted_count += 1
                    log.write(f"  Deleted: {del_file['name']} ({del_file['size']:,} bytes)\n")
                    print(f"  ✗ Deleted: {del_file['name']}")
                except Exception as e:
                    log.write(f"  ERROR deleting {del_file['name']}: {e}\n")
                    print(f"  ✗ ERROR: Could not delete {del_file['name']}: {e}")
            
            # Rename if needed
            if action['rename']:
                try:
                    action['rename']['from'].rename(action['rename']['to'])
                    renamed_count += 1
                    log.write(f"  Renamed: {action['rename']['from'].name} -> {action['rename']['to'].name}\n")
                    print(f"  ➜ Renamed: {action['rename']['from'].name} -> {action['rename']['to'].name}")
                except Exception as e:
                    log.write(f"  ERROR renaming: {e}\n")
                    print(f"  ✗ ERROR: Could not rename: {e}")
    
    print("\n" + "="*80)
    print("CLEANUP COMPLETE")
    print("="*80)
    print(f"\n✓ Deleted {deleted_count} files")
    print(f"✓ Renamed {renamed_count} files")
    print(f"✓ Log saved to: {log_file}")


def main():
    """Main function."""
    print("\n" + "="*80)
    print("DUPLICATE FILE CLEANUP SCRIPT")
    print("="*80)
    
    if not wiki_dir.exists():
        print(f"\n✗ Error: Directory not found: {wiki_dir}")
        sys.exit(1)
    
    if not wiki_dir.is_dir():
        print(f"\n✗ Error: Not a directory: {wiki_dir}")
        sys.exit(1)
    
    print(f"\nWiki directory: {wiki_dir}")
    
    # Step 1: Find duplicate groups
    print("\n🔍 Scanning for duplicate files...")
    duplicate_groups = find_duplicate_groups(wiki_dir)
    
    if not duplicate_groups:
        print("\n✓ No duplicates found! Directory is clean.")
        return
    
    print(f"✓ Found {len(duplicate_groups)} duplicate groups")
    
    # Step 2: Analyze what to do
    print("\n📊 Analyzing duplicates...")
    actions = analyze_duplicates(duplicate_groups)
    
    # Step 3: Show analysis
    print_analysis(actions)
    
    # Step 4: Confirm
    print("\n" + "="*80)
    response = input("\nProceed with cleanup? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n✗ Cleanup cancelled")
        return
    
    # Step 5: Execute
    execute_cleanup(actions, wiki_dir)
    
    print("\n✓ Done!\n")


if __name__ == "__main__":
    main()
