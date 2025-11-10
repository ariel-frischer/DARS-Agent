"""Unit tests for sweagent.agent.commands module.

Tests cover command parsing and documentation generation including:
- Command dataclass
- ParseCommandBash
- ParseCommandDetailed
- Bash function parsing
- Script parsing with @yaml
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sweagent.agent.commands import (
    Command,
    ParseCommand,
    ParseCommandBash,
    ParseCommandDetailed,
)


class TestCommand:
    """Test the Command dataclass."""

    def test_command_creation_minimal(self):
        """Test creating command with minimal required fields."""
        cmd = Command(code="ls -la", name="ls")
        assert cmd.code == "ls -la"
        assert cmd.name == "ls"
        assert cmd.docstring is None
        assert cmd.end_name is None

    def test_command_creation_full(self):
        """Test creating command with all fields."""
        cmd = Command(
            code="ls -la",
            name="ls",
            docstring="List files",
            end_name=None,
            arguments={"path": {"required": True}},
            signature="ls <path>",
        )
        assert cmd.code == "ls -la"
        assert cmd.name == "ls"
        assert cmd.docstring == "List files"
        assert cmd.end_name is None
        assert cmd.arguments == {"path": {"required": True}}
        assert cmd.signature == "ls <path>"

    def test_command_frozen(self):
        """Test that Command is frozen (immutable)."""
        cmd = Command(code="test", name="test")
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            cmd.name = "new_name"  # type: ignore

    def test_command_from_dict(self):
        """Test creating command from dictionary."""
        cmd_dict = {
            "code": "echo test",
            "name": "echo",
            "docstring": "Echo text",
        }
        cmd = Command.from_dict(cmd_dict)
        assert cmd.code == "echo test"
        assert cmd.name == "echo"
        assert cmd.docstring == "Echo text"


class TestParseCommand:
    """Test the ParseCommand abstract base class."""

    def test_get_parser_by_name(self):
        """Test retrieval of parser by name."""
        parser = ParseCommand.get("ParseCommandBash")
        assert isinstance(parser, ParseCommandBash)

    def test_get_parser_invalid_name(self):
        """Test that invalid parser name raises ValueError."""
        with pytest.raises(ValueError, match="Command parser.*not found"):
            ParseCommand.get("InvalidParser")


class TestParseCommandBash:
    """Test the ParseCommandBash class."""

    def test_parse_simple_bash_function(self):
        """Test parsing a simple bash function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""# @yaml
# docstring: List files in directory
ls_files() {
    ls -la
}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 1
        assert commands[0].name == "ls_files"
        assert "ls -la" in commands[0].code
        assert commands[0].docstring == "List files in directory"

    def test_parse_bash_function_with_arguments(self):
        """Test parsing bash function with documented arguments."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""# @yaml
# docstring: Change to directory
# arguments:
#   path:
#     required: true
#     type: string
#     description: Directory path
cd_dir() {
    cd "$1"
}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 1
        assert commands[0].name == "cd_dir"
        assert commands[0].arguments is not None
        assert "path" in commands[0].arguments
        assert commands[0].signature == "cd_dir <path>"

    def test_parse_bash_function_with_optional_argument(self):
        """Test parsing bash function with optional argument."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""# @yaml
# docstring: List files
# arguments:
#   path:
#     required: false
#     type: string
#     description: Directory path
list_files() {
    ls "${1:-.}"
}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 1
        assert commands[0].signature == "list_files [<path>]"

    def test_parse_multiple_bash_functions(self):
        """Test parsing file with multiple bash functions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""# @yaml
# docstring: First function
func1() {
    echo "one"
}

# @yaml
# docstring: Second function
func2() {
    echo "two"
}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 2
        assert commands[0].name == "func1"
        assert commands[1].name == "func2"

    def test_parse_script_with_shebang(self):
        """Test parsing a script file with shebang."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""#!/usr/bin/env python
