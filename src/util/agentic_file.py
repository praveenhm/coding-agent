# This file has nothing to do with this project, this is independent
# All the code you need to create a powerful agent that can create and edit any file on your 
# computer using the new text_editor tool in the Anthropic API.

import anthropic
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from termcolor import colored
from dotenv import load_dotenv

# Constants
SYSTEM_PROMPT = """You are a helpful coding assistant with access to a text editor tool.
You can view and modify files using the following commands:
1. view - Use this to examine the contents of a file before making any changes
Parameters: path (required), view_range (optional)

Example usage: View a file to understand its structure before editing
2. str_replace - Use this to modify file contents by replacing text
Parameters: path (required), old_str (required), new_str (required)

Important: The old_str must match EXACTLY with the content to replace
Best practice: First use view to see the file, then use str_replace
3. create - Use this to create a new file with content
Parameters: path (required), file_text (required)

Example usage: Create new test files, documentation, etc.
4. insert - Use this to add text at a specific location in a file
Parameters: path (required), insert_line (required), new_str (required)

Best practice: Use view first to identify the correct line number
5. undo_edit - Use this to revert the last edit made to a file
Parameters: path (required)

Example usage: When you need to undo a mistaken edit
IMPORTANT WORKFLOW:
1. When asked to modify a file, ALWAYS use view first to see the contents

2. For each modification task, use the appropriate command
3. When using str_replace, ensure the old_str matches exactly with whitespace and indentation
4. After making changes, summarize what you modified
For sequential operations, make sure to complete one tool operation fully before starting another.
"""


