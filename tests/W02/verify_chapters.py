"""
Verify chapter extraction and count total chapters.

Week 2 Session 2 - Dragon's Codex
Validates that all chapters were extracted correctly from the 15 WoT books.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def load_config():
    """Load basic configuration"""
    return {
        'books_json_path': 'data/raw/books',
        'output_report': 'data/metadata/chapter_verification_report.json'
    }

def verify_chapters(books_path: str) -> dict:
    """
    Verify chapter extraction from all books.
    
    Returns detailed statistics and validation results.
    """
    results = {
        'books': [],
        'summary': {
            'total_books': 0,
            'total_chapters': 0,
            'total_prologues': 0,
            'total_epilogues': 0,
            'total_regular_chapters': 0,
            'books_with_errors': 0,
            'errors': []
        }
    }
    
    # Get all JSON book files
    book_files = sorted(Path(books_path).glob('*.json'))
    
    print("\nDragon's Codex - Chapter Verification")
    print("Week 2 Session 2")
    print("=" * 70)
    print(f"\nProcessing {len(book_files)} books...\n")
    
    for book_file in book_files:
        try:
            with open(book_file, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            
            book_num = book_data.get('book_number', 'unknown')
            book_name = book_data.get('book_name', 'unknown')
            chapters = book_data.get('chapters', [])
            glossary = book_data.get('glossary', [])
            
            # Count chapter types
            chapter_counts = {
                'prologue': 0,
                'chapter': 0,
                'epilogue': 0
            }
            
            chapter_numbers = []
            chapter_issues = []
            
            for chapter in chapters:
                ch_type = chapter.get('type', 'unknown')
                ch_num = chapter.get('number', -1)
                ch_title = chapter.get('title', '').strip()
                ch_content = chapter.get('content', '').strip()
                
                # Count by type
                if ch_type in chapter_counts:
                    chapter_counts[ch_type] += 1
                
                # Collect chapter numbers
                chapter_numbers.append(ch_num)
                
                # Validate chapter
                if not ch_title:
                    chapter_issues.append(f"Chapter {ch_num} has no title")
                
                if not ch_content:
                    chapter_issues.append(f"Chapter {ch_num} '{ch_title}' has no content")
                
                if len(ch_content) < 100:
                    chapter_issues.append(f"Chapter {ch_num} '{ch_title}' has suspiciously short content ({len(ch_content)} chars)")
            
            # Check for gaps in chapter numbering (for regular chapters)
            regular_chapters = [ch for ch in chapters if ch.get('type') == 'chapter']
            regular_nums = sorted([ch.get('number', -1) for ch in regular_chapters])
            
            expected_nums = list(range(1, len(regular_chapters) + 1))
            if regular_nums != expected_nums:
                chapter_issues.append(f"Chapter numbering issue: expected {expected_nums[:5]}... got {regular_nums[:5]}...")
            
            # Build book result
            book_result = {
                'book_number': book_num,
                'book_name': book_name,
                'total_chapters': len(chapters),
                'prologues': chapter_counts['prologue'],
                'regular_chapters': chapter_counts['chapter'],
                'epilogues': chapter_counts['epilogue'],
                'glossary_entries': len(glossary),
                'has_issues': len(chapter_issues) > 0,
                'issues': chapter_issues,
                'chapter_numbers': chapter_numbers
            }
            
            results['books'].append(book_result)
            
            # Update summary
            results['summary']['total_books'] += 1
            results['summary']['total_chapters'] += len(chapters)
            results['summary']['total_prologues'] += chapter_counts['prologue']
            results['summary']['total_regular_chapters'] += chapter_counts['chapter']
            results['summary']['total_epilogues'] += chapter_counts['epilogue']
            
            if chapter_issues:
                results['summary']['books_with_errors'] += 1
                results['summary']['errors'].extend([f"Book {book_num}: {issue}" for issue in chapter_issues])
            
            # Print book info
            status = "✅" if not chapter_issues else "⚠️"
            print(f"{status} Book {book_num:>2}: {book_name}")
            print(f"   Chapters: {len(chapters):3} | P:{chapter_counts['prologue']} Ch:{chapter_counts['chapter']} E:{chapter_counts['epilogue']} | Glossary: {len(glossary)}")
            
            if chapter_issues:
                for issue in chapter_issues[:3]:  # Show first 3 issues
                    print(f"   ⚠️  {issue}")
                if len(chapter_issues) > 3:
                    print(f"   ... and {len(chapter_issues) - 3} more issues")
            
        except Exception as e:
            error_msg = f"Error processing {book_file.name}: {str(e)}"
            print(f"❌ {error_msg}")
            results['summary']['errors'].append(error_msg)
            results['summary']['books_with_errors'] += 1
    
    return results

def print_summary(results: dict):
    """Print verification summary"""
    summary = results['summary']
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Books processed: {summary['total_books']}/15")
    print(f"Total chapters: {summary['total_chapters']}")
    print(f"  - Prologues: {summary['total_prologues']}")
    print(f"  - Regular chapters: {summary['total_regular_chapters']}")
    print(f"  - Epilogues: {summary['total_epilogues']}")
    print(f"\nBooks with issues: {summary['books_with_errors']}")
    
    if summary['errors']:
        print(f"\n⚠️  Issues found: {len(summary['errors'])}")
        print("\nFirst 5 issues:")
        for error in summary['errors'][:5]:
            print(f"  - {error}")
        if len(summary['errors']) > 5:
            print(f"  ... and {len(summary['errors']) - 5} more")
    else:
        print("\n✅ No issues found!")
    
    # Chapter distribution
    print("\nChapter distribution by book:")
    for book in results['books']:
        print(f"  Book {book['book_number']:>2}: {book['total_chapters']:3} chapters")
    
    # Expected chapter count check
    expected_range = (400, 500)  # From the plan
    actual = summary['total_chapters']
    if expected_range[0] <= actual <= expected_range[1]:
        print(f"\n✅ Total chapters ({actual}) within expected range {expected_range}")
    else:
        print(f"\n⚠️  Total chapters ({actual}) outside expected range {expected_range}")

def spot_check_chapters(results: dict, num_samples: int = 20):
    """
    Suggest random chapters for manual spot-checking.
    """
    import random
    
    print("\n" + "=" * 70)
    print(f"SPOT CHECK: {num_samples} RANDOM CHAPTERS")
    print("=" * 70)
    print("\nManually verify these chapters have correct content:\n")
    
    # Collect all chapters
    all_chapters = []
    for book in results['books']:
        book_num = book['book_number']
        book_name = book['book_name']
        for ch_num in book['chapter_numbers']:
            all_chapters.append({
                'book_num': book_num,
                'book_name': book_name,
                'chapter_num': ch_num
            })
    
    # Random sample
    if len(all_chapters) >= num_samples:
        samples = random.sample(all_chapters, num_samples)
        for i, ch in enumerate(samples, 1):
            print(f"{i:2}. Book {ch['book_num']:>2} ({ch['book_name'][:30]:30}) - Chapter {ch['chapter_num']}")
    else:
        print(f"Not enough chapters for {num_samples} samples (only {len(all_chapters)} available)")

def save_report(results: dict, output_path: str):
    """Save verification report to JSON"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Verification report saved to: {output_path}")

def main():
    """Main execution"""
    config = load_config()
    
    # Run verification
    results = verify_chapters(config['books_json_path'])
    
    # Print summary
    print_summary(results)
    
    # Spot check suggestions
    spot_check_chapters(results)
    
    # Save report
    save_report(results, config['output_report'])
    
    print("\n" + "=" * 70)
    print("✅ Chapter verification complete!")
    print("=" * 70)

if __name__ == '__main__':
    main()