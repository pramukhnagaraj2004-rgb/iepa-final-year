import json
import re
from typing import Dict, Any, Optional

class ErrorNormalizer:
    """
    Parses standard stderr compiler/interpreter outputs (GCC and CPython)
    into structured JSON error events.
    """
    
    def __init__(self):
        # GCC error format: file:line:column: error/warning: message
        self.gcc_pattern = re.compile(r'^(.*?):(\d+):(\d+):\s+(error|warning|note):\s+(.*)$')
        
        # Python traceback patterns
        self.py_file_pattern = re.compile(r'^  File "(.*?)", line (\d+)(?:, in (.*))?$')
        self.py_error_pattern = re.compile(r'^([A-Za-z0-9_]+Error|Exception):\s+(.*)$')

    def parse_c_error(self, stderr_output: str) -> list[Dict[str, Any]]:
        """
        Parses GCC stderr output.
        """
        events = []
        lines = stderr_output.strip().split('\n')
        
        for line in lines:
            match = self.gcc_pattern.match(line.strip())
            if match:
                file_path, line_num, col_num, severity, message = match.groups()
                # Reconstruct a generic raw error string for the weak labeler
                raw_error = f"{severity}: {message}"
                
                events.append({
                    "language": "c",
                    "file": file_path,
                    "line": int(line_num),
                    "column": int(col_num),
                    "severity": severity,
                    "message": message,
                    "raw_error": raw_error
                })
        
        return events

    def parse_python_error(self, stderr_output: str) -> list[Dict[str, Any]]:
        """
        Parses Python traceback output.
        """
        events = []
        lines = stderr_output.strip().split('\n')
        
        current_file = None
        current_line = None
        current_func = None
        
        for line in lines:
            # Check for file/line info
            file_match = self.py_file_pattern.match(line)
            if file_match:
                current_file, current_line, current_func = file_match.groups()
                continue
                
            # Check for the actual error type and message (usually at the end of traceback)
            err_match = self.py_error_pattern.match(line)
            if err_match:
                error_type, message = err_match.groups()
                
                events.append({
                    "language": "python",
                    "file": current_file if current_file else "unknown",
                    "line": int(current_line) if current_line else 0,
                    "severity": "error",
                    "error_type": error_type,
                    "message": message,
                    "raw_error": line.strip()
                })
        
        return events

    def normalize(self, stderr_output: str, language: str) -> list[Dict[str, Any]]:
        """
        Main entry point for the execution sandbox to call.
        """
        if not stderr_output or not stderr_output.strip():
            return []
            
        if language.lower() == 'c':
            return self.parse_c_error(stderr_output)
        elif language.lower() == 'python':
            return self.parse_python_error(stderr_output)
        else:
            raise ValueError(f"Unsupported language: {language}")


if __name__ == '__main__':
    # Test cases
    normalizer = ErrorNormalizer()
    
    mock_gcc_out = """
main.c:10:5: error: ‘x’ undeclared (first use in this function)
main.c:12:12: warning: implicit declaration of function ‘foo’
"""
    print("--- GCC Parse Test ---")
    print(json.dumps(normalizer.normalize(mock_gcc_out, 'c'), indent=2))
    
    mock_py_out = """
Traceback (most recent call last):
  File "script.py", line 5, in <module>
    print(1 / 0)
ZeroDivisionError: division by zero
"""
    print("\n--- Python Parse Test ---")
    print(json.dumps(normalizer.normalize(mock_py_out, 'python'), indent=2))
