# Run order

## First download_wiki_pages.py

    WoT Wiki Complete Page List Downloader
    Uses MediaWiki API to get ALL pages from the WoT Fandom wiki

    This script fetches every single page title from the wiki, including:

    - Characters, Locations, Objects, Concepts, Events, Organizations
    - Books, Chapters, Prophecies, Terminology
    - Everything!

    Author: Dragon's Codex Project

    **Press `y` when asked**

    **What it does:**

    - Gets ALL page titles from WoT wiki via API
    - Saves to `data/auxiliary/wiki/wiki_all_page_titles.json`
    - You'll get ~15,000 page titles (not just 6,000 characters!)

    **Output you'll see:**

    Total Pages: 15,234
    ✓ Saved to: data/auxiliary/wiki/wiki_all_page_titles.json

## Second batch_scraper.py

    It will ask you if you want to do a test. This is usefull if you don't want to scrape the whole thing.
    If you say no, then it will ask you if you want to scrape everything. Press yes.
    It uses the list of pages generated in step 1 (data/auxiliary/wiki/wiki_all_page_titles.json)
    It uses wiki_scraper.py that gets all the information from every page