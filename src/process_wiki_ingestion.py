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
    
    logger.info("REPROCESSING ALL WIKI DATA")
    logger.info("="*70)

    ingestionBooksFolder = Config().PROJECT_ROOT / "src/ingestion/books/"
    ingestionWikiFolder = Config().PROJECT_ROOT / "src/ingestion/wiki/"

    response = input("This is going to take a while, are you sure? (y/n): ").strip().lower()
        
    if response == 'n':
        return False

    if not run_command(ingestionWikiFolder + "pass_01_download_all_wiki_page_titles.py", "1"):
        return False

    if not run_command(ingestionWikiFolder + "pass_02_batch_scraper.py", "2"):
        return False
    
    if not run_command(ingestionWikiFolder + "pass_03_cleaning_duplicates.py", "3"):
        return False
    
    if not run_command(ingestionWikiFolder + "pass_04_build_redirect_mapping.py", "4"):
        return False
    
    if not run_command(ingestionWikiFolder + "pass_05_analyze_wiki_categories.py", "5"):
        return False
    
    if not run_command(ingestionWikiFolder + "pass_06_organize_wiki_by_type.py", "6"):
        return False

    if not run_command(ingestionWikiFolder + "pass_07_build_character_index.py", "7"):
        return False
    
    if not run_command(ingestionBooksFolder + "pass_08_book_chunker.py", "8"):
        return False
    
    if not run_command(ingestionBooksFolder + "pass_09_prophecy_magic_extractor.py", "9"):
        return False
 
    if not run_command(ingestionBooksFolder + "pass_10_create_wiki_chunks_chronology.py", "10"):
        return False
 
    if not run_command(ingestionBooksFolder + "pass_11_create_wiki_chunks_character.py", "11"):
        return False
 
    if not run_command(ingestionBooksFolder + "pass_12_create_wiki_chunks_chapterSummary.py", "12"):
        return False

    if not run_command(ingestionBooksFolder + "pass_13_create_wiki_chunks_concept.py", "13"):
        return False
  
    
    return True

def main():
    """Main entry point"""
    
    success = reprocess_all_books()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()