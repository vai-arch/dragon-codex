"""
Dragon's Codex - Environment Setup Verification
Tests that all components are properly installed and configured.
"""

import sys
import os
from pathlib import Path


def test_python_version():
    """Verify Python version is 3.11+"""
    print("Testing Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.11+")
        return False


def test_imports():
    """Test all required imports"""
    print("\nTesting Python package imports...")
    
    packages = {
        'langchain': 'LangChain',
        'chromadb': 'ChromaDB',
        'dotenv': 'python-dotenv',
        'tqdm': 'tqdm',
        'markdown_it': 'markdown-it-py',
    }
    
    all_success = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ✗ {name} - {e}")
            all_success = False
    
    return all_success


def test_ollama():
    """Test Ollama connectivity"""
    print("\nTesting Ollama connection...")
    
    try:
        import subprocess
        result = subprocess.run(
            ['ollama', 'list'], 
            capture_output=True, 
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  ✓ Ollama is accessible")
            
            # Check for required models
            output = result.stdout
            models_found = {
                'nomic-embed-text': 'nomic-embed-text' in output,
                'llama3.1:8b': 'llama3.1' in output
            }
            
            for model, found in models_found.items():
                if found:
                    print(f"  ✓ Model {model} found")
                else:
                    print(f"  ✗ Model {model} not found - run: ollama pull {model}")
            
            return all(models_found.values())
        else:
            print(f"  ✗ Ollama error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("  ✗ Ollama not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("  ✗ Ollama connection timeout")
        return False
    except Exception as e:
        print(f"  ✗ Ollama test failed: {e}")
        return False


def test_directory_structure():
    """Verify project directory structure"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        'data',
        'data/raw',
        'data/raw/books',
        'data/raw/wiki',
        'data/processed',
        'data/metadata',
        'vector_stores',
        'src',
        'src/ingestion',
        'src/retrieval',
        'src/query',
        'src/generation',
        'src/utils',
        'notebooks',
        'tests',
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - missing")
            all_exist = False
    
    return all_exist


def test_env_file():
    """Check if .env file exists"""
    print("\nTesting configuration...")
    
    env_path = Path('.env')
    if env_path.exists():
        print("  ✓ .env file found")
        return True
    else:
        print("  ✗ .env file not found - copy from .env.template and configure")
        return False


def test_data_files():
    """Check if data files exist"""
    print("\nTesting data files...")
    
    books_path = Path('data/raw/books')
    wiki_path = Path('data/raw/wiki')
    
    results = []
    
    if books_path.exists():
        book_count = len(list(books_path.glob('*.txt')))
        if book_count >= 15:
            print(f"  ✓ Found {book_count} book files")
            results.append(True)
        elif book_count > 0:
            print(f"  ⚠ Found {book_count} book files - expected 15")
            results.append(True)  # Warning but not failure
        else:
            print(f"  ✗ No book files found in {books_path}")
            results.append(False)
    else:
        print(f"  ✗ Books directory not found")
        results.append(False)
    
    if wiki_path.exists():
        wiki_count = len(list(wiki_path.glob('*.txt')))
        if wiki_count > 5000:
            print(f"  ✓ Found {wiki_count} wiki files")
            results.append(True)
        elif wiki_count > 0:
            print(f"  ⚠ Found {wiki_count} wiki files - expected ~6000")
            results.append(True)  # Warning but not failure
        else:
            print(f"  ✗ No wiki files found in {wiki_path}")
            results.append(False)
    else:
        print(f"  ✗ Wiki directory not found")
        results.append(False)
    
    return all(results)


def main():
    """Run all tests"""
    print("=" * 60)
    print("Dragon's Codex - Setup Verification")
    print("=" * 60)
    
    results = {
        'Python Version': test_python_version(),
        'Package Imports': test_imports(),
        'Ollama': test_ollama(),
        'Directory Structure': test_directory_structure(),
        'Environment File': test_env_file(),
        'Data Files': test_data_files(),
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print("=" * 60)
    
    if all(results.values()):
        print("\n🎉 All tests passed! You're ready to begin Week 1 development.")
        return 0
    else:
        print("\n⚠ Some tests failed. Please resolve issues before continuing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
