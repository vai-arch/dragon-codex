"""
Reprocess Books Pipeline
Runs all steps needed when raw book files are modified

"""

import sys
from src.utils.logger import get_logger
from src.utils.util_files_functions import run_command
from src.utils.config import Config

logger = get_logger(__name__)


def reprocess_all_books():
    """Reprocess all books from raw TXT to final processed output"""
    
    logger.info("REPROCESSING ALL BOOKS")
    logger.info("="*70)

    ingestionBooksFolder = Config().PROJECT_ROOT / "src/ingestion/books/"

    if not run_command(ingestionBooksFolder / "pass_01_save_parsed_books.py", "1"):
        return False

    if not run_command(ingestionBooksFolder / "pass_02_create_books_structured.py", "2"):
        return False
        
    # These 2 scripts depend on wiki ingestion so they are now run in process_wiki_ingestion.py
    
    # if not run_command(ingestionBooksFolder / "pass_03_check_build_glossary_wiki_mapping.py", "3"):
    #     return False
    
    # if not run_command(ingestionBooksFolder / "pass_04_create_fake_wiki_entries_for_glossary.py", "3"):
    #     return False

    return True

def main():
    """Main entry point"""
    
    success = reprocess_all_books()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()