class ClaudeAgent:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-7-sonnet-20250219", max_tokens: int = 4000):
        """Initialize the Claude agent with API key and model.

        Args:
            api_key: Optional API key; if None, fetched from environment variable ANTHROPIC_API_KEY.
            model: The Anthropic model to use.
            max_tokens: Maximum tokens for Claude's responses.
        
        Raises:
            ValueError: If no API key is provided or found in the environment.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key.")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.conversation_history: List[Dict[str, Any]] = []
        self.file_backups: Dict[str, str] = {}  # For undo functionality
        self.system_prompt = SYSTEM_PROMPT

    def chat(self) -> None:
        """Start an interactive chat session with Claude."""
        if not self.api_key:
            print(colored("Error: API key is missing. Please set ANTHROPIC_API_KEY or pass api_key.", "red"))
            return
        print(colored("\n🤖 Claude Agent with Text Editor Tool", "cyan"))
        print(colored("Type 'exit' to quit, 'history' to see conversation history\n", "cyan"))
        while True:
            user_input = input(colored("You: ", "green"))
            if user_input.lower() == 'exit':
                print(colored("\nGoodbye! 👋", "cyan"))
                break
            if user_input.lower() == 'history':
                self._print_history()
                continue
            final_response = self._process_message(user_input)
            if final_response:
                self._print_assistant_response(final_response)

    def _process_message(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Process a user message and handle tool use.

        Args:
            user_message: The message input from the user.

        Returns:
            The final response from Claude, or None if an error occurs.
        """
        self.conversation_history.append({
            "role": "user",
            "content": [{"type": "text", "text": user_message}]
        })
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=[{"type": "text_editor_20250124", "name": "str_replace_editor"}],
                messages=self.conversation_history
            )
            self.conversation_history.append({"role": "assistant", "content": response.content})
            while response.stop_reason == "tool_use":
                for content_item in response.content:
                    if content_item.type == "tool_use":
                        tool_result = self._handle_tool_use(content_item)
                        self.conversation_history.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": content_item.id,
                                "content": tool_result
                            }]
                        })
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.system_prompt,
                    tools=[{"type": "text_editor_20250124", "name": "str_replace_editor"}],
                    messages=self.conversation_history
                )
                self.conversation_history.append({"role": "assistant", "content": response.content})
            return response
        except Exception as e:
            print(colored(f"\nError: {str(e)}", "red"))
            return None

    def _handle_tool_use(self, tool_use: Dict[str, Any]) -> str:
        """Handle tool use requests from Claude using pattern matching.

        Args:
            tool_use: The tool use request from Claude.

        Returns:
            Result of the tool operation as a string.
        """
        print(colored(f"\n🛠️ Using tool: {tool_use.name}", "yellow"))
        try:
            input_params = tool_use.input
            command = input_params.get('command', '')
            file_path = input_params.get('path', '')
            print(colored(f"Command: {command} on {file_path}", "yellow"))

            match command:
                case 'view':
                    view_range = input_params.get('view_range', None)
                    return self._view_file(file_path, view_range)
                case 'str_replace':
                    old_str = input_params.get('old_str', '')
                    new_str = input_params.get('new_str', '')
                    return self._replace_in_file(file_path, old_str, new_str)
                case 'create':
                    file_text = input_params.get('file_text', '')
                    return self._create_file(file_path, file_text)
                case 'insert':
                    insert_line = input_params.get('insert_line', 0)
                    new_str = input_params.get('new_str', '')
                    return self._insert_in_file(file_path, insert_line, new_str)
                case 'undo_edit':
                    return self._undo_edit(file_path)
                case _:
                    return f"Error: Unknown command '{command}'"
        except Exception as e:
            return f"Error executing {tool_use.name}: {str(e)}"

    def _view_file(self, file_path: str, view_range: Optional[List[int]] = None) -> str:
        """View file contents.

        Args:
            file_path: Path to the file.
            view_range: Optional range of lines to view [start, end].

        Returns:
            File contents with line numbers or an error message.
        """
        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found: {file_path}"
        try:
            with path.open('r', encoding='utf-8') as f:
                lines = f.readlines()
            if view_range:
                start = max(0, view_range[0] - 1)  # Convert to 0-indexed
                end = view_range[1] if view_range[1] != -1 else len(lines)
                lines = lines[start:end]
            return ''.join(f"{i + (view_range[0] if view_range else 1)}: {line}" for i, line in enumerate(lines))
        except PermissionError:
            return f"Error: Permission denied when accessing {file_path}"
        except Exception as e:
            return f"Error viewing file: {str(e)}"

    def _create_file(self, file_path: str, file_text: str) -> str:
        """Create a new file with the specified content.

        Args:
            file_path: Path to the new file.
            file_text: Content to write to the file.

        Returns:
            Success or error message.
        """
        path = Path(file_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                return f"Error: File already exists: {file_path}"
            with path.open('w', encoding='utf-8') as f:
                f.write(file_text)
            return f"Successfully created file: {file_path}"
        except PermissionError:
            return f"Error: Permission denied when creating {file_path}"
        except Exception as e:
            return f"Error creating file: {str(e)}"

    def _replace_in_file(self, file_path: str, old_str: str, new_str: str) -> str:
        """Replace text in a file.

        Args:
            file_path: Path to the file.
            old_str: Text to replace.
            new_str: Replacement text.

        Returns:
            Success or error message.
        """
        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found: {file_path}"
        try:
            self._backup_file(file_path)
            with path.open('r', encoding='utf-8') as f:
                content = f.read()
            count = content.count(old_str)
            if count == 0:
                return f"Error: Text not found in {file_path}"
            if count > 1:
                return f"Error: Multiple matches ({count}) found in {file_path}"
            new_content = content.replace(old_str, new_str, 1)
            with path.open('w', encoding='utf-8') as f:
                f.write(new_content)
            return "Successfully replaced text at exactly one location."
        except PermissionError:
            return f"Error: Permission denied when accessing {file_path}"
        except Exception as e:
            return f"Error replacing text: {str(e)}"

    def _insert_in_file(self, file_path: str, insert_line: int, new_str: str) -> str:
        """Insert text at a specific line in a file.

        Args:
            file_path: Path to the file.
            insert_line: Line number to insert at (1-indexed).
            new_str: Text to insert.

        Returns:
            Success or error message.
        """
        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found: {file_path}"
        try:
            self._backup_file(file_path)
            with path.open('r', encoding='utf-8') as f:
                lines = f.readlines()
            if insert_line > len(lines):
                return f"Error: Line number {insert_line} exceeds file length ({len(lines)})"
            lines.insert(insert_line - 1, new_str if new_str.endswith('\n') else new_str + '\n')
            with path.open('w', encoding='utf-8') as f:
                f.writelines(lines)
            return f"Successfully inserted text at line {insert_line}."
        except PermissionError:
            return f"Error: Permission denied when accessing {file_path}"
        except Exception as e:
            return f"Error inserting text: {str(e)}"

    def _undo_edit(self, file_path: str) -> str:
        """Undo the last edit to a file.

        Args:
            file_path: Path to the file.

        Returns:
            Success or error message.
        """
        if file_path not in self.file_backups:
            return f"Error: No backup found for {file_path}"
        try:
            with Path(file_path).open('w', encoding='utf-8') as f:
                f.write(self.file_backups[file_path])
            del self.file_backups[file_path]
            return f"Successfully restored {file_path} to previous state."
        except PermissionError:
            return f"Error: Permission denied when accessing {file_path}"
        except Exception as e:
            return f"Error undoing edit: {str(e)}"

    def _backup_file(self, file_path: str) -> None:
        """Create a backup of a file before editing.

        Args:
            file_path: Path to the file to back up.
        """
        if file_path not in self.file_backups:
            try:
                with Path(file_path).open('r', encoding='utf-8') as f:
                    self.file_backups[file_path] = f.read()
            except Exception:
                pass

    def _print_assistant_response(self, response: Dict[str, Any]) -> None:
        """Print the assistant's response.

        Args:
            response: The response from Claude.
        """
        if not response:
            return
        print(colored("\nClaude: ", "blue"), end="")
        for content in response.content:
            if content.type == "text":
                print(colored(content.text, "blue"))

    def _print_history(self) -> None:
        """Print the conversation history."""
        print(colored("\n===== Conversation History =====", "cyan"))
        for message in self.conversation_history:
            role = message["role"]
            if role == "user":
                content = message["content"][0]
                if content["type"] == "text":
                    print(colored(f"\nYou: {content['text']}", "green"))
                elif content["type"] == "tool_result":
                    print(colored(f"\nTool Result: [ID: {content['tool_use_id']}]", "yellow"))
            elif role == "assistant":
                print(colored("\nClaude: ", "blue"), end="")
                for content in message["content"]:
                    if content.type == "text":
                        print(colored(content.text, "blue"))
                    elif content.type == "tool_use":
                        print(colored(f"[Used tool: {content.name}]", "yellow"))
        print(colored("\n===============================", "cyan"))


def main() -> None:
    """Main function to run the Claude agent."""
    try:
        load_dotenv()
        agent = ClaudeAgent()
        agent.chat()
    except KeyboardInterrupt:
        print(colored("\nGoodbye! 👋", "cyan"))
    except Exception as e:
        print(colored(f"\nError: {str(e)}", "red"))


if __name__ == "__main__":
    main()
