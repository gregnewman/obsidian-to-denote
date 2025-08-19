# Obsidian to Denote Converter

This is a personal Python project I'm building to convert Obsidian markdown files to [Denote](https://protesilaos.com/emacs/denote) format, supporting both org-mode and markdown output with full preservation of links, assets, and metadata.

## Disclaimer

This converter was created to migrate my personal Obsidian vault(s) to Denote. It has been tested primarily with my own vault structure and may not cover all possible Obsidian configurations or edge cases.

**⚠️ Please test this converter on a COPY of your vault first!** While it works well for my use case, your vault may have different features, plugins, or organizational patterns that haven't been tested.

## Features That Need Testing/Verification

The following features have been implemented but should be verified against your specific vault:

### Core Functionality
- [ ] **YAML Frontmatter Parsing** - Complex metadata structures, nested values, special characters
- [ ] **Tag Extraction** - Inline tags, frontmatter tags, tags with special characters
- [ ] **Title Detection** - Fallback from metadata → first heading → filename
- [ ] **Timestamp Generation** - Uses file modification time or frontmatter created date

### Link Handling
- [ ] **WikiLinks** - Basic `[[note]]` and aliased `[[note|display text]]` links
- [ ] **Embedded Images** - `![[image.png]]` syntax
- [ ] **Embedded Files** - PDFs, documents, and other attachments
- [ ] **Standard Markdown Links** - Regular `[text](url)` links
- [ ] **Relative Path Links** - Links with folder paths like `[[folder/note]]`

### Asset Management
- [ ] **Image Files** - PNG, JPG, GIF, SVG formats
- [ ] **Document Attachments** - PDF, DOCX, XLSX, PPTX files
- [ ] **Asset Discovery** - Searches common folders (attachments/, assets/, images/)
- [ ] **Asset Path Resolution** - Handles various Obsidian attachment folder configurations

