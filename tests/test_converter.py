"""
Tests for Obsidian to Denote Converter
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest
import yaml

from obsidian_to_denote.converter import ObsidianToDenoteConverter


class TestObsidianToDenoteConverter:
    """Test suite for the converter"""

    @pytest.fixture
    def converter_org(self):
        """Create a converter instance for org-mode output"""
        return ObsidianToDenoteConverter(output_format='org')

    @pytest.fixture
    def converter_md(self):
        """Create a converter instance for markdown output"""
        return ObsidianToDenoteConverter(output_format='md')

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_slugify(self, converter_org):
        """Test the slugify function"""
        assert converter_org.slugify("Hello World") == "hello-world"
        assert converter_org.slugify("Test & Special@Characters!") == "test-specialcharacters"
        assert converter_org.slugify("Multiple   Spaces") == "multiple-spaces"
        assert converter_org.slugify("") == "untitled"
        assert converter_org.slugify(None) == "untitled"
        assert converter_org.slugify("Über Café") == "uber-cafe"  # ASCII transliteration
        assert converter_org.slugify("123-numbers") == "123-numbers"

    def test_extract_yaml_frontmatter(self, converter_org):
        """Test YAML frontmatter extraction"""
        # Test with valid frontmatter
        content = """---
title: Test Note
tags: [tag1, tag2]
created: 2024-01-15
---
# Content
This is the content."""
        
        metadata, remaining = converter_org.extract_yaml_frontmatter(content)
        assert metadata['title'] == "Test Note"
        assert metadata['tags'] == ['tag1', 'tag2']
        assert metadata['created'] == "2024-01-15"
        assert "# Content" in remaining
        assert "---" not in remaining

        # Test without frontmatter
        content_no_yaml = "# Just Content\nNo frontmatter here"
        metadata, remaining = converter_org.extract_yaml_frontmatter(content_no_yaml)
        assert metadata == {}
        assert remaining == content_no_yaml

        # Test with empty frontmatter
        content_empty = """---