# @yaml
# docstring: Python script command
print("Hello")
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            # Get the base name without extension
            expected_name = Path(f.name).name.rsplit(".", 1)[0]
            Path(f.name).unlink()

        assert len(commands) == 1
        assert commands[0].name == expected_name
        assert commands[0].docstring == "Python script command"

    def test_parse_script_with_arguments(self):
        """Test parsing script with arguments."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""#!/usr/bin/env python
# @yaml
# docstring: Script with args
# arguments:
#   input_file:
#     required: true
#     type: string
#     description: Input file
import sys
print(sys.argv[1])
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            expected_name = Path(f.name).name.rsplit(".", 1)[0]
            Path(f.name).unlink()

        assert len(commands) == 1
        assert "<input_file>" in commands[0].signature

    def test_parse_bash_function_with_end_name(self):
        """Test parsing bash function with end_name."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""# @yaml
# docstring: Multi-line edit
# end_name: end_edit
edit() {
    cat > file.txt
}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 1
        assert commands[0].end_name == "end_edit"

    def test_parse_bash_function_with_custom_signature(self):
        """Test parsing bash function with custom signature."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""# @yaml
# docstring: Custom signature
# signature: my_cmd --flag <arg>
my_cmd() {
    echo "$1"
}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 1
        assert commands[0].signature == "my_cmd --flag <arg>"

    def test_parse_non_shell_without_shebang_raises_error(self):
        """Test that non-shell file without shebang raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""# This is a Python file without shebang
print("hello")
""")
            f.flush()
            parser = ParseCommandBash()
            try:
                with pytest.raises(ValueError, match="does not have a .sh extension"):
                    parser.parse_command_file(f.name)
            finally:
                Path(f.name).unlink()

    def test_parse_script_multiple_yaml_raises_error(self):
        """Test that script with multiple @yaml tags raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""#!/usr/bin/env python
