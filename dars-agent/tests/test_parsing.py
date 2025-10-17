"""Unit tests for sweagent.agent.parsing module.

Tests cover parsing functions for different model output formats including:
- ActionParser
- ThoughtActionParser
- XMLThoughtActionParser
- JsonParser
- EditFormat
- Identity
"""

from __future__ import annotations

import pytest

from sweagent.agent.commands import Command
from sweagent.agent.parsing import (
    ActionParser,
    EditFormat,
    FormatError,
    Identity,
    JsonParser,
    ParseFunction,
    ThoughtActionParser,
    XMLThoughtActionParser,
    extract_keys,
    should_quote,
)


class TestParseFunction:
    """Test the ParseFunction abstract base class."""

    def test_get_parser_by_name(self):
        """Test retrieval of parser instances by name."""
        parser = ParseFunction.get("ActionParser")
        assert isinstance(parser, ActionParser)

    def test_get_parser_invalid_name(self):
        """Test that invalid parser name raises ValueError."""
        with pytest.raises(ValueError, match="Model output parser.*not found"):
            ParseFunction.get("InvalidParser")

    def test_format_error_template(self):
        """Test that format_error_template is accessible."""
        parser = ActionParser()
        assert "{command_docs}" in parser.format_error_template


class TestActionParser:
    """Test the ActionParser class."""

    @pytest.fixture
    def commands(self):
        """Sample commands for testing."""
        return [
            Command(code="ls -la", name="ls", docstring="List files"),
            Command(code="cd {path}", name="cd", docstring="Change directory"),
            Command(code="cat {file}", name="cat", docstring="Show file contents"),
        ]

    def test_parse_valid_command_happy_path(self, commands):
        """Test parsing a valid single command."""
        parser = ActionParser()
        model_response = "ls -la"
        thought, action = parser(model_response, commands)
        assert thought == "ls -la"
        assert action == "ls -la"

    def test_parse_valid_command_with_args(self, commands):
        """Test parsing a valid command with arguments."""
        parser = ActionParser()
        model_response = "cd /home/user"
        thought, action = parser(model_response, commands)
        assert thought == "cd /home/user"
        assert action == "cd /home/user"

    def test_parse_invalid_command(self, commands):
        """Test that invalid command raises FormatError."""
        parser = ActionParser()
        model_response = "invalid_command arg1"
        with pytest.raises(FormatError, match="First word.*not a valid command"):
            parser(model_response, commands)

    def test_parse_empty_response(self, commands):
        """Test parsing empty response raises FormatError."""
        parser = ActionParser()
        model_response = ""
        with pytest.raises(FormatError, match="First word.*not a valid command"):
            parser(model_response, commands)

    def test_parse_whitespace_only(self, commands):
        """Test parsing whitespace-only response raises FormatError."""
        parser = ActionParser()
        model_response = "   \n  \t  "
        with pytest.raises(FormatError, match="First word.*not a valid command"):
            parser(model_response, commands)