### Content Conversion (Org-mode)
- [ ] **Headers** - All levels (# through ######)
- [ ] **Emphasis** - Bold, italic, strikethrough, inline code
- [ ] **Lists** - Ordered, unordered, nested lists
- [ ] **Checkboxes** - Task lists with [ ] and [x]
- [ ] **Code Blocks** - With language specifications
- [ ] **Tables** - Basic markdown tables (limited support)
- [ ] **Block Quotes** - May need additional testing

### Directory Handling
- [ ] **Nested Folders** - Deep directory structures
- [ ] **Folder Name Tags** - Adding folder names as tags when flattening
- [ ] **Structure Preservation** - Maintaining original folder hierarchy
- [ ] **Special Characters in Paths** - Unicode, spaces, special characters

### Known Limitations
- **Obsidian Plugins** - Plugin-specific syntax (Dataview, Templater, etc.) is not processed
- **Canvas Files** - `.canvas` files are ignored (I do not have these in my vaults)
- **Graph View** - Graph relationships are not explicitly preserved
- **Aliases** - Only first alias is used for title generation
- **Block References** - `^block-id` references are not updated
- **Embedded Searches** - Query blocks are not processed
- **Excalidraw** - Drawing files are not handled

### Vault-Specific Considerations
Your vault may have:
- Custom attachment folder locations
- Non-standard organizational patterns
- Plugin-generated content or metadata
- Large files or many assets
- Symbolic links or junction points
- Case-sensitive filename requirements

**Please report any issues or edge cases you encounter!**

## Features

- 🔄 **Format Conversion**: Convert to org-mode or keep as markdown with Denote naming
- 📁 **Flexible Directory Handling**: 
  - Flatten to single directory (Denote standard)
  - Preserve original directory structure
  - Add folder names as tags when flattening
- 🖼️ **Asset Management**: 
  - Copy images, PDFs, and attachments to output directory
  - Preserve original asset locations
  - Automatic asset discovery across vault
- 🔗 **Smart Link Conversion**: 
  - Convert Obsidian WikiLinks to org-mode or markdown links
  - Update links to match new Denote filenames
  - Handle both internal note links and external assets
- 🏷️ **Tag Processing**: 
  - Extract tags from YAML frontmatter and inline hashtags
  - Include folder names as tags (optional)
  - Incorporate tags into Denote filename
- 📝 **Metadata Preservation**: 
  - Process YAML frontmatter
  - Convert metadata to org-mode properties
  - Generate Denote-compliant timestamps

## Installation

### Using uv (Recommended)

First, install `uv` if you haven't already:

```bash
# On macOS/Linux using curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv
```

Then clone and install the converter:

```bash
# Clone the repository
git clone https://github.com/gregnewman/obsidian-to-denote.git
cd obsidian-to-denote

# Create virtual environment and install
uv venv
uv pip install -e .

# Or run directly without installing
uv run obsidian-to-denote --help
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/obsidian-to-denote.git
cd obsidian-to-denote

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with pip
pip install -e .
```

### Direct Usage

You can also run the converter directly without installation:

```bash
uv run python obsidian_to_denote/converter.py [options]
```

## Usage

**Note:** All commands below assume you're using `uv`. If you've activated the virtual environment with `source .venv/bin/activate`, you can omit the `uv run` prefix.

### Basic Conversion

Convert an entire Obsidian vault to org-mode format:

```bash
uv run obsidian-to-denote /path/to/obsidian/vault /path/to/denote/notes
```

Or use the short alias:

```bash
uv run o2d /path/to/obsidian/vault /path/to/denote/notes
```

### Convert Single File

```bash
uv run o2d my-note.md output-dir/
```

### Output Format Options

Keep markdown format with Denote naming:

```bash
uv run o2d vault/ output/ --format md
```

Convert to org-mode (default):

```bash
uv run o2d vault/ output/ --format org
```

### Directory Structure Options

**Default: Flatten to single directory (Denote standard)**

```bash
uv run o2d vault/ output/
```

**Preserve original directory structure:**

```bash
uv run o2d vault/ output/ --preserve-structure
```

**Flatten but add folder names as tags:**

```bash
uv run o2d vault/ output/ --add-folder-tags
```

### Asset Handling Options

**Copy assets to output directory (default):**

```bash
uv run o2d vault/ output/ --assets copy
```

**Keep original asset paths:**

```bash
uv run o2d vault/ output/ --assets link
```

**Ignore assets:**

```bash
uv run o2d vault/ output/ --assets ignore
```

**Specify custom assets directory:**

```bash
uv run o2d vault/ output/ --assets copy --assets-dir attachments
```

### Link Handling

**Preserve WikiLinks in markdown output:**

```bash
uv run o2d vault/ output/ --format md --preserve-links
```

## Command Line Options

```
usage: obsidian-to-denote [-h] [-f {org,md}] [--preserve-links]
                          [--preserve-structure] [--add-folder-tags]
                          [--assets {copy,link,ignore}]
                          [--assets-dir ASSETS_DIR]
                          input output

Convert Obsidian markdown files to Denote format

positional arguments:
  input                 Input file or directory containing Obsidian markdown files
  output                Output directory for Denote files

options:
  -h, --help            show this help message and exit
  -f {org,md}, --format {org,md}
                        Output format: org for org-mode, md for markdown (default: org)
  --preserve-links      Preserve wiki-style links in markdown output
  --preserve-structure  Preserve directory structure (default: flatten to single directory)
  --add-folder-tags     Add folder names as tags when flattening
  --assets {copy,link,ignore}
                        How to handle assets: copy (default), link, or ignore
  --assets-dir ASSETS_DIR
                        Directory name for copied assets (default: assets)
```

## Denote Filename Format

The converter generates Denote-compliant filenames with the following structure:

```
YYYYMMDDTHHMMSS--title-slug__tag1_tag2.extension
```

Example conversions:
- `Projects/ProjectA.md` → `20240115T093000--project-a__projects.org`
- `Daily/2024-01-15.md` → `20240115T080000--daily-note__daily.org`

## Examples

### Example 1: Full Vault Conversion with Assets

Convert an Obsidian vault to org-mode, copying all assets:

```bash
uv run o2d ~/Documents/ObsidianVault ~/Documents/DenoteNotes --format org --assets copy
```

### Example 2: Markdown to Markdown with Structure

Keep markdown format and directory structure:

```bash
uv run o2d ~/ObsidianVault ~/DenoteNotes --format md --preserve-structure --preserve-links
```

### Example 3: Flatten with Context

Flatten structure but preserve context through tags:

```bash
uv run o2d ~/ObsidianVault ~/DenoteNotes --add-folder-tags --assets copy
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/gregnewman/obsidian-to-denote.git
cd obsidian-to-denote

# Create virtual environment with uv
uv venv

# Install with development dependencies
uv pip install -e .
uv pip install pytest pytest-cov black ruff

# Or if dev dependencies are in pyproject.toml (optional)
# uv pip install -e ".[dev]"
```

### Run Tests

```bash
# Run tests with uv
uv run pytest

# Run with coverage
uv run pytest --cov=obsidian_to_denote

# Run linting
uv run ruff check .
uv run black --check .
```

### Format Code

```bash
# Format with black
uv run black .

# Fix linting issues
uv run ruff check --fix .
```

## Project Structure

```
obsidian-to-denote/
├── obsidian_to_denote/
│   ├── __init__.py
│   └── converter.py        # Main converter module
├── tests/
│   ├── __init__.py
│   ├── test_converter.py   # Unit tests
│   └── fixtures/           # Test fixtures
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── LICENSE                 # MIT License
└── .gitignore
```

## How It Works

1. **Discovery**: Scans the Obsidian vault for markdown files
2. **Metadata Extraction**: Parses YAML frontmatter and extracts metadata
3. **Asset Processing**: Finds and processes referenced images and attachments
4. **Filename Generation**: Creates Denote-compliant filenames with timestamps and tags
5. **Content Conversion**: Converts markdown to org-mode (if specified)
6. **Link Updates**: Updates internal links to match new filenames
7. **Output**: Writes converted files to the specified directory

## Compatibility

- **Python**: 3.8+
- **Obsidian**: All versions (tested with vaults from v0.15+)
- **Denote**: Compatible with Denote 2.0+ naming conventions

## Limitations

- Does not process Obsidian plugins' custom syntax (Dataview queries, etc.)
- Canvas files (.canvas) are not converted
- Some complex Obsidian-specific markdown extensions may not convert perfectly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request (please ensure tests are updated an passing first)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Denote](https://protesilaos.com/emacs/denote) by Protesilaos Stavrou
- [Obsidian](https://obsidian.md/) for being an excellent note-taking tool
- The Emacs and Obsidian communities

## Troubleshooting

### Assets Not Found

If assets aren't being copied, check:
1. Asset file paths in your notes match actual file locations
2. Assets are in common folders (attachments/, assets/, images/)
3. Use debug output to see where the converter is searching

### Encoding Issues

For non-ASCII characters in filenames or content:
- The converter handles Unicode properly
- Filenames are transliterated to ASCII for Denote compatibility
- Content encoding is preserved

### Large Vaults

For vaults with thousands of notes:
- The converter processes files sequentially
- Progress is displayed for each file
- Consider converting in batches if needed
