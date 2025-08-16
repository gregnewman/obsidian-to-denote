#!/usr/bin/env python3
"""Obsidian to Denote Converter
Converts Obsidian markdown files to Denote format (org-mode or markdown)
"""

import argparse
import hashlib
import os
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path

import yaml


class ObsidianToDenoteConverter:
    def __init__(self, output_format='org', preserve_links=True, assets_handling='copy'):
        """Initialize converter
        
        Args:
            output_format: 'org' for org-mode, 'md' for markdown
            preserve_links: Whether to preserve wiki-style links
            assets_handling: How to handle assets:
                - 'copy': Copy assets to output directory
                - 'link': Keep original paths (absolute or relative)
                - 'ignore': Don't process assets

        """
        self.output_format = output_format
        self.preserve_links = preserve_links
        self.assets_handling = assets_handling
        self.file_mapping = {}  # Track old -> new filename mappings
        self.asset_mapping = {}  # Track asset file mappings
        self.assets_dir = 'assets'  # Subdirectory for assets

    def slugify(self, text):
        """Convert text to valid Denote slug format"""
        # Handle None or empty text
        if not text:
            return 'untitled'

        # Convert to string if not already
        text = str(text)

        # Remove non-ASCII characters
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        # Replace spaces and special chars with hyphens
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '-', text)
        result = text.strip('-')

        # Return a default if the result is empty
        return result if result else 'untitled'

    def extract_yaml_frontmatter(self, content):
        """Extract YAML frontmatter and return metadata + remaining content"""
        metadata = {}
        remaining_content = content

        if content.startswith('---\n'):
            try:
                end_idx = content.index('\n---\n', 4)
                yaml_content = content[4:end_idx]
                metadata = yaml.safe_load(yaml_content)
                remaining_content = content[end_idx + 5:]
            except (ValueError, yaml.YAMLError):
                pass

        return metadata, remaining_content

    def generate_denote_filename(self, original_path, metadata, content):
        """Generate Denote-style filename"""
        # Get creation time (use file mtime or metadata)
        file_stat = os.stat(original_path)
        created_time = datetime.fromtimestamp(file_stat.st_mtime)

        if metadata and 'created' in metadata:
            try:
                created_time = datetime.fromisoformat(str(metadata['created']))
            except:
                pass

        # Format timestamp
        timestamp = created_time.strftime('%Y%m%dT%H%M%S')

        # Extract title - start with filename stem as fallback
        title = Path(original_path).stem

        # Try to get title from metadata
        if metadata:
            if 'title' in metadata and metadata['title']:
                title = str(metadata['title'])
            elif 'aliases' in metadata and metadata['aliases']:
                if isinstance(metadata['aliases'], list) and metadata['aliases']:
                    title = str(metadata['aliases'][0])
                elif isinstance(metadata['aliases'], str):
                    title = metadata['aliases']

        # Try to extract first heading as title if still using filename
        if title == Path(original_path).stem and content:
            heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if heading_match:
                title = heading_match.group(1)

        # Ensure title is not None or empty
        if not title:
            title = 'untitled'

        title_slug = self.slugify(title)

        # Extract tags
        tags = []
        if metadata and 'tags' in metadata:
            if isinstance(metadata['tags'], list):
                tags = [str(tag) for tag in metadata['tags'] if tag]
            elif isinstance(metadata['tags'], str):
                tags = [metadata['tags']]

        # Also extract inline tags from content
        if content:
            inline_tags = re.findall(r'#(\w+)', content)
            tags.extend(inline_tags)

        # Remove duplicates and filter out None/empty values
        tags = list(set(tag for tag in tags if tag))

        # Build filename
        if tags:
            tags_str = '__' + '_'.join(self.slugify(tag) for tag in tags)
        else:
            tags_str = ''

        extension = '.org' if self.output_format == 'org' else '.md'
        filename = f"{timestamp}--{title_slug}{tags_str}{extension}"

        return filename, title, tags, created_time

    def convert_links(self, content, is_org=False):
        """Convert Obsidian wiki-links to appropriate format"""
        if is_org:
            # Convert [[link]] to [[file:link.org][link]] for org-mode
            def replace_link(match):
                link_text = match.group(1)
                if '|' in link_text:
                    link, desc = link_text.split('|', 1)
                else:
                    link = desc = link_text

                # Check if link is in our file mapping
                for old_name, new_name in self.file_mapping.items():
                    if Path(old_name).stem == link:
                        link = Path(new_name).stem
                        break

                return f"[[file:{link}.org][{desc}]]"

            content = re.sub(r'\[\[([^\]]+)\]\]', replace_link, content)

            # Convert embedded images/files
            content = re.sub(r'!\[\[([^\]]+)\]\]', r'[[file:\1]]', content)

        elif not self.preserve_links:
            # Convert wiki-links to standard markdown links
            def replace_link(match):
                link_text = match.group(1)
                if '|' in link_text:
                    link, desc = link_text.split('|', 1)
                else:
                    link = desc = link_text

                # Check if link is in our file mapping
                for old_name, new_name in self.file_mapping.items():
                    if Path(old_name).stem == link:
                        link = Path(new_name).stem
                        break

                return f"[{desc}]({link}.md)"

            content = re.sub(r'\[\[([^\]]+)\]\]', replace_link, content)

        return content

    def find_asset(self, file_ref, source_dir):
        """Find asset file in vault (handles Obsidian's asset resolution)"""
        # Get the vault root (assuming we're converting from a vault)
        current_dir = Path(source_dir)
        vault_root = current_dir

        # Find vault root by looking for .obsidian folder
        while vault_root.parent != vault_root:
            if (vault_root / '.obsidian').exists():
                break
            vault_root = vault_root.parent
        else:
            # If no .obsidian found, use the input directory as root
            vault_root = current_dir

        # Remove any alias from reference
        if '|' in file_ref:
            file_ref = file_ref.split('|')[0].strip()

        # Clean the reference
        file_ref = file_ref.strip()

        # Try different locations where Obsidian might store assets
        possible_paths = [
            current_dir / file_ref,  # Relative to current file's directory
            vault_root / file_ref,  # Relative to vault root
            vault_root / 'attachments' / file_ref,  # Common attachments folder
            vault_root / 'Attachments' / file_ref,  # Case variation
            vault_root / 'assets' / file_ref,  # Common assets folder
            vault_root / 'Assets' / file_ref,  # Case variation
            vault_root / 'images' / file_ref,  # Common images folder
            vault_root / 'Images' / file_ref,  # Case variation
            vault_root / 'Files' / file_ref,  # Another common folder
            current_dir / 'attachments' / file_ref,  # Local attachments
            current_dir / 'assets' / file_ref,  # Local assets
        ]

        # Check each possible path
        for path in possible_paths:
            if path.exists() and path.is_file():
                print(f"  Found asset: {file_ref} at {path}")
                return path

        # Last resort: search entire vault for the filename
        search_name = Path(file_ref).name
        print(f"  Searching vault for: {search_name}")
        for path in vault_root.rglob(search_name):
            if path.is_file():
                print(f"  Found asset via search: {file_ref} at {path}")
                return path

        print(f"  Asset NOT found: {file_ref}")
        return None

    def copy_asset(self, asset_path, output_dir):
        """Copy asset to output directory and return relative path"""
        assets_dir = Path(output_dir) / self.assets_dir

        # Generate unique filename to avoid conflicts
        hash_suffix = hashlib.md5(str(asset_path).encode()).hexdigest()[:8]
        new_name = f"{asset_path.stem}_{hash_suffix}{asset_path.suffix}"

        dest_path = assets_dir / new_name

        # Copy file if not already copied
        if str(asset_path) not in self.asset_mapping:
            shutil.copy2(asset_path, dest_path)
            self.asset_mapping[str(asset_path)] = str(dest_path.relative_to(output_dir))
            print(f"  Copied asset: {asset_path.name} -> {dest_path.name}")

        return self.asset_mapping[str(asset_path)]

    def process_assets(self, content, source_dir, output_dir, is_org=False):
        """Process and copy referenced assets (images, PDFs, etc.)"""
        if self.assets_handling == 'ignore':
            return content

        # Create assets directory if copying
        if self.assets_handling == 'copy':
            assets_path = Path(output_dir) / self.assets_dir
            assets_path.mkdir(exist_ok=True)

        # Find all embedded files and links
        # Obsidian embeds: ![[file.pdf]], ![[image.png]]
        embed_pattern = r'!\[\[([^\]]+)\]\]'
        # Standard markdown images: ![alt](path/to/image.png)
        md_img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        # Obsidian attachments: [[file.pdf]]
        attach_pattern = r'(?<!\!)\[\[([^\]|]+\.(?:pdf|docx?|xlsx?|pptx?|zip|mp4|mp3|wav)(?:\|[^\]]+)?)\]\]'

        def process_embed(match):
            """Process embedded files"""
            file_ref = match.group(1)

            # Check if it's an internal link (to another note) vs asset
            if not any(file_ref.endswith(ext) for ext in
                      ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.pdf',
                       '.mp4', '.mp3', '.wav', '.mov', '.docx', '.xlsx', '.pptx']):
                # It's likely a note reference, not an asset
                return match.group(0)

            # Find the actual file
            asset_path = self.find_asset(file_ref, source_dir)
            if not asset_path:
                print(f"Warning: Asset not found: {file_ref}")
                return match.group(0)

            # Process based on handling mode
            if self.assets_handling == 'copy':
                new_path = self.copy_asset(asset_path, output_dir)
                if is_org:
                    return f"[[file:{new_path}]]"
                else:
                    return f"![{asset_path.stem}]({new_path})"
            else:  # link mode
                if is_org:
                    return f"[[file:{asset_path}]]"
                else:
                    return f"![{asset_path.stem}]({asset_path})"

        def process_md_image(match):
            """Process markdown images"""
            alt_text = match.group(1)
            img_path = match.group(2)

            # Skip URLs
            if img_path.startswith(('http://', 'https://')):
                return match.group(0)

            asset_path = self.find_asset(img_path, source_dir)
            if not asset_path:
                print(f"Warning: Image not found: {img_path}")
                return match.group(0)

            if self.assets_handling == 'copy':
                new_path = self.copy_asset(asset_path, output_dir)
                if is_org:
                    return f"[[file:{new_path}]]"
                else:
                    return f"![{alt_text}]({new_path})"
            else:  # link mode
                if is_org:
                    return f"[[file:{asset_path}]]"
                else:
                    return match.group(0)

        def process_attachment(match):
            """Process non-image attachments"""
            file_info = match.group(1)
            if '|' in file_info:
                file_ref, desc = file_info.split('|', 1)
            else:
                file_ref = file_info
                desc = Path(file_ref).stem

            asset_path = self.find_asset(file_ref, source_dir)
            if not asset_path:
                print(f"Warning: Attachment not found: {file_ref}")
                return match.group(0)

            if self.assets_handling == 'copy':
                new_path = self.copy_asset(asset_path, output_dir)
                if is_org:
                    return f"[[file:{new_path}][{desc}]]"
                else:
                    return f"[{desc}]({new_path})"
            else:  # link mode
                if is_org:
                    return f"[[file:{asset_path}][{desc}]]"
                else:
                    return f"[{desc}]({asset_path})"

        # Process content
        content = re.sub(embed_pattern, process_embed, content)
        content = re.sub(md_img_pattern, process_md_image, content)
        content = re.sub(attach_pattern, process_attachment, content)

        return content

    def convert_to_org(self, content, metadata, title, tags):
        """Convert markdown content to org-mode format"""
        lines = content.split('\n')
        org_lines = []

        # Add org-mode header
        org_lines.append(f"#+title: {title}")
        org_lines.append(f"#+date: {datetime.now().strftime('%Y-%m-%d')}")

        if tags:
            org_lines.append(f"#+filetags: {' '.join(':' + tag + ':' for tag in tags)}")

        # Add other metadata as properties
        if metadata:
            org_lines.append("\n:PROPERTIES:")
            for key, value in metadata.items():
                if key not in ['title', 'tags', 'aliases']:
                    org_lines.append(f":{key.upper()}: {value}")
            org_lines.append(":END:")

        org_lines.append("")  # Empty line after header

        in_code_block = False
        code_lang = ""

        for line in lines:
            # Handle code blocks
            if line.startswith('```'):
                if not in_code_block:
                    code_lang = line[3:].strip()
                    org_lines.append(f"#+BEGIN_SRC {code_lang}")
                    in_code_block = True
                else:
                    org_lines.append("#+END_SRC")
                    in_code_block = False
                continue

            if in_code_block:
                org_lines.append(line)
                continue

            # Convert headers
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                header_text = line[level:].strip()
                org_lines.append('*' * level + ' ' + header_text)
                continue

            # Convert emphasis
            line = re.sub(r'\*\*(.+?)\*\*', r'*\1*', line)  # Bold
            line = re.sub(r'__(.+?)__', r'*\1*', line)  # Bold alt
            line = re.sub(r'\*(.+?)\*', r'/\1/', line)  # Italic
            line = re.sub(r'_(.+?)_', r'/\1/', line)  # Italic alt
            line = re.sub(r'~~(.+?)~~', r'+\1+', line)  # Strikethrough
            line = re.sub(r'`([^`]+)`', r'~\1~', line)  # Inline code

            # Convert lists
            line = re.sub(r'^(\s*)[-*+]\s', r'\1- ', line)  # Unordered lists
            line = re.sub(r'^(\s*)(\d+)\.\s', r'\1\2. ', line)  # Ordered lists

            # Convert checkboxes
            line = re.sub(r'^(\s*)- \[ \]\s', r'\1- [ ] ', line)
            line = re.sub(r'^(\s*)- \[x\]\s', r'\1- [X] ', line)

            org_lines.append(line)

        content = '\n'.join(org_lines)
        return self.convert_links(content, is_org=True)

    def convert_file(self, input_path, output_dir, relative_path=None, preserve_structure=False, vault_root=None):
        """Convert a single Obsidian file to Denote format
        
        Args:
            input_path: Path to input file
            output_dir: Base output directory
            relative_path: Relative path from input base directory
            preserve_structure: Whether to preserve directory structure
            vault_root: Root directory of the Obsidian vault

        """
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata, remaining_content = self.extract_yaml_frontmatter(content)

        # Get source directory for asset resolution
        source_dir = input_path.parent
        if vault_root is None:
            vault_root = source_dir

        # Process assets before other conversions
        remaining_content = self.process_assets(
            remaining_content,
            source_dir,
            output_dir,
            is_org=(self.output_format == 'org')
        )

        # Generate Denote filename
        denote_filename, title, tags, created_time = self.generate_denote_filename(
            input_path, metadata, remaining_content
        )

        # Store mapping for link conversion
        self.file_mapping[input_path] = denote_filename

        # Convert content
        if self.output_format == 'org':
            converted_content = self.convert_to_org(
                remaining_content, metadata, title, tags
            )
        else:
            # Keep as markdown but update links
            converted_content = self.convert_links(remaining_content, is_org=False)

            # Optionally add Denote-style front matter comment
            header_lines = [
                "---",
                f"title: {title}",
                f"date: {created_time.strftime('%Y-%m-%d')}",
                f"tags: {', '.join(tags)}",
                f"identifier: {created_time.strftime('%Y%m%dT%H%M%S')}",
                "---",
                "",
            ]
            converted_content = '\n'.join(header_lines) + converted_content

        # Determine output path
        if preserve_structure and relative_path:
            # Preserve directory structure
            output_subdir = Path(output_dir) / relative_path.parent
            output_subdir.mkdir(parents=True, exist_ok=True)
            output_path = output_subdir / denote_filename
        else:
            # Flat structure (Denote default)
            output_path = Path(output_dir) / denote_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)

        return denote_filename, output_path

    def convert_directory(self, input_dir, output_dir, preserve_structure=False, add_folder_tags=False):
        """Convert all Obsidian files in a directory
        
        Args:
            input_dir: Input directory containing Obsidian files
            output_dir: Output directory for Denote files
            preserve_structure: Whether to preserve directory structure
            add_folder_tags: Whether to add folder names as tags

        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # First pass: collect all files for mapping
        md_files = list(input_path.glob('**/*.md'))

        print(f"Found {len(md_files)} markdown files to convert")
        if self.assets_handling == 'copy':
            print(f"Assets will be copied to {self.assets_dir}/ directory")

        converted_files = []
        for md_file in md_files:
            try:
                relative_path = md_file.relative_to(input_path)

                # Optionally add folder as tag
                if add_folder_tags and relative_path.parent != Path('.'):
                    # Read file to add folder tags
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    metadata, remaining = self.extract_yaml_frontmatter(content)
                    if metadata is None:
                        metadata = {}

                    # Add folder names as tags
                    folder_tags = [self.slugify(part) for part in relative_path.parent.parts]
                    if 'tags' not in metadata:
                        metadata['tags'] = []
                    elif isinstance(metadata['tags'], str):
                        metadata['tags'] = [metadata['tags']]
                    metadata['tags'].extend(folder_tags)

                new_filename, output_file_path = self.convert_file(
                    md_file, output_dir, relative_path, preserve_structure, vault_root=input_path
                )
                converted_files.append((md_file, output_file_path))

                # Display progress with structure info
                if preserve_structure:
                    print(f"Converted: {relative_path} -> {output_file_path.relative_to(output_path)}")
                else:
                    print(f"Converted: {md_file.name} -> {new_filename}")

            except Exception as e:
                print(f"Error converting {md_file}: {e}")
                import traceback
                traceback.print_exc()

        return converted_files

def main():
    parser = argparse.ArgumentParser(
        description='Convert Obsidian markdown files to Denote format'
    )
    parser.add_argument(
        'input',
        help='Input file or directory containing Obsidian markdown files'
    )
    parser.add_argument(
        'output',
        help='Output directory for Denote files'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['org', 'md'],
        default='org',
        help='Output format: org for org-mode, md for markdown (default: org)'
    )
    parser.add_argument(
        '--preserve-links',
        action='store_true',
        help='Preserve wiki-style links in markdown output'
    )
    parser.add_argument(
        '--preserve-structure',
        action='store_true',
        help='Preserve directory structure (default: flatten to single directory per Denote convention)'
    )
    parser.add_argument(
        '--add-folder-tags',
        action='store_true',
        help='Add folder names as tags to help maintain context when flattening'
    )
    parser.add_argument(
        '--assets',
        choices=['copy', 'link', 'ignore'],
        default='copy',
        help='How to handle assets: copy (default), link (keep paths), or ignore'
    )
    parser.add_argument(
        '--assets-dir',
        default='assets',
        help='Directory name for copied assets (default: assets)'
    )

    args = parser.parse_args()

    converter = ObsidianToDenoteConverter(
        output_format=args.format,
        preserve_links=args.preserve_links,
        assets_handling=args.assets
    )

    # Set custom assets directory if specified
    if args.assets_dir:
        converter.assets_dir = args.assets_dir

    input_path = Path(args.input)

    if input_path.is_file():
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        new_filename, output_file_path = converter.convert_file(input_path, output_path)
        print(f"Converted: {input_path.name} -> {new_filename}")
    elif input_path.is_dir():
        converted = converter.convert_directory(
            input_path,
            args.output,
            preserve_structure=args.preserve_structure,
            add_folder_tags=args.add_folder_tags
        )
        print(f"\nConverted {len(converted)} files")

        if args.assets == 'copy' and converter.asset_mapping:
            print(f"Copied {len(converter.asset_mapping)} assets to {converter.assets_dir}/")

        if args.preserve_structure:
            print("Directory structure preserved in output")
        elif args.add_folder_tags:
            print("Flattened structure with folder names added as tags")
        else:
            print("Flattened to single directory (Denote default)")
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
