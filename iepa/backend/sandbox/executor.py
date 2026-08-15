import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

class CodeExecutor:
    def __init__(
        self,
        timeout: int = 10,
        memory: str = "128m",
        cpus: float = 0.5,
        pids_limit: int = 64,
        docker_image: str = "python:3.11-slim"
    ):
        self.timeout = timeout
        self.memory = memory
        self.cpus = cpus
        self.pids_limit = pids_limit
        self.docker_image = docker_image

    def _extract_error_raw(self, stderr: str) -> str:
        """
        Extracts the primary Python exception string from stderr.
        Finds the last non-empty line that contains 'Error:'.
        Falls back to the last non-empty line if no explicit 'Error:' line exists.
        """
        lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        if not lines:
            return ""
        
        # Look for the last line containing 'Error:'
        for line in reversed(lines):
            if "Error:" in line:
                return line
        
        # Fallback to the last line of stderr
        return lines[-1]

    def execute(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Executes code inside an isolated Docker container with CPU, memory, 
        and network restrictions.
        """
        temp_dir = tempfile.mkdtemp(prefix="iepa_sandbox_")
        try:
            # Write submission.py inside the temporary directory
            script_path = os.path.join(temp_dir, "submission.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Normalize path for Docker volume mounting (especially on Windows)
            norm_mount_path = os.path.abspath(temp_dir).replace("\\", "/")

            # Build Docker execution command with exact security flags
            docker_cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", self.memory,
                f"--cpus={self.cpus}",
                f"--pids-limit={self.pids_limit}",
                "-v", f"{norm_mount_path}:/code:ro",
                self.docker_image,
                "python", "/code/submission.py"
            ]

            # Execute subprocess with timeout
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode

            if exit_code == 0 and not stderr:
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": stderr,
                    "error_raw": "",
                    "exit_code": exit_code,
                    "timed_out": False,
                    "language": language
                }
            else:
                error_raw = self._extract_error_raw(stderr)
                is_success = (exit_code == 0 and not error_raw)
                return {
                    "success": is_success,
                    "stdout": stdout,
                    "stderr": stderr,
                    "error_raw": error_raw,
                    "exit_code": exit_code,
                    "timed_out": False,
                    "language": language
                }

        except subprocess.TimeoutExpired as e:
            timeout_msg = f"TimeoutError: code execution exceeded {self.timeout} seconds"
            return {
                "success": False,
                "stdout": e.stdout if e.stdout else "",
                "stderr": timeout_msg,
                "error_raw": timeout_msg,
                "exit_code": -1,
                "timed_out": True,
                "language": language
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "error_raw": f"ExecutionError: {str(e)}",
                "exit_code": -1,
                "timed_out": False,
                "language": language
            }
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    executor = CodeExecutor(timeout=5)
    print("=== Testing CodeExecutor in Isolation ===")

    # Test 1: IndexError
    print("\n--- Test 1: IndexError Submission ---")
    code_index_error = "numbers = [10, 20, 30]\nprint(numbers[10])"
    res1 = executor.execute(code_index_error)
    print("Success:", res1["success"])
    print("Exit code:", res1["exit_code"])
    print("Error raw:", res1["error_raw"])
    print("Timed out:", res1["timed_out"])
    assert "IndexError" in res1["error_raw"], f"Expected IndexError, got {res1['error_raw']}"

    # Test 2: Clean code
    print("\n--- Test 2: Clean Successful Execution ---")
    code_clean = "def greet(name):\n    return f'Hello, {name}!'\n\nprint(greet('Pramukh'))"
    res2 = executor.execute(code_clean)
    print("Success:", res2["success"])
    print("Stdout:", res2["stdout"].strip())
    print("Error raw:", res2["error_raw"])
    print("Timed out:", res2["timed_out"])
    assert res2["success"] is True
    assert res2["error_raw"] == ""
    assert "Hello, Pramukh!" in res2["stdout"]

    # Test 3: Infinite loop (Timeout)
    print("\n--- Test 3: Infinite Loop Timeout ---")
    code_timeout = "import time\nwhile True:\n    time.sleep(0.5)"
    res3 = executor.execute(code_timeout)
    print("Success:", res3["success"])
    print("Timed out:", res3["timed_out"])
    print("Error raw:", res3["error_raw"])
    assert res3["timed_out"] is True
    assert "TimeoutError" in res3["error_raw"]

    print("\n[+] All isolated CodeExecutor tests passed successfully!")
