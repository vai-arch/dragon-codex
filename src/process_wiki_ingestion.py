"""
Reprocess Wiki Pipeline
Runs all steps needed for ingesting the wiki

"""

import sys
from src.utils.logger import get_logger
from src.utils.util_functions import run_command
from src.utils.config import Config

logger = get_logger(__name__)


def reprocess_all_books():
    """Download and processs all wiki"""
    
    logger.info("REPROCESSING ALL BWIKIOOKS")
    logger.info("="*70)

    ingestionBooksFolder = Config().PROJECT_ROOT / "src/ingestion/wiki/"

    response = input("This is going to take a while, are you sure? (y/n): ").strip().lower()
        
    if response == 'n':
        return False

    if not run_command(ingestionBooksFolder + "pass_01_download_all_wiki_page_titles.py", "1"):
        return False

    if not run_command(ingestionBooksFolder + "pass_02_batch_scraper.py", "2"):
        return False
    
    if not run_command(ingestionBooksFolder + "pass_03_build_redirect_mapping.py", "2"):
        return False
    
    return True

def main():
    """Main entry point"""
    
    success = reprocess_all_books()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()