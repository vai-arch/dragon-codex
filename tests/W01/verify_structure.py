"""
Dragon's Codex - Directory Structure Verification
Verifies that all required directories exist and creates missing ones.
"""

from pathlib import Path


def verify_and_create_structure():
    """Verify and create project directory structure"""
    
    required_dirs = [
        # Data directories
        'data',
        'data/raw',
        'data/raw/books',
        'data/raw/wiki',
        'data/processed',
        'data/metadata',
        
        # Vector stores
        'vector_stores',
        
        # Source code
        'src',
        'src/ingestion',
        'src/retrieval',
        'src/query',
        'src/generation',
        'src/utils',
        'src/mcp',
        
        # Notebooks and tests
        'notebooks',
        'tests',
        
        # Logs
        'logs',
    ]
    
    print("=" * 60)
    print("Dragon's Codex - Directory Structure Verification")
    print("=" * 60)
    
    created = []
    existing = []
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            existing.append(dir_path)
            print(f"  ✓ {dir_path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
            print(f"  ✓ {dir_path} (created)")
    
    # Create .gitkeep files in important empty directories
    gitkeep_dirs = [
        'data/raw/books',
        'data/raw/wiki',
        'data/processed',
        'data/metadata',
        'vector_stores',
        'logs',
    ]
    
    for dir_path in gitkeep_dirs:
        gitkeep_file = Path(dir_path) / '.gitkeep'
        if not gitkeep_file.exists():
            gitkeep_file.touch()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Existing directories: {len(existing)}")
    print(f"  Created directories:  {len(created)}")
    print(f"  Total directories:    {len(required_dirs)}")
    
    if created:
        print("\n📁 Created directories:")
        for d in created:
            print(f"    - {d}")
    
    print("\n✓ Directory structure verified!")
    
    return True


def check_critical_files():
    """Check for critical configuration files"""
    print("\n" + "=" * 60)
    print("Critical Files Check")
    print("=" * 60)
    
    critical_files = {
        '.env': 'Environment configuration (copy from .env.template)',
        '.gitignore': 'Git ignore rules',
        'requirements.txt': 'Python dependencies',
        'README.md': 'Project documentation',
    }
    
    all_present = True
    
    for filename, description in critical_files.items():
        filepath = Path(filename)
        if filepath.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - {description}")
            all_present = False
    
    return all_present


def check_data_files():
    """Check for data files"""
    print("\n" + "=" * 60)
    print("Data Files Check")
    print("=" * 60)
    
    books_path = Path('data/raw/books')
    wiki_path = Path('data/raw/wiki')
    
    book_count = len(list(books_path.glob('*.txt')))
    wiki_count = len(list(wiki_path.glob('*.txt')))
    
    print(f"  Book files:  {book_count:,} (expected 15)")
    print(f"  Wiki files:  {wiki_count:,} (expected ~6000)")
    
    if book_count == 0:
        print("  ⚠ No book files found - add to data/raw/books/")
    if wiki_count == 0:
        print("  ⚠ No wiki files found - add to data/raw/wiki/")
    
    return book_count > 0 and wiki_count > 0


def main():
    """Main verification function"""
    print("\n")
    
    # Verify directory structure
    verify_and_create_structure()
    
    # Check critical files
    files_ok = check_critical_files()
    
    # Check data files
    data_ok = check_data_files()
    
    print("\n" + "=" * 60)
    print("Final Status")
    print("=" * 60)
    
    if files_ok and data_ok:
        print("  ✓ All checks passed!")
        print("  ✓ You're ready to proceed with development")
        return 0
    else:
        print("  ⚠ Some checks failed")
        if not files_ok:
            print("    - Missing critical configuration files")
        if not data_ok:
            print("    - Missing data files")
        print("\n  Please resolve issues before continuing")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
