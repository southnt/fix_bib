# BibTeX Bibliography DOI Fixer

A Python utility to enhance BibTeX bibliography files exported from Google Scholar by adding missing DOI fields, removing redundant information, and standardizing entry formats.

## The Problem

Google Scholar's BibTeX exports often have several issues:

1. **Missing DOIs**: Entries frequently lack Digital Object Identifier (DOI) fields, which are crucial for reliable citation linking
2. **Redundant Fields**: Exports contain unnecessary fields like `organization`, `abstract`, and `keywords` that clutter your bibliography
3. **Inconsistent Titles**: Titles may not match the canonical versions in scholarly databases

## Features

This script resolves these issues by:

- ✅ **Adding Missing DOIs**: Automatically finds and adds the correct DOI for each entry
- ✅ **Intelligent Matching**: Uses both title and author information to find the most accurate DOI match
- ✅ **Customizable Field Removal**: Lets you specify which redundant fields to eliminate
- ✅ **Title Standardization**: Updates entry titles to match the canonical versions from Crossref
- ✅ **Title Case Preservation**: Ensures proper capitalization in LaTeX output
- ✅ **DOI Conflict Resolution**: Warns about and intelligently resolves DOI conflicts

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
python fix_bibliography.py input.bib output.bib --remove organization abstract keywords url
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
   - Retrieves the DOI and standardized title from Crossref
   - Removes specified redundant fields
3. **Output**: The processed entries are written to a new BibTeX file

## Example

Input entry:
```bibtex
@article{smith2019machine,
  title={machine learning applications},
  author={Smith, John and Johnson, Robert},
  journal={Journal of Machine Learning},
  volume={42},
  number={3},
  pages={123--145},
  year={2019},
  abstract={This paper discusses various applications...},
  keywords={machine learning, applications, algorithms},
  organization={University of Example}
}
```

Output entry:
```bibtex
@article{smith2019machine,
  title={Machine Learning Applications: A Comprehensive Survey},
  author={Smith, John and Johnson, Robert},
  journal={Journal of Machine Learning},
  volume={42},
  number={3},
  pages={123--145},
  year={2019},
  doi={10.1234/jml.2019.42.3.123}
}
```

## Limitations

- The script relies on the Crossref API, which may have rate limits
- Matching accuracy depends on the quality of the original entries
- Some entries may not have DOIs registered in Crossref

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Thanks
I appreciate the help from GitHub Copilot and Claude 3.7 Sonnet Thinking with Viber coding.