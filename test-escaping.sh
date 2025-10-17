#!/bin/bash

################################################################################
# test-escaping.sh - Shell Special Character Escaping Demonstration
#
# Purpose: Demonstrates proper escaping and handling of shell special characters
# including backticks, quotes, dollar signs, and other metacharacters.
#
# Special characters covered:
# - Backticks (`) - command substitution (legacy)
# - Single quotes (') - literal strings
# - Double quotes (") - variable expansion allowed
# - Dollar signs ($) - variable expansion
# - Backslashes (\) - escape character
# - Command substitution $() - modern alternative to backticks
# - Heredocs - multi-line strings
################################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

echo "=== Shell Escaping Test Suite ==="
echo

# ==============================================================================
# Section 1: Backticks - Legacy Command Substitution
# ==============================================================================
echo "1. BACKTICKS - Legacy Command Substitution"
echo "-------------------------------------------"

# Safe: Using backticks (deprecated but shown for reference)
# Note: Backticks are shown as examples, not executed in echo
echo 'Running command: `date`'
# Actual backtick usage (executed):
result=`ls -la | head -n 3`
echo "Result of backtick command stored (first 3 lines):"
echo "$result"

# Preferred: Modern command substitution with $()
current_date=$(date)
echo "Preferred method: \$(date) = $current_date"
echo

# ==============================================================================
# Section 2: Nested Quotes - Single and Double Quote Mixing
# ==============================================================================
echo "2. NESTED QUOTES - Mixing Single and Double Quotes"
echo "---------------------------------------------------"

# Double quotes with escaped inner double quotes
message="He said \"It's working!\" and I replied 'Great!'"
echo "$message"

# Single quotes with escaped single quote (using '\'' technique)
# Explanation: End single quote, add escaped single quote, start single quote again
echo 'She said "Don'\''t use `backticks` here"'

# Alternative: Use double quotes when you need single quotes inside
alt_message="She said \"Don't use \`backticks\` here\""
echo "$alt_message"
echo

# ==============================================================================
# Section 3: Command Substitution - Nested and Complex
# ==============================================================================
echo "3. COMMAND SUBSTITUTION - Nested Examples"
echo "------------------------------------------"

# Nested command substitution
output=$(echo "Nested $(date +%Y) inside")
echo "$output"

# Multiple levels of nesting
year=$(date +%Y)
nested_output=$(echo "Year $(echo $year) extracted")
echo "$nested_output"
echo

# ==============================================================================
# Section 4: Dollar Signs and Variables
# ==============================================================================
echo "4. DOLLAR SIGNS AND VARIABLES"
echo "------------------------------"

# Literal dollar sign (escaped)
price=\$100
echo "Price: $price"

# Variable with spaces in value (use quotes)
var="${HOME}/path with spaces"
echo "Path: $var"

# Prevent variable expansion with single quotes
literal='$HOME is not expanded'
echo "$literal"

# Show actual expansion
expanded="$HOME is expanded"
echo "$expanded"
echo

# ==============================================================================
# Section 5: Special Characters Collection
# ==============================================================================
echo "5. SPECIAL CHARACTERS - Complete Set"
echo "-------------------------------------"

# In double quotes, most special chars are literal except: $ ` \ " !
symbols="!@#\$%^&*(){}[]|\\;:<>?,./"
echo "Symbols in double quotes: $symbols"

# In single quotes, everything is literal (easiest way)
symbols_single='!@#$%^&*(){}[]|\;:<>?,./'
echo "Symbols in single quotes: $symbols_single"

# Individual escaping in double quotes
escaped="Escaped: \$ \` \" \\ "
echo "$escaped"
echo

# ==============================================================================
# Section 6: Heredocs - Multi-line String Handling
# ==============================================================================
echo "6. HEREDOCS - Multi-line Strings"
echo "--------------------------------"

# Quoted delimiter (EOF in quotes) - NO variable expansion
cat <<'EOF'
This heredoc contains (literal, not expanded):
- Backticks: `command`
- Quotes: "double" and 'single'
- Variables: $HOME and ${USER}
- Command sub: $(date)
- All special chars: !@#$%^&*()
EOF

echo
echo "Now with variable expansion (unquoted delimiter):"

