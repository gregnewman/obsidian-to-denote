"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary Obsidian vault with sample content"""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    
    # Create .obsidian folder to identify as vault
    (vault / ".obsidian").mkdir()
    
    # Create sample structure
    (vault / "attachments").mkdir()
    (vault / "projects").mkdir()
    (vault / "daily").mkdir()
    (vault / "archive").mkdir()
    
    # Create sample notes with various features
    
    # Note with full metadata
    (vault / "welcome.md").write_text("""---
title: Welcome to My Vault
aliases: [Start Here, Index]
tags: [meta, important]
created: 2024-01-01T10:00:00
modified: 2024-01-15T15:30:00
author: Test User
---

# Welcome to My Vault

This is the main entry point. See [[projects/project-alpha]] for current work.

## Features

- **Bold text** and *italic text*
- ~~Strikethrough~~
- `inline code`
- [[Internal Links]]
- [External Links](https://example.com)

### Code Example

```python
def greet(name):
    return f"Hello, {name}!"
```

### Tasks

- [ ] Set up vault
- [x] Create welcome note
- [ ] Add more content
""")
    
    # Project note with image
    (vault / "projects" / "project-alpha.md").write_text("""---
title: Project Alpha
tags: [project, active]
---

# Project Alpha

This project includes a diagram:

![[architecture.png]]

See also [[projects/project-beta|Project Beta]] for related work.

## Resources

- [[meeting-notes-2024-01-15]]
- ![[project-spec.pdf]]
""")
    
    # Daily note without frontmatter
    (vault / "daily" / "2024-01-15.md").write_text("""# Daily Note - January 15, 2024

## Morning
- Reviewed [[projects/project-alpha]]
- Meeting with team #meeting

## Afternoon
- Updated documentation
- Fixed bugs #bugfix #development

## Tasks
- [x] Review PRs
- [x] Update project status
- [ ] Prepare tomorrow's presentation
""")
    
    # Archive note with minimal content
    (vault / "archive" / "old-ideas.md").write_text("""Random ideas from last year

- Idea 1
- Idea 2
- Link to [[nonexistent-note]]
""")
    
    # Note with special characters
    (vault / "special-éñçödīng.md").write_text("""---
title: Unicode Test Note
tags: [test, special-chars]
---

# Testing Special Characters

This note has spëcial chàracters in the filename and content.

Über café naïve résumé 日本語 中文 العربية
""")
    
    # Create fake attachments
    (vault / "attachments" / "architecture.png").write_bytes(b"PNG\x89fake image data")
    (vault / "attachments" / "project-spec.pdf").write_bytes(b"%PDF-1.4 fake pdf")
    (vault / "daily" / "meeting-notes-2024-01-15.md").write_text("# Meeting Notes\n\nDiscussed project timeline.")
    
    return vault


@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory"""
    output = tmp_path / "denote_output"
    output.mkdir()
    return output


@pytest.fixture
def converter_settings():
    """Common converter settings for testing"""
    return {
        'org': {
            'output_format': 'org',
            'preserve_links': False,
            'assets_handling': 'copy'
        },
        'md': {
            'output_format': 'md',
            'preserve_links': True,
            'assets_handling': 'copy'
        },
        'minimal': {
            'output_format': 'org',
            'preserve_links': False,
            'assets_handling': 'ignore'
        }
    }