# @yaml
# docstring: First
# @yaml
# docstring: Second
print("hello")
""")
            f.flush()
            parser = ParseCommandBash()
            try:
                with pytest.raises(ValueError, match="multiple @yaml tags"):
                    parser.parse_command_file(f.name)
            finally:
                Path(f.name).unlink()

    def test_generate_command_docs_simple(self):
        """Test generating documentation for commands."""
        parser = ParseCommandBash()
        commands = [
            Command(code="ls", name="ls", docstring="List files", signature="ls [<path>]"),
            Command(code="cd", name="cd", docstring="Change directory", signature="cd <path>"),
        ]
        docs = parser.generate_command_docs(commands, [])
        assert "ls [<path>] - List files" in docs
        assert "cd <path> - Change directory" in docs

    def test_generate_command_docs_with_subroutines(self):
        """Test generating docs with subroutines."""
        parser = ParseCommandBash()
        commands = [Command(code="ls", name="ls", docstring="List files")]
        subroutines = [Command(code="sub", name="sub", docstring="Subroutine")]
        docs = parser.generate_command_docs(commands, subroutines)
        assert "List files" in docs
        assert "Subroutine" in docs

    def test_generate_command_docs_with_format_kwargs(self):
        """Test generating docs with format kwargs."""
        parser = ParseCommandBash()
        commands = [
            Command(code="test", name="test", docstring="Test {var}", signature="test"),
        ]
        docs = parser.generate_command_docs(commands, [], var="VALUE")
        assert "Test VALUE" in docs


class TestParseCommandDetailed:
    """Test the ParseCommandDetailed class."""

    def test_get_signature_simple(self):
        """Test getting signature for simple command."""
        cmd = Command(code="ls", name="ls")
        sig = ParseCommandDetailed.get_signature(cmd)
        assert sig == "ls"

    def test_get_signature_with_required_arg(self):
        """Test getting signature with required argument."""
        cmd = Command(
            code="cd",
            name="cd",
            arguments={"path": {"required": True, "type": "string", "description": "Path"}},
        )
        sig = ParseCommandDetailed.get_signature(cmd)
        assert sig == "cd <path>"

    def test_get_signature_with_optional_arg(self):
        """Test getting signature with optional argument."""
        cmd = Command(
            code="ls",
            name="ls",
            arguments={"path": {"required": False, "type": "string", "description": "Path"}},
        )
        sig = ParseCommandDetailed.get_signature(cmd)
        assert sig == "ls [<path>]"

    def test_get_signature_multiple_args(self):
        """Test getting signature with multiple arguments."""
        cmd = Command(
            code="copy",
            name="copy",
            arguments={
                "source": {"required": True, "type": "string", "description": "Source"},
                "dest": {"required": True, "type": "string", "description": "Destination"},
            },
        )
        sig = ParseCommandDetailed.get_signature(cmd)
        assert "<source>" in sig
        assert "<dest>" in sig

    def test_generate_command_docs_detailed(self):
        """Test generating detailed documentation."""
        parser = ParseCommandDetailed()
        commands = [
            Command(
                code="ls",
                name="ls",
                docstring="List files",
                signature="ls [<path>]",
                arguments={
                    "path": {
                        "required": False,
                        "type": "string",
                        "description": "Directory to list",
                    },
                },
            ),
        ]
        docs = parser.generate_command_docs(commands, [])
        assert "ls:" in docs
        assert "docstring: List files" in docs
        assert "signature: ls [<path>]" in docs
        assert "arguments:" in docs
        assert "path (string) [optional]: Directory to list" in docs

    def test_generate_command_docs_with_required_arg(self):
        """Test detailed docs with required argument."""
        parser = ParseCommandDetailed()
        commands = [
            Command(
                code="cd",
                name="cd",
                docstring="Change directory",
                arguments={
                    "path": {
                        "required": True,
                        "type": "string",
                        "description": "Target directory",
                    },
                },
            ),
        ]
        docs = parser.generate_command_docs(commands, [])
        assert "path (string) [required]: Target directory" in docs


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_parse_empty_bash_file(self):
        """Test parsing empty bash file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 0

    def test_parse_bash_file_with_comments_only(self):
        """Test parsing bash file with only comments."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""# This is a comment
# Another comment
# No functions here
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 0

    def test_parse_bash_function_without_yaml(self):
        """Test parsing bash function without @yaml docs."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""my_func() {
    echo "test"
}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 1
        assert commands[0].name == "my_func"
        assert commands[0].docstring is None

    def test_parse_bash_function_multiline_body(self):
        """Test parsing bash function with multiline body."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("""# @yaml
# docstring: Multiline function
multi() {
    echo "line 1"
    echo "line 2"
    echo "line 3"
}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 1
        assert "line 1" in commands[0].code
        assert "line 2" in commands[0].code
        assert "line 3" in commands[0].code

    def test_command_without_docstring_in_docs(self):
        """Test that command without docstring is handled in docs."""
        parser = ParseCommandBash()
        commands = [Command(code="test", name="test", docstring=None)]
        docs = parser.generate_command_docs(commands, [])
        # Should not crash, docs might be empty or minimal
        assert isinstance(docs, str)

    def test_parse_underscored_utility_file(self):
        """Test parsing file starting with underscore (utility file)."""
        with tempfile.NamedTemporaryFile(mode="w", prefix="_util", suffix=".py", delete=False) as f:
            f.write("""#!/usr/bin/env python
# Utility file without @yaml
def helper():
    pass
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        # Utility files can have zero commands
        assert isinstance(commands, list)

    def test_very_long_function_name(self):
        """Test parsing bash function with very long name."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            long_name = "very_long_function_name_" * 10
            f.write(f"""# @yaml
# docstring: Long name function
{long_name}() {{
    echo "test"
}}
""")
            f.flush()
            parser = ParseCommandBash()
            commands = parser.parse_command_file(f.name)
            Path(f.name).unlink()

        assert len(commands) == 1
        assert commands[0].name == long_name