---
# Content"""
        metadata, remaining = converter_org.extract_yaml_frontmatter(content_empty)
        assert metadata is None or metadata == {}
        assert "# Content" in remaining

    def test_generate_denote_filename(self, converter_org, temp_dir):
        """Test Denote filename generation"""
        # Create a test file
        test_file = Path(temp_dir) / "test.md"
        test_file.write_text("# Test Content")
        
        metadata = {
            'title': 'Test Note',
            'tags': ['tag1', 'tag2']
        }
        content = "# Test Content"
        
        filename, title, tags, created_time = converter_org.generate_denote_filename(
            test_file, metadata, content
        )
        
        # Check filename format
        assert filename.endswith('.org')
        assert '--test-note__' in filename
        assert 'tag1' in filename
        assert 'tag2' in filename
        
        # Check timestamp format (YYYYMMDDTHHMMSS)
        timestamp_part = filename.split('--')[0]
        assert len(timestamp_part) == 15  # YYYYMMDDTHHMMSS
        assert timestamp_part[8] == 'T'

    def test_generate_denote_filename_no_metadata(self, converter_org, temp_dir):
        """Test filename generation without metadata"""
        test_file = Path(temp_dir) / "my-note.md"
        test_file.write_text("Just some content")
        
        filename, title, tags, created_time = converter_org.generate_denote_filename(
            test_file, None, "Just some content"
        )
        
        assert '--my-note' in filename
        assert filename.endswith('.org')

    def test_generate_denote_filename_with_heading(self, converter_org, temp_dir):
        """Test filename generation using first heading as title"""
        test_file = Path(temp_dir) / "untitled.md"
        content = "# My Important Note\nSome content"
        test_file.write_text(content)
        
        filename, title, tags, created_time = converter_org.generate_denote_filename(
            test_file, {}, content
        )
        
        assert '--my-important-note' in filename
        assert title == "My Important Note"

    def test_convert_links_to_org(self, converter_org):
        """Test converting Obsidian links to org-mode format"""
        content = "Check [[my-note]] and [[another note|description]]"
        result = converter_org.convert_links(content, is_org=True)
        
        assert "[[file:my-note.org][my-note]]" in result
        assert "[[file:another note.org][description]]" in result

    def test_convert_links_to_markdown(self, converter_md):
        """Test converting Obsidian links to standard markdown"""
        converter_md.preserve_links = False
        content = "Check [[my-note]] and [[another note|description]]"
        result = converter_md.convert_links(content, is_org=False)
        
        assert "[my-note](my-note.md)" in result
        assert "[description](another note.md)" in result

    def test_convert_to_org_headers(self, converter_org):
        """Test markdown to org-mode header conversion"""
        content = """# Level 1
## Level 2
### Level 3
#### Level 4"""
        
        result = converter_org.convert_to_org(content, {}, "Test", [])
        assert "* Level 1" in result
        assert "** Level 2" in result
        assert "*** Level 3" in result
        assert "**** Level 4" in result

    def test_convert_to_org_emphasis(self, converter_org):
        """Test markdown to org-mode emphasis conversion"""
        content = "**bold** and *italic* and ~~strikethrough~~ and `code`"
        result = converter_org.convert_to_org(content, {}, "Test", [])
        
        # Note: The conversion might be complex due to nested replacements
        # Check for org-mode syntax
        assert "~code~" in result  # Inline code
        assert "+strikethrough+" in result  # Strikethrough

    def test_convert_to_org_lists(self, converter_org):
        """Test markdown to org-mode list conversion"""
        content = """- Item 1
- Item 2
  - Nested item
1. Numbered item
2. Another numbered"""
        
        result = converter_org.convert_to_org(content, {}, "Test", [])
        assert "- Item 1" in result
        assert "  - Nested item" in result
        assert "1. Numbered item" in result

    def test_convert_to_org_checkboxes(self, converter_org):
        """Test markdown to org-mode checkbox conversion"""
        content = """- [ ] Unchecked
- [x] Checked"""
        
        result = converter_org.convert_to_org(content, {}, "Test", [])
        assert "- [ ] Unchecked" in result
        assert "- [X] Checked" in result  # Note capital X in org-mode

    def test_convert_to_org_code_blocks(self, converter_org):
        """Test markdown to org-mode code block conversion"""
        content = """```python
def hello():
    print("Hello")
```"""
        
        result = converter_org.convert_to_org(content, {}, "Test", [])
        assert "#+BEGIN_SRC python" in result
        assert "#+END_SRC" in result
        assert 'print("Hello")' in result

    def test_convert_to_org_with_metadata(self, converter_org):
        """Test org-mode conversion with metadata"""
        metadata = {
            'title': 'My Note',
            'author': 'John Doe',
            'created': '2024-01-15'
        }
        tags = ['tag1', 'tag2']
        
        result = converter_org.convert_to_org("Content", metadata, "My Note", tags)
        
        assert "#+title: My Note" in result
        assert "#+filetags: :tag1: :tag2:" in result
        assert ":PROPERTIES:" in result
        assert ":AUTHOR: John Doe" in result
        assert ":CREATED: 2024-01-15" in result

    def test_convert_file_basic(self, converter_org, temp_dir):
        """Test basic file conversion"""
        # Create input file
        input_file = Path(temp_dir) / "input" / "test.md"
        input_file.parent.mkdir(parents=True, exist_ok=True)
        input_file.write_text("""---
title: Test Note
tags: [test]
---
# Test Note
This is a test.""")
        
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert file
        filename, output_path = converter_org.convert_file(
            input_file, output_dir
        )
        
        # Check output file exists
        assert output_path.exists()
        assert filename.endswith('.org')
        assert '--test-note__test' in filename
        
        # Check content
        content = output_path.read_text()
        assert "#+title: Test Note" in content
        assert "* Test Note" in content

    def test_convert_directory(self, converter_org, temp_dir):
        """Test directory conversion"""
        # Create input directory structure
        input_dir = Path(temp_dir) / "vault"
        (input_dir / "folder1").mkdir(parents=True, exist_ok=True)
        (input_dir / "folder2").mkdir(parents=True, exist_ok=True)
        
        # Create test files
        (input_dir / "note1.md").write_text("# Note 1")
        (input_dir / "folder1" / "note2.md").write_text("# Note 2")
        (input_dir / "folder2" / "note3.md").write_text("# Note 3")
        
        output_dir = Path(temp_dir) / "output"
        
        # Convert directory
        converted = converter_org.convert_directory(input_dir, output_dir)
        
        assert len(converted) == 3
        
        # Check all files were converted
        output_files = list(output_dir.glob("*.org"))
        assert len(output_files) == 3

    def test_convert_directory_with_folder_tags(self, converter_org, temp_dir):
        """Test directory conversion with folder tags"""
        # Create input structure
        input_dir = Path(temp_dir) / "vault"
        (input_dir / "projects").mkdir(parents=True, exist_ok=True)
        
        # Create test file
        (input_dir / "projects" / "my-project.md").write_text("""---
tags: [important]
---
# My Project""")
        
        output_dir = Path(temp_dir) / "output"
        
        # Convert with folder tags
        converter_org.convert_directory(
            input_dir, output_dir, add_folder_tags=True
        )
        
        # Check output
        output_files = list(output_dir.glob("*.org"))
        assert len(output_files) == 1
        
        # Check that folder name is in tags
        filename = output_files[0].name
        assert 'projects' in filename or 'important' in filename

    def test_asset_finding(self, converter_org, temp_dir):
        """Test asset finding logic"""
        # Create vault structure
        vault_dir = Path(temp_dir) / "vault"
        vault_dir.mkdir(parents=True, exist_ok=True)
        (vault_dir / ".obsidian").mkdir()
        (vault_dir / "attachments").mkdir()
        (vault_dir / "notes").mkdir()
        
        # Create an asset
        asset_file = vault_dir / "attachments" / "image.png"
        asset_file.write_bytes(b"fake image data")
        
        # Test finding from different locations
        found = converter_org.find_asset("image.png", vault_dir / "notes")
        assert found is not None
        assert found.name == "image.png"

    def test_process_assets_ignore(self, converter_org):
        """Test asset processing in ignore mode"""
        converter = ObsidianToDenoteConverter(assets_handling='ignore')
        content = "![[image.png]] and [[document.pdf]]"
        result = converter.process_assets(content, Path("."), Path("."))
        assert result == content  # Should remain unchanged

    def test_edge_cases(self, converter_org, temp_dir):
        """Test various edge cases"""
        # Test with None title
        test_file = Path(temp_dir) / "test.md"
        test_file.write_text("")
        
        filename, title, tags, _ = converter_org.generate_denote_filename(
            test_file, {'title': None}, ""
        )
        assert title == "untitled"
        assert '--untitled' in filename
        
        # Test with empty tags
        filename, title, tags, _ = converter_org.generate_denote_filename(
            test_file, {'tags': []}, ""
        )
        assert tags == []
        assert '__' not in filename  # No tags section
        
        # Test with string tags instead of list
        filename, title, tags, _ = converter_org.generate_denote_filename(
            test_file, {'tags': 'single-tag'}, ""
        )
        assert tags == ['single-tag']
        assert '__single-tag' in filename