class TestThoughtActionParser:
    """Test the ThoughtActionParser class."""

    @pytest.fixture
    def commands(self):
        """Sample commands for testing."""
        return [
            Command(code="ls", name="ls", docstring="List files"),
            Command(code="grep", name="grep", docstring="Search text"),
        ]

    def test_parse_thought_action_happy_path(self, commands):
        """Test parsing valid thought and action format."""
        parser = ThoughtActionParser()
        model_response = """Let's list the files in the directory.
```
ls -la
```"""
        thought, action = parser(model_response, commands)
        assert "Let's list the files" in thought
        assert action == "ls -la"

    def test_parse_with_language_specifier(self, commands):
        """Test parsing code block with language specifier."""
        parser = ThoughtActionParser()
        model_response = """Let's use bash to list files.
```bash
ls -la
```"""
        thought, action = parser(model_response, commands)
        assert "Let's use bash" in thought
        assert action == "ls -la"

    def test_parse_multiple_code_blocks_uses_last(self, commands):
        """Test that parser uses the last code block when multiple exist."""
        parser = ThoughtActionParser()
        model_response = """First, let's see what this does:
```
echo "test"
```
Now let's actually list the files:
```
ls -la
```"""
        thought, action = parser(model_response, commands)
        assert action == "ls -la"
        assert "echo" not in action

    def test_parse_nested_code_blocks_ignored(self, commands):
        """Test that nested code blocks are properly handled."""
        parser = ThoughtActionParser()
        model_response = """Here's what we'll do:
```
ls -la
```"""
        thought, action = parser(model_response, commands)
        assert action == "ls -la"

    def test_parse_no_code_block_raises_error(self, commands):
        """Test that missing code block raises FormatError."""
        parser = ThoughtActionParser()
        model_response = "Let's list files but I forgot the code block"
        with pytest.raises(FormatError, match="No action found"):
            parser(model_response, commands)

    def test_parse_unclosed_code_block_raises_error(self, commands):
        """Test that unclosed code block raises FormatError."""
        parser = ThoughtActionParser()
        model_response = """Let's list files
```
ls -la"""
        with pytest.raises(FormatError, match="No action found"):
            parser(model_response, commands)

    def test_parse_empty_code_block(self, commands):
        """Test parsing empty code block."""
        parser = ThoughtActionParser()
        model_response = """Let's do something
```
```"""
        thought, action = parser(model_response, commands)
        assert action == ""


class TestXMLThoughtActionParser:
    """Test the XMLThoughtActionParser class."""

    @pytest.fixture
    def commands(self):
        """Sample commands for testing."""
        return [
            Command(code="ls", name="ls", docstring="List files"),
        ]

    def test_parse_xml_format_happy_path(self, commands):
        """Test parsing valid XML format."""
        parser = XMLThoughtActionParser()
        model_response = """Let's list the files.
<command>
ls -la
</command>"""
        thought, action = parser(model_response, commands)
        assert "Let's list the files" in thought
        assert action == "ls -la"

    def test_parse_xml_multiple_commands_uses_last(self, commands):
        """Test that last command tag is used when multiple exist."""
        parser = XMLThoughtActionParser()
        model_response = """First command:
<command>
echo "test"
</command>
Second command:
<command>
ls -la
</command>"""
        thought, action = parser(model_response, commands)
        assert action == "ls -la"

    def test_parse_xml_no_command_tag_raises_error(self, commands):
        """Test that missing command tag raises FormatError."""
        parser = XMLThoughtActionParser()
        model_response = "Let's list files without tags"
        with pytest.raises(FormatError, match="No action found"):
            parser(model_response, commands)

    def test_parse_xml_missing_opening_tag(self, commands):
        """Test that missing opening tag raises FormatError."""
        parser = XMLThoughtActionParser()
        model_response = """Let's list files
ls -la
</command>"""
        with pytest.raises(FormatError, match="No action found"):
            parser(model_response, commands)

    def test_parse_xml_missing_closing_tag(self, commands):
        """Test that missing closing tag raises FormatError."""
        parser = XMLThoughtActionParser()
        model_response = """Let's list files
<command>
ls -la"""
        with pytest.raises(FormatError, match="No action found"):
            parser(model_response, commands)

    def test_parse_xml_empty_command(self, commands):
        """Test parsing empty command."""
        parser = XMLThoughtActionParser()
        model_response = """Let's do something
<command>
</command>"""
        thought, action = parser(model_response, commands)
        assert action == ""

    def test_parse_xml_whitespace_handling(self, commands):
        """Test that whitespace is properly trimmed."""
        parser = XMLThoughtActionParser()
        model_response = """Let's list files
<command>
  ls -la
</command>
Some text after"""
        thought, action = parser(model_response, commands)
        assert action == "ls -la"
        assert "Some text after" in thought


