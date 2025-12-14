conda activate dragon
# List of Python modules to run
$modules = @(
    "src.ingestion.books.pass_01_save_parsed_books",
    "src.ingestion.books.pass_02_create_books_structured",
    "src.ingestion.books.pass_03_check_build_glossary_wiki_mapping", # this module does not belong here, it depends on the wiki pages already downlaoded
    "src.ingestion.books.pass_04_create_fake_wiki_entries_for_glossary"
    #"src.ingestion.wiki.pass_15_create_chunks",
    #"src.ingestion.wiki.pass_16_enrich_chunks",
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
