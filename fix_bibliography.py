#!/usr/bin/env python3
"""
Fix BibTeX bibliography by adding DOIs, updating metadata fields,
removing redundant fields, and standardizing titles based on Crossref data.
Enhanced field updates from Crossref API
"""

import argparse
import bibtexparser
import requests
import time
import re
import os
from difflib import SequenceMatcher
from bibtexparser.bwriter import BibTexWriter
from datetime import datetime

def similar(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def clean_text(text):
    """Clean text by removing unnecessary characters and normalizing whitespace."""
    if not text:
        return ""
    # Remove curly braces, normalize whitespace
    text = re.sub(r'[{}]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_doi_from_crossref(entry, similarity_threshold=0.75, max_results=10):
    """
    Query Crossref API to find DOI and standardized metadata.
    Returns a tuple of (doi, metadata_dict) where metadata_dict contains updated fields.
    """
    # Extract data from entry
    title = clean_text(entry.get('title', ''))
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
    headers = {'User-Agent': 'BibtexFixer/6.0 (mailto:example@example.com)'}
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Print number of results found
        total_results = data['message']['total-results']
        print(f"  Found {total_results} potential matches from Crossref")
        
        # Check if we got any results
        if total_results == 0:
            print(f"  ⚠️  WARNING: No matches found for this entry!")
            return None, None
        
        # Process results to find best match
        best_match = None
        best_similarity = 0
        best_metadata = {}
        
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
                
                # Extract metadata fields from Crossref
                metadata = {}
                # Title
                metadata['title'] = current_title
                
                # Journal/container title
                if 'container-title' in item and item['container-title']:
                    metadata['journal'] = item['container-title'][0]
                
                # Volume
                if 'volume' in item:
                    metadata['volume'] = item['volume']
                
                # Issue/Number
                if 'issue' in item:
                    metadata['number'] = item['issue']
                
                # Pages
                if 'page' in item:
                    metadata['pages'] = item['page'].replace('-', '--')  # BibTeX format
                
                # Year
                if 'published-print' in item and 'date-parts' in item['published-print']:
                    metadata['year'] = str(item['published-print']['date-parts'][0][0])
                elif 'published-online' in item and 'date-parts' in item['published-online']:
                    metadata['year'] = str(item['published-online']['date-parts'][0][0])
                elif 'created' in item and 'date-parts' in item['created']:
                    metadata['year'] = str(item['created']['date-parts'][0][0])
                
                # Publisher
                if 'publisher' in item:
                    metadata['publisher'] = item['publisher']
                
                # Book title (for conference papers)
                if 'event' in item and item['event'].get('name'):
                    metadata['booktitle'] = item['event']['name']
                
                # Type - map to BibTeX entry type
                if 'type' in item:
                    type_mapping = {
                        'journal-article': 'article',
                        'proceedings-article': 'inproceedings',
                        'book-chapter': 'incollection',
                        'book': 'book',
                        'edited-book': 'book',
                        'monograph': 'book',
                        'report': 'techreport',
                        'dissertation': 'phdthesis'
                    }
                    if item['type'] in type_mapping:
                        metadata['ENTRYTYPE'] = type_mapping[item['type']]
                
                # URL
                if 'URL' in item:
                    metadata['url'] = item['URL']
                
                best_metadata = metadata
                print(f"  Found potential match (score: {combined_score:.2f}): {current_title[:60]}...")
        
        # Only return if we're confident in the match
        if best_similarity >= similarity_threshold:
            return best_match, best_metadata
            
        print(f"  ⚠️  WARNING: Best match score ({best_similarity:.2f}) is below threshold ({similarity_threshold})!")
        print(f"  ⚠️  Match not accepted: \"{best_metadata.get('title', '')}\"")
        return None, None
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API request error: {e}")
        return None, None

def update_entry_with_metadata(entry, metadata):
    """
    Update entry with metadata from Crossref.
    Returns a tuple of (updated_entry, fields_updated).
    """
    fields_updated = []
    
    # Fields to update if they exist in metadata
    updateable_fields = ['title', 'journal', 'volume', 'number', 'pages', 
                         'year', 'publisher', 'booktitle', 'url']
    
    for field in updateable_fields:
        if field in metadata and metadata[field]:
            if field not in entry or clean_text(entry[field]) != clean_text(metadata[field]):
                old_value = entry.get(field, 'N/A')
                
                # Special case for title to preserve user's formatting choices
                if field == 'title':
                    entry[field] = f"{{{metadata[field]}}}"
                else:
                    entry[field] = metadata[field]
                
                fields_updated.append(field)
                print(f"  Updated {field}: '{old_value}' -> '{metadata[field]}'")
    
    # Handle entry type update if relevant
    if 'ENTRYTYPE' in metadata and metadata['ENTRYTYPE']:
        if entry['ENTRYTYPE'] != metadata['ENTRYTYPE']:
            old_type = entry['ENTRYTYPE']
            entry['ENTRYTYPE'] = metadata['ENTRYTYPE']
            fields_updated.append('ENTRYTYPE')
            print(f"  Updated entry type: {old_type} -> {metadata['ENTRYTYPE']}")
    
    return entry, fields_updated

def process_bibliography(input_file, output_file, remove_fields=None, similarity_threshold=0.75):
    """
    Main function to process bibliography:
    1. Add DOIs
    2. Update metadata fields from Crossref
    3. Remove specified fields
    4. Standardize titles
    """
    # Default fields to remove if not specified
    if remove_fields is None:
        remove_fields = []
    
    # Parse input file
    with open(input_file, 'r', encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    
    processed = 0
    total_entries = len(bib_database.entries)
    entries_updated = 0
    entries_warning = 0
    
    # Create a list to collect entries with potential issues
    potential_issue_entries = []
    
    # Process each entry
    for entry in bib_database.entries:
        processed += 1
        print(f"\nProcessing entry {processed}/{total_entries}: {entry.get('ID', 'Unknown ID')}")
        
        # Check if DOI already exists
        existing_doi = entry.get('doi')
        if existing_doi:
            print(f"  Existing DOI: {existing_doi}")
        
        # Get DOI and metadata from Crossref
        crossref_doi, metadata = get_doi_from_crossref(entry, similarity_threshold)
        
        # Update with metadata if found
        fields_updated = []
        if crossref_doi:
            if not existing_doi or existing_doi.lower() != crossref_doi.lower():
                entry['doi'] = crossref_doi
                fields_updated.append('doi')
                print(f"  Updated DOI: {crossref_doi}")
            
            # Update other fields with Crossref metadata
            if metadata:
                entry, updated_fields = update_entry_with_metadata(entry, metadata)
                fields_updated.extend(updated_fields)
        
        # Remove specified fields
        for field in remove_fields:
            if field in entry:
                del entry[field]
                print(f"  Removed field: {field}")
                fields_updated.append(f"removed:{field}")
        
        if fields_updated:
            entries_updated += 1
            print(f"  ✅ Updated {len(fields_updated)} fields: {', '.join(fields_updated)}")
        else:
            entries_warning += 1
            print(f"  ⚠️  WARNING: No changes were made to this entry!")
            print(f"  ⚠️  This may indicate an issue with matching or the entry already being complete.")
            
            # Add entry to potential issues list
            potential_issue_entries.append(entry.copy())
        
        # Rate limiting to be nice to the API
        if processed < total_entries:
            time.sleep(1)
    
    # Write to output file
    writer = BibTexWriter()
    writer.indent = '  '
    writer.comma_first = False
    
    with open(output_file, 'w', encoding='utf-8') as bibtex_file:
        bibtex_file.write(writer.write(bib_database))
    
    # Write potential issues to a separate file
    if potential_issue_entries:
        issues_db = bibtexparser.bibdatabase.BibDatabase()
        issues_db.entries = potential_issue_entries
        
        issues_file = 'potential_issues.bib'
        with open(issues_file, 'w', encoding='utf-8') as bibtex_file:
            bibtex_file.write(writer.write(issues_db))
    
    print(f"\nProcessing complete!")
    print(f"✅ Updated {entries_updated} of {total_entries} entries.")
    print(f"⚠️  {entries_warning} entries had no changes (potential issues).")
    print(f"Output saved to {output_file}")
    
    if entries_warning > 0:
        print(f"⚠️  {entries_warning} entries with potential issues saved to {issues_file}")
        print("\n⚠️  WARNING: Some entries had no changes applied!")
        print("    Consider reviewing these entries manually or adjusting the similarity threshold.")
        print("    Try running with --threshold 0.65 to be more lenient with matching.")

def main():
    """Parse arguments and run the script."""
    parser = argparse.ArgumentParser(description='Fix BibTeX bibliography by adding DOIs and updating metadata fields.')
    parser.add_argument('input_file', help='Input BibTeX file')
    parser.add_argument('output_file', help='Output BibTeX file')
    parser.add_argument('--remove', nargs='+', default=['organization', 'abstract', 'keywords'],
                        help='List of fields to remove (default: organization abstract keywords)')
    parser.add_argument('--threshold', type=float, default=0.75,
                        help='Similarity threshold for accepting matches (0.0-1.0, default: 0.75)')
    
    args = parser.parse_args()
    
    # Add timestamp and version info to output
    print(f"BibTeX Bibliography DOI Fixer - Version 6.0")
    print(f"Run by: southnt")
    print(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Input file: {args.input_file}")
    print(f"Output file: {args.output_file}")
    print(f"Similarity threshold: {args.threshold}")
    print(f"Fields to remove: {', '.join(args.remove)}")
    print("-" * 60)
    
    process_bibliography(
        args.input_file, 
        args.output_file, 
        args.remove, 
        args.threshold
    )

if __name__ == "__main__":
    main()