class TestJsonParser:
    """Test the JsonParser class."""

    @pytest.fixture
    def commands(self):
        """Sample commands for testing."""
        return [
            Command(
                code="ls",
                name="ls",
                docstring="List files",
                signature="ls {path}",
                arguments={"path": {"required": True, "type": "string", "description": "Path to list"}},
            ),
            Command(code="cd", name="cd", docstring="Change directory", end_name=None),
        ]

    def test_parse_json_happy_path(self, commands):
        """Test parsing valid JSON format."""
        parser = JsonParser()
        model_response = """{
            "thought": "I need to list the files",
            "command": {
                "name": "ls",
                "arguments": {
                    "path": "/home"
                }
            }
        }"""
        thought, action = parser(model_response, commands)
        assert thought == "I need to list the files"
        assert "ls" in action
        assert "/home" in action

    def test_parse_json_command_without_arguments(self, commands):
        """Test parsing JSON with command but no arguments."""
        parser = JsonParser()
        model_response = """{
            "thought": "Let's change directory",
            "command": {
                "name": "cd"
            }
        }"""
        thought, action = parser(model_response, commands)
        assert thought == "Let's change directory"
        assert action == "cd"

    def test_parse_json_invalid_json_raises_error(self, commands):
        """Test that invalid JSON raises FormatError."""
        parser = JsonParser()
        model_response = "{ invalid json }"
        with pytest.raises(FormatError, match="not valid JSON"):
            parser(model_response, commands)

    def test_parse_json_not_object_raises_error(self, commands):
        """Test that non-object JSON raises FormatError."""
        parser = JsonParser()
        model_response = '["array", "not", "object"]'
        with pytest.raises(FormatError, match="not a JSON object"):
            parser(model_response, commands)

    def test_parse_json_missing_thought_raises_error(self, commands):
        """Test that missing 'thought' key raises FormatError."""
        parser = JsonParser()
        model_response = """{
            "command": {
                "name": "ls"
            }
        }"""
        with pytest.raises(FormatError, match="'thought'.*missing"):
            parser(model_response, commands)

    def test_parse_json_missing_command_raises_error(self, commands):
        """Test that missing 'command' key raises FormatError."""
        parser = JsonParser()
        model_response = """{
            "thought": "I need to do something"
        }"""
        with pytest.raises(FormatError, match="'command'.*missing"):
            parser(model_response, commands)

    def test_parse_json_command_not_object_raises_error(self, commands):
        """Test that non-object command value raises FormatError."""
        parser = JsonParser()
        model_response = """{
            "thought": "test",
            "command": "ls"
        }"""
        with pytest.raises(FormatError, match="'command'.*not a JSON object"):
            parser(model_response, commands)

    def test_parse_json_missing_command_name_raises_error(self, commands):
        """Test that missing 'name' in command raises FormatError."""
        parser = JsonParser()
        model_response = """{
            "thought": "test",
            "command": {
                "arguments": {}
            }
        }"""
        with pytest.raises(FormatError, match="'name'.*missing"):
            parser(model_response, commands)

    def test_parse_json_unknown_command(self, commands):
        """Test parsing JSON with unknown command name."""
        parser = JsonParser()
        model_response = """{
            "thought": "Run unknown command",
            "command": {
                "name": "unknown_cmd",
                "arguments": {
                    "arg1": "value1"
                }
            }
        }"""
        thought, action = parser(model_response, commands)
        assert "unknown_cmd" in action

    def test_parse_json_argument_quoting(self, commands):
        """Test that arguments are properly quoted when needed."""
        parser = JsonParser()
        model_response = """{
            "thought": "List files with spaces",
            "command": {
                "name": "ls",
                "arguments": {
                    "path": "/path with spaces"
                }
            }
        }"""
        thought, action = parser(model_response, commands)
        # Should quote paths with spaces
        assert "path" in action or "with" in action


class TestEditFormat:
    """Test the EditFormat class (inherits from ThoughtActionParser)."""

    @pytest.fixture
    def commands(self):
        """Sample commands for testing."""
        return []

    def test_edit_format_inherits_thought_action_parser(self, commands):
        """Test that EditFormat inherits from ThoughtActionParser."""
        parser = EditFormat()
        model_response = """Let's edit the file.
```
import os
os.listdir()
```"""
        thought, action = parser(model_response, commands)
        assert "Let's edit" in thought
        assert "import os" in action


