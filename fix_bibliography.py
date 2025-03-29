#!/usr/bin/env python3
"""
Fix BibTeX bibliography by adding DOIs, removing redundant fields,
and standardizing titles based on Crossref data.
"""

import argparse
import bibtexparser
import requests
import time
from difflib import SequenceMatcher
from bibtexparser.bwriter import BibTexWriter

def similar(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_doi_from_crossref(entry, similarity_threshold=0.75, max_results=10):
    """
    Query Crossref API to find DOI and standardized title.
    Uses multiple fields for more accurate results.
    """
    # Extract data from entry
    title = entry.get('title', '').strip('{}')
    authors = entry.get('author', '').split(' and ')
    year = entry.get('year', '')
    
    # Build initial query with title
    query = title
    
    # Create more specific query if possible
    if authors and len(authors) > 0:
        # Extract last name of first author
        first_author_lastname = authors[0].split(',')[0] if ',' in authors[0] else authors[0].split()[-1]
        query = f"{first_author_lastname} {title}"
    
    print(f"  Searching Crossref for: {query[:60]}...")
    
    # Prepare API call
    base_url = 'https://api.crossref.org/works'
    params = {
        'query.bibliographic': query,
        'rows': max_results,
    }
    
    # Add filters if available
    if year:
        params['filter'] = f'from-pub-date:{year},until-pub-date:{year}'
    
    # Make API request
    headers = {'User-Agent': 'BibtexFixer/1.0 (mailto:example@example.com)'}
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Print number of results found
        total_results = data['message']['total-results']
        print(f"  Found {total_results} potential matches from Crossref")
        
        # Check if we got any results
        if total_results == 0:
            return None, None
        
        # Process results to find best match
        best_match = None
        best_similarity = 0
        best_title = None
        
        for item in data['message']['items']:
            if 'title' not in item or not item['title']:
                continue
            
            current_title = item['title'][0]
            current_similarity = similar(title, current_title)
            
            # If we have authors, check if they match to improve accuracy
            author_match = 1.0
            if authors and 'author' in item:
                item_authors = [f"{a.get('given', '')} {a.get('family', '')}" for a in item['author']]
                author_matches = []
                for author in authors:
                    best_author_match = max([similar(author, ia) for ia in item_authors] or [0])
                    author_matches.append(best_author_match)
                if author_matches:
                    author_match = sum(author_matches) / len(author_matches)
            
            # Combined score - more weight on title but author match matters
            combined_score = (current_similarity * 0.7) + (author_match * 0.3)
            
            # Get DOI
            current_doi = item.get('DOI')
            
            if combined_score > best_similarity and current_doi:
                best_similarity = combined_score
                best_match = current_doi
                best_title = current_title
                print(f"  Found potential match (score: {combined_score:.2f}): {current_title[:60]}...")
        
        # Only return if we're confident in the match
        if best_similarity >= similarity_threshold:
            return best_match, best_title
            
        return None, None
        
    except requests.exceptions.RequestException as e:
        print(f"  API request error: {e}")
        return None, None

def process_bibliography(input_file, output_file, remove_fields=None, similarity_threshold=0.75):
    """
    Main function to process bibliography:
    1. Add DOIs
    2. Remove specified fields
    3. Standardize titles
    4. Preserve title case
    """
    # Default fields to remove if not specified
    if remove_fields is None:
        remove_fields = []
    
    # Parse input file
    with open(input_file, 'r', encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    
    processed = 0
    total_entries = len(bib_database.entries)
    
    # Process each entry
    for entry in bib_database.entries:
        processed += 1
        print(f"\nProcessing entry {processed}/{total_entries}: {entry.get('ID', 'Unknown ID')}")
        
        # Check if DOI already exists
        existing_doi = entry.get('doi')
        
        # Get DOI and standardized title from Crossref
        crossref_doi, standardized_title = get_doi_from_crossref(entry, similarity_threshold)
        
        # Compare DOIs if both exist
        if existing_doi and crossref_doi:
            if existing_doi.lower() != crossref_doi.lower():
                print(f"  ⚠️ WARNING: DOI mismatch!")
                print(f"  ⚠️ Existing DOI: {existing_doi}")
                print(f"  ⚠️ Crossref DOI: {crossref_doi}")
                print(f"  ✅ Using Crossref DOI as it's likely more accurate")
        
        if crossref_doi:
            print(f"  Found DOI: {crossref_doi}")
            entry['doi'] = crossref_doi
            
            # Update title with standardized version while preserving case
            if standardized_title:
                print(f"  Updating title to: {standardized_title}")
                # Use braces to preserve case in LaTeX
                entry['title'] = f"{{{standardized_title}}}"
        elif not existing_doi:
            print("  No matching DOI found")
        
        # Remove specified fields
        for field in remove_fields:
            if field in entry:
                del entry[field]
                print(f"  Removed field: {field}")
        
        # Rate limiting to be nice to the API
        if processed < total_entries:
            time.sleep(1)
    
    # Write to output file
    writer = BibTexWriter()
    writer.indent = '  '
    writer.comma_first = False
    
    with open(output_file, 'w', encoding='utf-8') as bibtex_file:
        bibtex_file.write(writer.write(bib_database))
    
    print(f"\nProcessing complete! Output saved to {output_file}")

def main():
    """Parse arguments and run the script."""
    parser = argparse.ArgumentParser(description='Fix BibTeX bibliography by adding DOIs and standardizing titles.')
    parser.add_argument('input_file', help='Input BibTeX file')
    parser.add_argument('output_file', help='Output BibTeX file')
    parser.add_argument('--remove', nargs='+', default=['organization', 'abstract', 'keywords'],
                        help='List of fields to remove (default: organization abstract keywords)')
    parser.add_argument('--threshold', type=float, default=0.75,
                        help='Similarity threshold for accepting matches (0.0-1.0, default: 0.75)')
    
    args = parser.parse_args()
    
    process_bibliography(
        args.input_file, 
        args.output_file, 
        args.remove, 
        args.threshold
    )

if __name__ == "__main__":
    main()