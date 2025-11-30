# WoT Book Structure - Parsing Documentation

## Source Files

- Format: Plain text (.txt)
- Encoding: UTF-8
- Naming: [Number]-[Title].txt

## Structure Markers

- PROLOGUE → Chapter 0, type: prologue
- CHAPTER → Chapter 1+, type: chapter
- EPILOGUE → Chapter (max+1), type: epilogue
- GLOSSARY → Glossary section

## Parsing Script

- Location: parse_all_books.py
- Output: JSON files (same name, .json extension)
- Total books: 15 (00-14)
- Total chapters: ~450

## Verification

- Script: tests/W01/verify_book_parsing.py
- Status: ✓ PASSED
- Date verified: [Today's date]

## Notes

- All chapter content preserved completely
- Glossary terms with pronunciations extracted
- Chapter numbering: Prologue=0, Chapters=1+, Epilogue=last+1

## JSON STRUCTURE

´´´ json
{
  "book_number": "01",
  "book_name": "The_Eye_of_the_World",
  "chapters": [
    {
      "number": 0,
      "type": "prologue",
      "title": "Dragonmount",
      "content": "Full chapter text..."
    },
    {
      "number": 1,
      "type": "chapter",
      "title": "An Empty Road",
      "content": "Full chapter text..."
    },
    {
      "number": 54,
      "type": "epilogue",
      "title": "Endings",
      "content": "Full epilogue text..."
    }
  ],
  "glossary": [
    {
      "term": "Aes Sedai",
      "pronunciation": "EYEZ seh-DEYE",
      "description": "Wielders of the One Power..."
    }
  ]
}
´´´