class TestIdentity:
    """Test the Identity parser class."""

    @pytest.fixture
    def commands(self):
        """Sample commands for testing."""
        return []

    def test_identity_returns_same_output(self, commands):
        """Test that Identity parser returns input as both thought and action."""
        parser = Identity()
        model_response = "This is the model response"
        thought, action = parser(model_response, commands)
        assert thought == model_response
        assert action == model_response

    def test_identity_with_empty_string(self, commands):
        """Test Identity parser with empty string."""
        parser = Identity()
        model_response = ""
        thought, action = parser(model_response, commands)
        assert thought == ""
        assert action == ""


class TestExtractKeys:
    """Test the extract_keys helper function."""

    def test_extract_keys_single_key(self):
        """Test extracting a single key from format string."""
        format_string = "ls {path}"
        keys = extract_keys(format_string)
        assert keys == {"path"}

    def test_extract_keys_multiple_keys(self):
        """Test extracting multiple keys from format string."""
        format_string = "copy {source} to {destination}"
        keys = extract_keys(format_string)
        assert keys == {"source", "destination"}

    def test_extract_keys_no_keys(self):
        """Test extracting keys from string with no placeholders."""
        format_string = "ls -la"
        keys = extract_keys(format_string)
        assert keys == set()

    def test_extract_keys_repeated_key(self):
        """Test that repeated keys are only included once."""
        format_string = "compare {file} with {file}"
        keys = extract_keys(format_string)
        assert keys == {"file"}

    def test_extract_keys_empty_string(self):
        """Test extracting keys from empty string."""
        format_string = ""
        keys = extract_keys(format_string)
        assert keys == set()


class TestShouldQuote:
    """Test the should_quote helper function."""

    def test_should_quote_string_value_no_end_name(self):
        """Test that string values are quoted when command has no end_name."""
        command = Command(code="ls", name="ls", end_name=None)
        assert should_quote("test string", command) is True

    def test_should_quote_string_value_with_end_name(self):
        """Test that string values are not quoted when command has end_name."""
        command = Command(code="edit", name="edit", end_name="end_edit")
        assert should_quote("test string", command) is False

    def test_should_quote_non_string_value(self):
        """Test that non-string values are not quoted."""
        command = Command(code="ls", name="ls", end_name=None)
        assert should_quote(123, command) is False
        assert should_quote(None, command) is False
        assert should_quote([], command) is False

    def test_should_quote_empty_string(self):
        """Test quoting behavior with empty string."""
        command = Command(code="ls", name="ls", end_name=None)
        assert should_quote("", command) is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def commands(self):
        """Sample commands for testing."""
        return [Command(code="test", name="test", docstring="Test command")]

    def test_very_long_model_response(self, commands):
        """Test parsing very long model response."""
        parser = ThoughtActionParser()
        long_thought = "A" * 10000
        model_response = f"""{long_thought}
```
test
```"""
        thought, action = parser(model_response, commands)
        assert len(thought) > 9000
        assert action == "test"

    def test_special_characters_in_thought(self, commands):
        """Test handling special characters in thought."""
        parser = ThoughtActionParser()
        model_response = """Let's test special chars: !@#$%^&*()
```
test
```"""
        thought, action = parser(model_response, commands)
        assert "!@#$%^&*()" in thought

    def test_unicode_characters(self, commands):
        """Test handling Unicode characters."""
        parser = ThoughtActionParser()
        model_response = """Let's test Unicode: 你好 мир 🚀
```
test
```"""
        thought, action = parser(model_response, commands)
        assert "你好" in thought
        assert "мир" in thought
        assert "🚀" in thought

    def test_newlines_in_action(self, commands):
        """Test handling newlines in action."""
        parser = ThoughtActionParser()
        model_response = """Let's run multiline
```
test \\
--arg1 \\
--arg2
```"""
        thought, action = parser(model_response, commands)
        assert "\\" in action or "arg1" in action
