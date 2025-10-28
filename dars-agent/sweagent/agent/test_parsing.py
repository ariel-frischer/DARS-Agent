from __future__ import annotations

import pytest
from unittest.mock import Mock
from sweagent.agent.parsing import (
    ActionParser,
    ThoughtActionParser,
    XMLThoughtActionParser,
    EditFormat,
    Identity,
    JsonParser,
    ParseFunction,
    FormatError,
    extract_keys,
    should_quote,
)
from sweagent.agent.commands import Command


class TestActionParser:
    """Test suite for ActionParser"""

    @pytest.fixture
    def commands(self):
        """Create mock commands for testing"""
        cmd_ls = Mock(spec=Command)
        cmd_ls.name = "ls"
        cmd_cd = Mock(spec=Command)
        cmd_cd.name = "cd"
        cmd_cat = Mock(spec=Command)
        cmd_cat.name = "cat"
        return [cmd_ls, cmd_cd, cmd_cat]

    def test_valid_command(self, commands):
        """Test parsing a valid command"""
        parser = ActionParser()
        response = "ls -la"
        thought, action = parser(response, commands)
        assert thought == "ls -la"
        assert action == "ls -la"

    def test_valid_command_with_arguments(self, commands):
        """Test parsing a valid command with multiple arguments"""
        parser = ActionParser()
        response = "cat file.txt"
        thought, action = parser(response, commands)
        assert thought == "cat file.txt"
        assert action == "cat file.txt"

    def test_invalid_command(self, commands):
        """Test parsing an invalid command raises FormatError"""
        parser = ActionParser()
        response = "invalid_command arg1"
        with pytest.raises(FormatError):
            parser(response, commands)

    def test_empty_response(self, commands):
        """Test parsing empty response raises FormatError"""
        parser = ActionParser()
        response = ""
        with pytest.raises(FormatError):
            parser(response, commands)

    def test_whitespace_only_response(self, commands):
        """Test parsing whitespace-only response raises FormatError"""
        parser = ActionParser()
        response = "   \n\t  "
        with pytest.raises(FormatError):
            parser(response, commands)

    def test_command_with_leading_whitespace(self, commands):
        """Test parsing command with leading whitespace"""
        parser = ActionParser()
        response = "  ls -la"
        thought, action = parser(response, commands)
        assert action == "  ls -la"


class TestThoughtActionParser:
    """Test suite for ThoughtActionParser"""

    @pytest.fixture
    def commands(self):
        return [Mock(spec=Command, name="ls")]

    def test_basic_thought_action(self, commands):
        """Test parsing basic thought followed by action in code block"""
        parser = ThoughtActionParser()
        response = """Let me list the files.
```
ls -la
```"""
        thought, action = parser(response, commands)
        assert "Let me list the files." in thought
        assert action.strip() == "ls -la"

    def test_multiple_code_blocks_takes_last(self, commands):
        """Test that multiple code blocks takes the last one"""
        parser = ThoughtActionParser()
        response = """First thought.
```
first command
```
Second thought.
```
second command
```"""
        thought, action = parser(response, commands)
        assert action.strip() == "second command"
        assert "First thought." in thought
        assert "Second thought." in thought

    def test_code_block_with_language(self, commands):
        """Test parsing code block with language specifier"""
        parser = ThoughtActionParser()
        response = """Let me write some Python.
```python
print("hello")
```"""
        thought, action = parser(response, commands)
        assert action.strip() == 'print("hello")'

    def test_no_code_block(self, commands):
        """Test parsing response without code block raises FormatError"""
        parser = ThoughtActionParser()
        response = "Just some text without code block"
        with pytest.raises(FormatError):
            parser(response, commands)

    def test_unclosed_code_block(self, commands):
        """Test parsing unclosed code block raises FormatError"""
        parser = ThoughtActionParser()
        response = """Some thought.
```
ls -la"""
        with pytest.raises(FormatError):
            parser(response, commands)

    def test_empty_code_block(self, commands):
        """Test parsing empty code block"""
        parser = ThoughtActionParser()
        response = """Some thought.
```
```"""
        thought, action = parser(response, commands)
        assert action == ""

    def test_multiline_action(self, commands):
        """Test parsing multiline action in code block"""
        parser = ThoughtActionParser()
        response = """Running multiple commands.
```
cd /tmp
ls -la
```"""
        thought, action = parser(response, commands)
        assert "cd /tmp" in action
        assert "ls -la" in action


