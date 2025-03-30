# BibTeX Bibliography DOI Fixer

A Python utility to enhance BibTeX bibliography files exported from Google Scholar, etc., by adding missing DOI fields, updating metadata fields from Crossref, removing redundant information, and standardizing entry formats.

## The Problem

Google Scholar's BibTeX exports often have several issues:

1. **Missing DOIs**: Entries frequently lack Digital Object Identifier (DOI) fields, which are crucial for reliable citation linking
2. **Incomplete or Incorrect Metadata**: Fields like pages, volume, journal names may be incorrect or formatted improperly
3. **Redundant Fields**: Exports contain unnecessary fields like `organization`, `abstract`, and `keywords` that clutter your bibliography
4. **Inconsistent Titles**: Titles may not match the canonical versions in scholarly databases

## Features

This script resolves these issues by:

- ✅ **Adding Missing DOIs**: Automatically finds and adds the correct DOI for each entry
- ✅ **Intelligent Metadata Enhancement**: Updates pages, booktitle, volume, number, year, journal and other fields from Crossref
- ✅ **Field Standardization**: Ensures proper BibTeX formatting (e.g., pages with double-hyphens: 127--145)
- ✅ **Intelligent Matching**: Uses both title and author information to find the most accurate matches
- ✅ **Customizable Field Removal**: Lets you specify which redundant fields to eliminate
- ✅ **Title Standardization**: Updates entry titles to match the canonical versions from Crossref
- ✅ **Title Case Preservation**: Ensures proper capitalization in LaTeX output
- ✅ **DOI Conflict Resolution**: Warns about and intelligently resolves DOI conflicts
- ✅ **Issue Identification**: Saves problematic entries to a separate file for easy review

## Run on colab (Recommended)
https://colab.research.google.com/drive/1UaIh96xLRa1Oe1pIdOAVAHslTyHgcRIJ?usp=sharing

## Requirements

- Python 3.6 or higher
- `bibtexparser` library
- `requests` library

## Installation

1. Clone this repository or download the script:
```bash
git clone https://github.com/yourusername/bibtex-doi-fixer.git
cd bibtex-doi-fixer
```

2. Install the required dependencies:
```bash
pip install bibtexparser requests
```

## Usage

Basic usage:
```bash
python fix_bibliography.py input.bib output.bib
```

Specify which fields to remove:
```bash
python fix_bibliography.py input.bib output.bib --remove organization abstract keywords url publisher
```

Adjust the similarity threshold for DOI matching:
```bash
python fix_bibliography.py input.bib output.bib --threshold 0.8
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `input_file` | Path to the input BibTeX file |
| `output_file` | Path to the output BibTeX file |
| `--remove [fields]` | Space-separated list of fields to remove (default: organization abstract keywords) |
| `--threshold THRESHOLD` | Similarity threshold for accepting matches (0.0-1.0, default: 0.75) |

## How It Works

1. **Loading**: The script reads the input BibTeX file using the bibtexparser library
2. **Processing**: For each entry:
   - Extracts title, authors, and year information
   - Queries the Crossref API with this information
   - Uses a similarity algorithm to find the best matching publication
   - Retrieves the DOI and standardized metadata from Crossref
   - Updates fields with canonical information from Crossref
   - Removes specified redundant fields
3. **Output**: 
   - The processed entries are written to a new BibTeX file
   - Entries with potential issues (no changes) are saved to `potential_issues.bib`

## Output Files

The script produces two output files:
1. **Main Output File**: Contains all entries with updated DOIs and metadata
2. **Potential Issues File**: `potential_issues.bib` contains entries that couldn't be matched or had no changes applied

## Example

Input entry:
```bibtex
@article{smith2019machine,
  title={machine learning applications},
  author={Smith, John and Johnson, Robert},
  journal={Journal of Machine Learning},
  volume={42},
  pages={123-145},
  year={2019},
  abstract={This paper discusses various applications...},
  keywords={machine learning, applications, algorithms},
  organization={University of Example}
}
```

Output entry:
```bibtex
@article{smith2019machine,
  title={{Machine Learning Applications: A Comprehensive Survey}},
  author={Smith, John and Johnson, Robert},
  journal={Journal of Machine Learning},
  volume={42},
  number={3},
  pages={123--145},
  year={2019},
  doi={10.1234/jml.2019.42.3.123},
  publisher={Elsevier}
}
```

## Warning System

The script includes a comprehensive warning system to identify entries that may need manual attention:

- ⚠️ **No Matches Found**: When no potential matches are found on Crossref
- ⚠️ **Below Threshold Warning**: When the best match score is below the similarity threshold
- ⚠️ **No Changes Warning**: When an entry was processed but no fields were updated

All entries with warnings are collected into a separate `potential_issues.bib` file for easy review.

## Limitations

- The script relies on the Crossref API, which may have rate limits
- Matching accuracy depends on the quality of the original entries
- Some entries may not have DOIs registered in Crossref
- Mathematical notation in titles might need additional LaTeX formatting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Thanks
I appreciate the help from GitHub Copilot and Claude 3.7 Sonnet Thinking with Viber coding.
