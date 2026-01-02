conda activate dragon
# List of Python modules to run
$modules = @(
    # "src.ingestion.ing_01_parse_raw_books",
    # "src.ingestion.ing_02_download_all_wiki_page_titles",
    # "src.ingestion.ing_03_wiki_scrapper", 
    "src.processing.prc_01_process_books",
    "src.processing.prc_02_process_glossary",
    "src.processing.prc_03_create_fake_wiki_entries_for_glossary",
    "src.processing.prc_04_analyze_wiki_categories",
    "src.processing.prc_05_organize_wiki_by_type"
    "src.processing.prc_06_build_character_index",
    "src.processing.prc_07_build_prophecy_magic_and_timeline_index",
    "src.processing.prc_08_build_concept_index",
    "src.processing.prc_09_build_temporal_aliases",
    "src.processing.prc_10_build_bm25_index",
    "src.embedding.emb_01_create_chunks",
    "src.embedding.emb_02_enrich_chunks",
    "src.embedding.emb_03_embed_all_chunks",
    "src.embedding.emb_04_create_collections",
    "src.retrieval.testing.ret_test_01_test_baselines_retrieval_v1A",
    "src.retrieval.testing.ret_test_02_score_retrieval"
)

foreach ($module in $modules) {
    Write-Host "Running Python module: $module"
    python -m $module

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Python module $module failed. Halting further execution."
        exit $LASTEXITCODE
    }
}

Write-Host "✅ All Python modules completed successfully."