class TestXMLThoughtActionParser:
    """Test suite for XMLThoughtActionParser"""

    @pytest.fixture
    def commands(self):
        return [Mock(spec=Command, name="ls")]

    def test_basic_xml_format(self, commands):
        """Test parsing basic XML format"""
        parser = XMLThoughtActionParser()
        response = """Let me list the files.
<command>
ls -la
</command>"""
        thought, action = parser(response, commands)
        assert "Let me list the files." in thought
        assert action == "ls -la"

    def test_multiple_command_tags_takes_last(self, commands):
        """Test that multiple command tags takes the last one"""
        parser = XMLThoughtActionParser()
        response = """First thought.
<command>
first command
</command>
Second thought.
<command>
second command
</command>"""
        thought, action = parser(response, commands)
        assert action == "second command"
        assert "First thought." in thought

    def test_missing_opening_tag(self, commands):
        """Test missing opening tag raises FormatError"""
        parser = XMLThoughtActionParser()
        response = """Some thought.
ls -la
</command>"""
        with pytest.raises(FormatError):
            parser(response, commands)

    def test_missing_closing_tag(self, commands):
        """Test missing closing tag raises FormatError"""
        parser = XMLThoughtActionParser()
        response = """Some thought.
<command>
ls -la"""
        with pytest.raises(FormatError):
            parser(response, commands)

    def test_empty_command_tag(self, commands):
        """Test empty command tag"""
        parser = XMLThoughtActionParser()
        response = """Some thought.
<command>
</command>"""
        thought, action = parser(response, commands)
        assert action == ""

    def test_thought_after_command(self, commands):
        """Test thought text after command tag is included"""
        parser = XMLThoughtActionParser()
        response = """Before.
<command>
ls -la
</command>
After command."""
        thought, action = parser(response, commands)
        assert "Before." in thought
        assert "After command." in thought
        assert action == "ls -la"


class TestJsonParser:
    """Test suite for JsonParser"""

    @pytest.fixture
    def commands(self):
        cmd = Mock(spec=Command)
        cmd.name = "ls"
        cmd.signature = "ls {path}"
        cmd.end_name = None
        return [cmd]

    def test_valid_json_with_command(self, commands):
        """Test parsing valid JSON with command"""
        parser = JsonParser()
        response = """{
            "thought": "Let me list files",
            "command": {
                "name": "ls",
                "arguments": {
                    "path": "/tmp"
                }
            }
        }"""
        thought, action = parser(response, commands)
        assert thought == "Let me list files"
        assert "ls" in action
        assert "/tmp" in action

    def test_json_missing_thought(self, commands):
        """Test JSON missing thought field raises FormatError"""
        parser = JsonParser()
        response = """{
            "command": {
                "name": "ls"
            }
        }"""
        with pytest.raises(FormatError, match="thought"):
            parser(response, commands)

    def test_json_missing_command(self, commands):
        """Test JSON missing command field raises FormatError"""
        parser = JsonParser()
        response = """{
            "thought": "Some thought"
        }"""
        with pytest.raises(FormatError, match="command"):
            parser(response, commands)

    def test_json_missing_command_name(self, commands):
        """Test JSON missing command name raises FormatError"""
        parser = JsonParser()
        response = """{
            "thought": "Some thought",
            "command": {
                "arguments": {"path": "/tmp"}
            }
        }"""
        with pytest.raises(FormatError, match="name"):
            parser(response, commands)

    def test_invalid_json(self, commands):
        """Test invalid JSON raises FormatError"""
        parser = JsonParser()
        response = "not valid json"
        with pytest.raises(FormatError, match="not valid JSON"):
            parser(response, commands)

    def test_json_array_not_object(self, commands):
        """Test JSON array instead of object raises FormatError"""
        parser = JsonParser()
        response = '[{"thought": "test"}]'
        with pytest.raises(FormatError, match="not a JSON object"):
            parser(response, commands)

    def test_command_not_dict(self, commands):
        """Test command value not being a dict raises FormatError"""
        parser = JsonParser()
        response = """{
            "thought": "test",
            "command": "ls"
        }"""
        with pytest.raises(FormatError, match="not a JSON object"):
            parser(response, commands)

    def test_unknown_command_name(self, commands):
        """Test unknown command name still generates action"""
        parser = JsonParser()
        response = """{
            "thought": "test",
            "command": {
                "name": "unknown",
                "arguments": {"arg1": "val1"}
            }
        }"""
        thought, action = parser(response, commands)
        assert "unknown" in action

    def test_command_without_arguments(self, commands):
        """Test command without arguments field"""
        parser = JsonParser()
        response = """{
            "thought": "test",
            "command": {
                "name": "ls"
            }
        }"""
        thought, action = parser(response, commands)
        assert thought == "test"
        assert "ls" in action


class TestIdentity:
    """Test suite for Identity parser"""

    def test_returns_same_response(self):
        """Test Identity parser returns response as both thought and action"""
        parser = Identity()
        response = "some command here"
        thought, action = parser(response, [])
        assert thought == response
        assert action == response

    def test_empty_response(self):
        """Test Identity parser with empty response"""
        parser = Identity()
        response = ""
        thought, action = parser(response, [])
        assert thought == ""
        assert action == ""