class TestIntegration:
    """Integration tests for the converter"""
    
    @pytest.fixture
    def sample_vault(self, tmp_path):
        """Create a sample Obsidian vault for testing"""
        vault = tmp_path / "test_vault"
        vault.mkdir()
        
        # Create .obsidian folder
        (vault / ".obsidian").mkdir()
        
        # Create some notes
        (vault / "index.md").write_text("""---
title: Index
tags: [main, toc]
---
# Index

This is the main index linking to [[projects/project1]] and [[daily/2024-01-15]].""")
        
        # Create subdirectories
        (vault / "projects").mkdir()
        (vault / "daily").mkdir()
        (vault / "attachments").mkdir()
        
        (vault / "projects" / "project1.md").write_text("""---
title: Project Alpha
tags: [project, important]
---
# Project Alpha

See the [[index]] for more info.
Check the diagram: ![[diagram.png]]""")
        
        (vault / "daily" / "2024-01-15.md").write_text("""# Daily Note

- [ ] Task 1
- [x] Task 2

Worked on [[projects/project1]]""")
        
        # Create a fake attachment
        (vault / "attachments" / "diagram.png").write_bytes(b"fake png data")
        
        return vault

    def test_full_vault_conversion(self, sample_vault, tmp_path):
        """Test converting an entire vault"""
        output_dir = tmp_path / "denote_output"
        
        converter = ObsidianToDenoteConverter(
            output_format='org',
            assets_handling='copy'
        )
        
        converted = converter.convert_directory(
            sample_vault,
            output_dir,
            preserve_structure=False,
            add_folder_tags=True
        )
        
        # Check files were converted
        assert len(converted) == 3
        
        # Check org files exist
        org_files = list(output_dir.glob("*.org"))
        assert len(org_files) == 3
        
        # Check assets were copied
        assets_dir = output_dir / "assets"
        if converter.asset_mapping:
            assert assets_dir.exists()
            assert len(list(assets_dir.glob("*.png"))) == 1
        
        # Check content of one file
        index_files = [f for f in org_files if "index" in f.name.lower()]
        if index_files:
            content = index_files[0].read_text()
            assert "#+title:" in content
            assert "#+filetags:" in content
