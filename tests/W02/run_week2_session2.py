"""
Week 2 Session 2 - Master Runner Script

Executes all Session 2 tasks in the correct order:
1. Create books_structured.json
2. Verify chapters
3. Build character list

Dragon's Codex - Wheel of Time RAG System
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_step(step_num, total_steps, description):
    """Print step information"""
    print(f"\n[{step_num}/{total_steps}] {description}")
    print("-" * 80)

def run_script(script_path: str, description: str) -> bool:
    """
    Run a Python script and return success status.
    
    Args:
        script_path: Path to the Python script
        description: Human-readable description
    
    Returns:
        True if script succeeded, False otherwise
    """
    try:
        print(f"\nRunning: {script_path}")
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {description}: {str(e)}")
        return False

def check_prerequisites() -> bool:
    """
    Check that required directories and files exist.
    
    Returns:
        True if all prerequisites are met, False otherwise
    """
    print_header("Checking Prerequisites")
    
    required_paths = [
        'data/raw/books',
        'build_character_list.py',
        'verify_chapters.py',
        'create_books_structured.py'
    ]
    
    issues = []
    
    for path_str in required_paths:
        path = Path(path_str)
        if not path.exists():
            issues.append(f"Missing: {path_str}")
            print(f"❌ {path_str}")
        else:
            print(f"✅ {path_str}")
    
    # Check for book JSON files
    book_files = list(Path('data/raw/books').glob('*.json')) if Path('data/raw/books').exists() else []
    if len(book_files) < 15:
        issues.append(f"Expected 15 book JSON files, found {len(book_files)}")
        print(f"❌ Found only {len(book_files)} book JSON files (expected 15)")
    else:
        print(f"✅ Found {len(book_files)} book JSON files")
    
    if issues:
        print("\n⚠️  Prerequisites not met:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("\n✅ All prerequisites met!")
    return True

def create_output_directories():
    """Ensure output directories exist"""
    directories = [
        'data/processed',
        'data/metadata'
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory ready: {dir_path}")

def main():
    """Main execution"""
    start_time = datetime.now()
    
    print_header("Dragon's Codex - Week 2 Session 2 Master Runner")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("This script will execute all Week 2 Session 2 tasks:")
    print("  1. Create books_structured.json (consolidate all books)")
    print("  2. Verify chapters (quality check)")
    print("  3. Build character list (extract from glossaries)")
    print("\nEstimated time: 10-15 minutes")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Cannot proceed. Please fix the issues above.")
        return 1
    
    # Create output directories
    print_header("Creating Output Directories")
    create_output_directories()
    
    # Define tasks
    tasks = [
        {
            'script': 'create_books_structured.py',
            'description': 'Create books_structured.json',
            'step': 1
        },
        {
            'script': 'verify_chapters.py',
            'description': 'Verify chapter extraction',
            'step': 2
        },
        {
            'script': 'build_character_list.py',
            'description': 'Build character list',
            'step': 3
        }
    ]
    
    total_steps = len(tasks)
    results = []
    
    # Execute tasks
    for task in tasks:
        print_step(task['step'], total_steps, task['description'])
        success = run_script(task['script'], task['description'])
        results.append({
            'task': task['description'],
            'success': success
        })
        
        if not success:
            print(f"\n⚠️  Task failed. You may want to check the output above.")
            print("Continuing with remaining tasks...\n")
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("Session 2 Summary")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:   {duration.total_seconds():.1f} seconds\n")
    
    print("Task Results:")
    all_success = True
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['task']}")
        if not result['success']:
            all_success = False
    
    print("\n" + "=" * 80)
    if all_success:
        print("✅ Week 2 Session 2 Complete!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Review the output files:")
        print("     - data/processed/books_structured.json")
        print("     - data/metadata/chapter_verification_report.json")
        print("     - data/metadata/character_names_initial.json")
        print("  2. Perform manual spot-checks on suggested chapters")
        print("  3. Review WEEK2_SESSION2_GUIDE.md for next steps")
        print("\nReady to proceed to Week 2 Session 3!")
        return 0
    else:
        print("⚠️  Week 2 Session 2 Completed with Warnings")
        print("=" * 80)
        print("\nSome tasks failed. Please review the output above.")
        print("Check the individual script outputs for details.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)