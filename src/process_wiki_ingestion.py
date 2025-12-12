"""
Reprocess Wiki Pipeline
Runs all steps needed for ingesting the wiki

"""

import sys
from src.utils.logger import get_logger
from src.utils.util_files_functions import run_command, remove_file, copy_files
from src.utils.config import Config

logger = get_logger(__name__)


def reprocess_all_books():
    """Download and processs all wiki"""
    
    logger.info("REPROCESSING ALL WIKI DATA")
    logger.info("="*70)

    ingestionBooksFolder = Config().PROJECT_ROOT / "src/ingestion/books/"
    ingestionWikiFolder = Config().PROJECT_ROOT / "src/ingestion/wiki/"
    retrievalWikiFolder = Config().PROJECT_ROOT / "src/retrieval/"

    # response = input("This is going to take a while, are you sure? (y/n): ").strip().lower()
        
    # if response == 'n':
    #     return False

    # if not run_command(ingestionWikiFolder / "pass_01_download_all_wiki_page_titles.py", "1"):
    #     return False

    # if not run_command(ingestionWikiFolder / "pass_02_batch_scraper.py", "2"):
    #     return False
    
    # if not run_command(ingestionWikiFolder / "pass_03_cleaning_duplicates.py", "3"):
    #     return False
    
    # if not run_command(ingestionWikiFolder / "pass_04_build_redirect_mapping.py", "4"):
    #     return False
    
    # if not run_command(ingestionBooksFolder / "pass_03_check_build_glossary_wiki_mapping.py", "3"):
    #     return False
    
    # if not run_command(ingestionBooksFolder / "pass_04_create_fake_wiki_entries_for_glossary.py", "3"):
    #     return False

    # if not run_command(ingestionWikiFolder / "pass_05_analyze_wiki_categories.py", "5"):
    #     return False
    
    # if not run_command(ingestionWikiFolder / "pass_06_organize_wiki_by_type.py", "6"):
    #     return False

    # if not run_command(ingestionWikiFolder / "pass_07_build_character_index.py", "7"):
    #     return False
    
    # if not run_command(ingestionBooksFolder / "pass_08_book_chunker.py", "8"):
    #     return False
    
    # if not run_command(ingestionWikiFolder / "pass_09_build_prophecy_and_magic_index.py", "9"):
    #     return False
    
    # if not run_command(ingestionWikiFolder / "pass_10_build_concept_index.py", "10"):
    #     return False
 
    # if not run_command(ingestionWikiFolder / "pass_11_create_wiki_chunks_character.py", "11"):
    #     return False
 
    # if not run_command(ingestionWikiFolder / "pass_12_create_wiki_chunks_chapterSummary.py", "12"):
    #     return False
 
    # if not run_command(ingestionWikiFolder / "pass_13_create_wiki_chunks_chronology.py", "13"):
    #     return False

    if not run_command(ingestionWikiFolder / "pass_14_create_wiki_chunks_concept.py", "14"):
        return False
  

  
    if not run_command(ingestionWikiFolder / "pass_16_enrich_character_concepts_magic_prophecies.py", "16"):
        return False

    remove_file(Config().FILE_EMBEDDING_CHECKPOINT) 

    if not run_command(retrievalWikiFolder / "pass_17_embed_all_chunks.py", "17"):
        return False

    if not run_command(retrievalWikiFolder / "pass_18_create_collections.py", "18"):
        return False

    return True

def main():
    """Main entry point"""
    
    success = reprocess_all_books()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()