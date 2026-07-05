#!/usr/bin/env python3
"""
Extract all \cite{...} commands from a .tex file and convert matching BibTeX entries to \bibitem format.
"""

import re
from pathlib import Path

def extract_citations(tex_file):
    """Extract all unique citation keys from a LaTeX file."""
    print(f"Reading: {tex_file}")
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    
    # Match \cite{key1,key2,...} and \cite[optional]{key1,key2,...}
    pattern = r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}'
    matches = re.findall(pattern, content)
    
    print(f"Found {len(matches)} \\cite commands")
    
    # Split by comma and clean whitespace
    keys = set()
    for match in matches:
        for key in match.split(','):
            key = key.strip()
            if key:
                keys.add(key)
    
    return sorted(keys)

def parse_bibtex_file(bib_file):
    """Parse a BibTeX file and return a dictionary of entries."""
    print(f"Reading: {bib_file}")
    with open(bib_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    
    entries = {}
    # Match @type{key, fields }
    # More robust pattern that handles nested braces
    pattern = r'@(\w+)\s*\{\s*([^,\s]+)\s*,((?:[^@](?!@\w+\{))*)\}'
    
    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        entry_type = match.group(1)
        key = match.group(2).strip()
        fields_text = match.group(3)
        
        # Parse fields - handle both {...} and "..." values
        fields = {}
        field_pattern = r'(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|"[^"]*")'
        for field_match in re.finditer(field_pattern, fields_text):
            field_name = field_match.group(1)
            field_value = field_match.group(2)
            # Remove outer braces or quotes
            if field_value.startswith('{') and field_value.endswith('}'):
                field_value = field_value[1:-1]
            elif field_value.startswith('"') and field_value.endswith('"'):
                field_value = field_value[1:-1]
            fields[field_name.lower()] = field_value.strip()
        
        entries[key] = {
            'type': entry_type.lower(),
            'fields': fields
        }
    
    return entries

def format_authors(author_text):
    """Format author names."""
    if not author_text:
        return ''
    
    # Split by 'and'
    authors = [a.strip() for a in re.split(r'\s+and\s+', author_text)]
    
    if len(authors) == 1:
        return authors[0]
    elif len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    elif len(authors) > 2:
        return f"{authors[0]} et al."
    
    return author_text

def bibtex_to_bibitem(key, entry):
    """Convert a BibTeX entry to \bibitem format."""
    entry_type = entry['type']
    fields = entry['fields']
    
    # Start with the bibitem
    lines = [f"\\bibitem{{{key}}}"]
    
    # Get common fields
    author = format_authors(fields.get('author', ''))
    title = fields.get('title', '')
    year = fields.get('year', '')
    
    # Format based on entry type
    if entry_type == 'article':
        journal = fields.get('journal', '')
        volume = fields.get('volume', '')
        pages = fields.get('pages', '')
        doi = fields.get('doi', '')
        
        if author:
            lines.append(f"{author},")
        lines.append(f"``{title},''")
        if journal:
            lines.append(f"\\textit{{{journal}}}")
        if volume:
            lines.append(f"\\textbf{{{volume}}}")
        if pages:
            lines.append(f"({year}), {pages}.")
        elif year:
            lines.append(f"({year}).")
        if doi:
            lines.append(f"doi: {doi}")
    
    elif entry_type == 'book':
        publisher = fields.get('publisher', '')
        edition = fields.get('edition', '')
        
        if author:
            lines.append(f"{author},")
        lines.append(f"\\textit{{{title}}}")
        if edition:
            lines.append(f"({edition} ed.,")
        if publisher:
            if edition:
                lines.append(f"{publisher}, {year}).")
            else:
                lines.append(f"({publisher}, {year}).")
        elif year:
            lines.append(f"({year}).")
    
    elif entry_type in ['inproceedings', 'incollection']:
        booktitle = fields.get('booktitle', '')
        editor = fields.get('editor', '')
        publisher = fields.get('publisher', '')
        pages = fields.get('pages', '')
        
        if author:
            lines.append(f"{author},")
        lines.append(f"``{title},''")
        lines.append(f"in \\textit{{{booktitle}}}")
        if editor:
            lines.append(f", ed. {editor}")
        if pages:
            lines.append(f", pp. {pages}")
        if publisher and year:
            lines.append(f"({publisher}, {year}).")
        elif year:
            lines.append(f"({year}).")
    
    elif entry_type == 'misc':
        howpublished = fields.get('howpublished', '')
        note = fields.get('note', '')
        doi = fields.get('doi', '')
        url = fields.get('url', '')
        publisher = fields.get('publisher', '')
        
        if author:
            lines.append(f"{author},")
        lines.append(f"``{title}''")
        if publisher:
            lines.append(f"({publisher}, {year}).")
        elif year:
            lines.append(f"({year}).")
        if howpublished:
            lines.append(howpublished)
        if note:
            lines.append(note)
        if doi:
            lines.append(f"doi: {doi}")
        elif url:
            lines.append(url)
    
    else:
        # Generic format
        if author:
            lines.append(f"{author},")
        if title:
            lines.append(f"\\textit{{{title}}}")
        if year:
            lines.append(f"({year}).")
    
    return '\n'.join(lines) + '\n'

def main():
    try:
        # File paths
        tex_file = Path(r"C:\workspace\solo_projects\Swirl-String-Theory\SST-01-Canon\Swirl-String-Theory_Canon-v0.5.12.tex")
        bib_file = Path(r"C:\workspace\solo_projects\Swirl-String-Theory\SST-01-Canon\canon_swirl_string_theory.bib")
        output_file = Path(r"C:\workspace\solo_projects\Swirl-String-Theory\SST-01-Canon\converted_bibitems.tex")
        
        print("="*60)
        print("BibTeX to \\bibitem Converter")
        print("="*60)
        
        # Extract citations
        print("\n1. Extracting citations from LaTeX file...")
        cited_keys = extract_citations(tex_file)
        print(f"   Found {len(cited_keys)} unique citations\n")
        
        # Parse BibTeX file
        print("2. Parsing BibTeX file...")
        bib_entries = parse_bibtex_file(bib_file)
        print(f"   Parsed {len(bib_entries)} BibTeX entries\n")
        
        # Convert to bibitems
        print("3. Converting to \\bibitem format...")
        bibitems = []
        found_keys = []
        missing_keys = []
        
        for key in cited_keys:
            if key in bib_entries:
                bibitem = bibtex_to_bibitem(key, bib_entries[key])
                bibitems.append(bibitem)
                found_keys.append(key)
                print(f"   ✓ {key}")
            else:
                missing_keys.append(key)
                print(f"   ✗ {key} (NOT FOUND)")
        
        # Write output
        print(f"\n4. Writing output to {output_file.name}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("% Converted bibliography items\n")
            f.write("% Generated from canon_swirl_string_theory.bib\n")
            f.write(f"% Date: {Path(__file__).stat().st_mtime}\n\n")
            f.write("\\begin{thebibliography}{99}\n\n")
            for item in bibitems:
                f.write(item + '\n')
            f.write("\\end{thebibliography}\n")
        
        print(f"   ✓ Written {len(bibitems)} bibliography items\n")
        
        # Write summary
        summary_file = output_file.parent / "citation_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("CITATION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total citations found:     {len(cited_keys)}\n")
            f.write(f"Found in .bib file:        {len(found_keys)}\n")
            f.write(f"Missing from .bib file:    {len(missing_keys)}\n\n")
            
            if found_keys:
                f.write("SUCCESSFULLY CONVERTED:\n")
                f.write("-" * 60 + "\n")
                for key in found_keys:
                    f.write(f"  ✓ {key}\n")
                f.write("\n")
            
            if missing_keys:
                f.write("MISSING FROM BIB FILE:\n")
                f.write("-" * 60 + "\n")
                for key in missing_keys:
                    f.write(f"  ✗ {key}\n")
                f.write("\n")
        
        print(f"5. Summary written to {summary_file.name}")
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total citations:       {len(cited_keys)}")
        print(f"Successfully converted: {len(found_keys)}")
        print(f"Missing references:     {len(missing_keys)}")
        print("=" * 60)
        
        if missing_keys:
            print("\n⚠ WARNING: Some citations are missing from the .bib file")
            print("   See citation_summary.txt for details")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())