# Unquoted delimiter - allows variable expansion
cat <<EOF
This heredoc expands variables:
- Current user: ${USER}
- Home directory: ${HOME}
- Current date: $(date +%Y-%m-%d)
EOF

echo

# ==============================================================================
# Section 7: Functions - Safe Escaping Techniques
# ==============================================================================
echo "7. FUNCTIONS - Safe Escaping Techniques"
echo "----------------------------------------"

# Function to safely echo a command without executing it
safe_echo_command() {
    local cmd="$1"
    echo "Command (not executed): $cmd"
}

safe_echo_command 'rm -rf /'
safe_echo_command "echo \$HOME"

# Function to demonstrate quoting variables
safe_file_operation() {
    local filename="$1"
    # Always quote variables to handle spaces and special chars
    if [[ -f "$filename" ]]; then
        echo "File exists: $filename"
    else
        echo "File does not exist: $filename"
    fi
}

safe_file_operation "file with spaces.txt"

# Function showing array handling (safe for filenames with spaces)
process_files() {
    local files=("file1.txt" "file with spaces.txt" "file'with'quotes.txt")
    for file in "${files[@]}"; do
        echo "Processing: $file"
    done
}

process_files
echo

# ==============================================================================
# Section 8: SQL and Injection-Style Strings (Safe Handling)
# ==============================================================================
echo "8. SQL INJECTION-STYLE STRINGS - Safe Storage"
echo "----------------------------------------------"

# Store dangerous strings safely in variables (don't execute them)
dangerous_sql="'; DROP TABLE users; --"
dangerous_shell='`rm -rf /`'

echo "Dangerous SQL (stored safely): $dangerous_sql"
echo "Dangerous shell (stored safely): $dangerous_shell"
echo "Key: These are just strings, not executed commands"
echo

# ==============================================================================
# Section 9: Regex and Backslash Handling
# ==============================================================================
echo "9. REGEX - Backslash and Pattern Handling"
echo "------------------------------------------"

# Backslashes need careful handling
regex_pattern='[`'"'"'"$\\]'
echo "Regex pattern: $regex_pattern"

# String replacement with special chars
test_string='Replace `backticks` and "quotes"'
# Using parameter expansion for simple replacements
sanitized="${test_string//\`/}"
echo "After removing backticks: $sanitized"
echo

# ==============================================================================
# Section 10: JSON and Mixed Content
# ==============================================================================
echo "10. JSON - Escaping for JSON Strings"
echo "-------------------------------------"

# Creating JSON with special characters (use jq for production)
json_message='He said "don'\''t use '\''backticks'\''"'
json_path='C:\\Users\\test\\file with spaces.txt'

cat <<EOF
{
  "command": "echo \`date\`",
  "message": "$json_message",
  "path": "$json_path",
  "regex": "[\`'\"\\\\]+"
}
EOF

echo
echo

# ==============================================================================
# Section 11: Best Practices Summary
# ==============================================================================
echo "11. BEST PRACTICES SUMMARY"
echo "============================"
cat <<'PRACTICES'

1. PREFER $() over backticks for command substitution
   Good: output=$(command)
   Avoid: output=`command`

2. QUOTE YOUR VARIABLES to handle spaces and special chars
   Good: rm "$filename"
   Bad:  rm $filename

3. USE SINGLE QUOTES for literal strings (no expansion)
   Good: echo 'Price: $100'

4. USE DOUBLE QUOTES when you need variable expansion
   Good: echo "User: $USER"

5. ESCAPE SPECIAL CHARS in double quotes: $ ` " \
   Good: echo "Price: \$100"

6. USE HEREDOCS for multi-line content
   - Quoted delimiter (<<'EOF') = no expansion
   - Unquoted delimiter (<<EOF) = allow expansion

7. ARRAYS are safer than word splitting
   Good: files=("a.txt" "b.txt"); for f in "${files[@]}"
   Bad:  files="a.txt b.txt"; for f in $files

8. USE [[ ]] instead of [ ] for better quoting behavior
   Good: [[ "$var" == "value" ]]
   Bad:  [ "$var" = "value" ]

9. NEVER USE eval unless absolutely necessary
   Dangerous: eval "$user_input"

10. USE printf instead of echo for complex formatting
    Good: printf '%s\n' "$variable"

PRACTICES

echo
echo "=== Test Suite Complete ==="
echo "All special character escaping examples demonstrated successfully!"
