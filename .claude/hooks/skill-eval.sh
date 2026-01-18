#!/bin/bash
# Skill Evaluation Hook
# Analyzes prompts and suggests relevant skills based on keywords, patterns, and file paths
#
# Called by: UserPromptSubmit hook in settings.json
# Input: $CLAUDE_USER_PROMPT (the user's prompt)
# Output: JSON feedback suggesting skills to activate

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_FILE="$SCRIPT_DIR/skill-rules.json"
PROMPT="${CLAUDE_USER_PROMPT:-}"

# If no rules file or no prompt, exit silently
if [ ! -f "$RULES_FILE" ] || [ -z "$PROMPT" ]; then
    exit 0
fi

# Check if Node.js is available for advanced matching
if command -v node &> /dev/null; then
    # Use Node.js for sophisticated matching
    node "$SCRIPT_DIR/skill-eval.js" "$PROMPT" "$RULES_FILE"
else
    # Fallback: simple keyword matching in bash
    PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')
    SUGGESTIONS=""
    
    # Simple keyword detection
    if echo "$PROMPT_LOWER" | grep -qE '\b(test|spec|jest|pytest|mock)\b'; then
        SUGGESTIONS="${SUGGESTIONS}testing-patterns, "
    fi
    
    if echo "$PROMPT_LOWER" | grep -qE '\b(debug|bug|error|fix|broken|issue)\b'; then
        SUGGESTIONS="${SUGGESTIONS}debug-detective, "
    fi
    
    if echo "$PROMPT_LOWER" | grep -qE '\b(component|react|hook|state|props)\b'; then
        SUGGESTIONS="${SUGGESTIONS}react-patterns, "
    fi
    
    if echo "$PROMPT_LOWER" | grep -qE '\b(api|endpoint|rest|graphql|query|mutation)\b'; then
        SUGGESTIONS="${SUGGESTIONS}api-design, "
    fi
    
    if echo "$PROMPT_LOWER" | grep -qE '\b(database|sql|query|schema|migration)\b'; then
        SUGGESTIONS="${SUGGESTIONS}database-patterns, "
    fi
    
    if echo "$PROMPT_LOWER" | grep -qE '\b(form|validation|input|submit)\b'; then
        SUGGESTIONS="${SUGGESTIONS}form-patterns, "
    fi
    
    # If we found suggestions, output them
    if [ -n "$SUGGESTIONS" ]; then
        SUGGESTIONS="${SUGGESTIONS%, }"  # Remove trailing comma
        echo "{\"feedback\": \"💡 Suggested skills: $SUGGESTIONS\"}"
    fi
fi

exit 0