class TestEditFormat:
    """Test suite for EditFormat parser"""

    @pytest.fixture
    def commands(self):
        return [Mock(spec=Command, name="edit")]

    def test_edit_format_inherits_thought_action(self, commands):
        """Test EditFormat inherits from ThoughtActionParser"""
        parser = EditFormat()
        response = """Replacing content.
```
new content here
```"""
        thought, action = parser(response, commands)
        assert "Replacing content." in thought
        assert "new content here" in action


class TestExtractKeys:
    """Test suite for extract_keys function"""

    def test_extract_single_key(self):
        """Test extracting a single key from format string"""
        format_string = "ls {path}"
        keys = extract_keys(format_string)
        assert keys == {"path"}

    def test_extract_multiple_keys(self):
        """Test extracting multiple keys from format string"""
        format_string = "copy {source} to {destination}"
        keys = extract_keys(format_string)
        assert keys == {"source", "destination"}

    def test_extract_no_keys(self):
        """Test extracting keys from format string with no placeholders"""
        format_string = "ls -la"
        keys = extract_keys(format_string)
        assert keys == set()

    def test_extract_repeated_key(self):
        """Test extracting keys when same key appears multiple times"""
        format_string = "replace {word} with {word}"
        keys = extract_keys(format_string)
        # Set should contain unique keys only
        assert keys == {"word"}

    def test_extract_empty_string(self):
        """Test extracting keys from empty string"""
        format_string = ""
        keys = extract_keys(format_string)
        assert keys == set()


class TestShouldQuote:
    """Test suite for should_quote function"""

    def test_should_quote_string_value(self):
        """Test that string values should be quoted when end_name is None"""
        command = Mock(spec=Command, end_name=None)
        assert should_quote("some string", command) is True

    def test_should_not_quote_when_end_name_exists(self):
        """Test that string values should not be quoted when end_name exists"""
        command = Mock(spec=Command, end_name="end")
        assert should_quote("some string", command) is False

    def test_should_not_quote_non_string(self):
        """Test that non-string values should not be quoted"""
        command = Mock(spec=Command, end_name=None)
        assert should_quote(123, command) is False
        assert should_quote(None, command) is False
        assert should_quote([], command) is False


class TestParseFunction:
    """Test suite for ParseFunction base class"""

    def test_get_parser_by_name(self):
        """Test getting parser by name"""
        parser = ParseFunction.get("ActionParser")
        assert isinstance(parser, ActionParser)

        parser = ParseFunction.get("JsonParser")
        assert isinstance(parser, JsonParser)

    def test_get_invalid_parser_name(self):
        """Test getting parser with invalid name raises ValueError"""
        with pytest.raises(ValueError, match="not found"):
            ParseFunction.get("InvalidParser")

    def test_format_error_template_exists(self):
        """Test that format_error_template property exists"""
        parser = ActionParser()
        error_template = parser.format_error_template
        assert isinstance(error_template, str)
        assert len(error_template) > 0

    def test_abstract_call_not_implemented(self):
        """Test that abstract ParseFunction cannot be instantiated directly"""
        # ParseFunction is abstract, calling it should raise NotImplementedError
        parser = ParseFunction()
        with pytest.raises(NotImplementedError):
            parser("response", [])


class TestFormatError:
    """Test suite for FormatError exception"""

    def test_format_error_is_exception(self):
        """Test that FormatError is an Exception"""
        error = FormatError("test message")
        assert isinstance(error, Exception)

    def test_format_error_message(self):
        """Test that FormatError carries message"""
        message = "test error message"
        error = FormatError(message)
        assert str(error) == message


class TestEdgeCases:
    """Test edge cases across multiple parsers"""

    def test_unicode_in_response(self):
        """Test handling unicode characters"""
        parser = Identity()
        response = "Hello 世界 🌍"
        thought, action = parser(response, [])
        assert thought == response
        assert action == response

    def test_very_long_response(self):
        """Test handling very long responses"""
        parser = Identity()
        response = "x" * 10000
        thought, action = parser(response, [])
        assert len(thought) == 10000

    def test_special_characters_in_json(self):
        """Test JSON parsing with special characters"""
        parser = JsonParser()
        response = """{
            "thought": "File with \\"quotes\\" and \\n newlines",
            "command": {
                "name": "ls"
            }
        }"""
        thought, action = parser(response, [])
        assert "quotes" in thought

    def test_whitespace_handling(self):
        """Test various whitespace scenarios"""
        parser = ActionParser()
        cmd_ls = Mock(spec=Command)
        cmd_ls.name = "ls"
        commands = [cmd_ls]

        # Multiple spaces
        response = "ls    -la"
        thought, action = parser(response, commands)
        assert action == response

    def test_case_sensitivity(self):
        """Test case sensitivity in command names"""
        parser = ActionParser()
        cmd_ls = Mock(spec=Command)
        cmd_ls.name = "ls"
        commands = [cmd_ls]

        # Different case should raise error
        response = "LS -la"
        with pytest.raises(FormatError):
            parser(response, commands)
