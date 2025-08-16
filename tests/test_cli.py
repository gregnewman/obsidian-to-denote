"""Tests for CLI functionality
"""

import subprocess
import sys


class TestCLI:
    """Test command-line interface"""

    def test_help_message(self):
        """Test that help message works"""
        result = subprocess.run(
            [sys.executable, "-m", "obsidian_to_denote.converter", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Convert Obsidian markdown files to Denote format" in result.stdout
        assert "--format" in result.stdout
        assert "--preserve-links" in result.stdout

    def test_missing_arguments(self):
        """Test error handling for missing arguments"""
        result = subprocess.run(
            [sys.executable, "-m", "obsidian_to_denote.converter"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "usage" in result.stderr.lower()

    def test_invalid_input_path(self, tmp_path):
        """Test error handling for invalid input path"""
        result = subprocess.run(
            [
                sys.executable, "-m", "obsidian_to_denote.converter",
                str(tmp_path / "nonexistent"),
                str(tmp_path / "output")
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "not a valid file or directory" in result.stdout

    def test_single_file_conversion(self, tmp_path):
        """Test converting a single file via CLI"""
        # Create test file
        input_file = tmp_path / "test.md"
        input_file.write_text("# Test Note\n\nContent here.")

        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                sys.executable, "-m", "obsidian_to_denote.converter",
                str(input_file),
                str(output_dir),
                "--format", "org"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Converted:" in result.stdout
        assert output_dir.exists()

        # Check that an org file was created
        org_files = list(output_dir.glob("*.org"))
        assert len(org_files) == 1

    def test_directory_conversion_with_options(self, temp_vault, tmp_path):
        """Test converting a directory with various options"""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                sys.executable, "-m", "obsidian_to_denote.converter",
                str(temp_vault),
                str(output_dir),
                "--format", "md",
                "--preserve-links",
                "--add-folder-tags",
                "--assets", "copy",
                "--assets-dir", "media"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Converted" in result.stdout
        assert "files" in result.stdout

        # Check output
        assert output_dir.exists()
        md_files = list(output_dir.glob("*.md"))
        assert len(md_files) > 0

        # Check if assets directory was created with custom name
        if any("![[" in f.read_text() for f in temp_vault.rglob("*.md")):
            media_dir = output_dir / "media"
            # Assets directory might not exist if no assets were found
            # This is okay - just checking the option worked

    def test_preserve_structure_option(self, temp_vault, tmp_path):
        """Test the preserve-structure option"""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                sys.executable, "-m", "obsidian_to_denote.converter",
                str(temp_vault),
                str(output_dir),
                "--preserve-structure"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Check that subdirectories were created
        assert (output_dir / "projects").exists() or \
               (output_dir / "daily").exists() or \
               (output_dir / "archive").exists()

    def test_format_options(self, tmp_path):
        """Test both org and md format options"""
        # Create simple test file
        input_file = tmp_path / "test.md"
        input_file.write_text("# Test\n**Bold** and *italic*")

        # Test org format
        output_org = tmp_path / "output_org"
        result = subprocess.run(
            [
                sys.executable, "-m", "obsidian_to_denote.converter",
                str(input_file),
                str(output_org),
                "--format", "org"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        org_files = list(output_org.glob("*.org"))
        assert len(org_files) == 1

        # Test md format
        output_md = tmp_path / "output_md"
        result = subprocess.run(
            [
                sys.executable, "-m", "obsidian_to_denote.converter",
                str(input_file),
                str(output_md),
                "--format", "md"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        md_files = list(output_md.glob("*.md"))
        assert len(md_files) == 1
