import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

IS_RENDER = bool(os.environ.get("RENDER", False))

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
        
        for line in reversed(lines):
            if "Error:" in line:
                return line
        
        return lines[-1]

    def _execute_subprocess(self, script_path: str, language: str) -> Dict[str, Any]:
        """
        Fallback direct subprocess execution used on Render or when Docker is unavailable.
        """
        try:
            proc = subprocess.run(
                [sys.executable, script_path],
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

    def execute(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Executes code inside an isolated Docker container if available,
        or falls back to direct subprocess if Docker daemon is unreachable or on Render.
        """
        temp_dir = tempfile.mkdtemp(prefix="iepa_sandbox_")
        try:
            script_path = os.path.join(temp_dir, "submission.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            # If on Render, use direct subprocess
            if IS_RENDER:
                return self._execute_subprocess(script_path, language)

            # Normalize path for Docker volume mounting
            norm_mount_path = os.path.abspath(temp_dir).replace("\\", "/")

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

            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode

            # Check if Docker daemon failed
            if "docker: error during connect" in stderr or "open //./pipe/dockerDesktopLinuxEngine" in stderr or exit_code == 125:
                # Docker daemon not ready -> fallback to direct subprocess
                return self._execute_subprocess(script_path, language)

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
            # Fallback to subprocess if Docker failed to connect
            return self._execute_subprocess(script_path, language)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    executor = CodeExecutor(timeout=5)
    print("=== Testing CodeExecutor with resilient daemon fallback ===")
    print(f"IS_RENDER mode: {IS_RENDER}")

    # Test 1: IndexError
    code_index_error = "numbers = [10, 20, 30]\nprint(numbers[10])"
    res1 = executor.execute(code_index_error)
    print("Test 1 - IndexError caught:", "IndexError" in res1["error_raw"])
    print("Error raw:", res1["error_raw"])
    assert "IndexError" in res1["error_raw"]

    # Test 2: Clean code
    code_clean = "print('Subprocess / Sandbox test passed!')"
    res2 = executor.execute(code_clean)
    print("Test 2 - Clean execution:", res2["success"])
    assert res2["success"] is True

    print("\n[+] CodeExecutor verified!")
