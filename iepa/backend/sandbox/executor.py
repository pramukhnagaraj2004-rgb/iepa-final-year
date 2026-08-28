import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

IS_RENDER = bool(os.environ.get("RENDER", False))

# Fed to any code that calls input() so it doesn't hang forever waiting
# on a stdin that will never actually be typed into. 30 lines of "1" is
# enough for typical intro-level scripts with a handful of input() calls.
DEFAULT_STDIN = "\n".join(["1"] * 30) + "\n"


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
                input=DEFAULT_STDIN,
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

            if IS_RENDER:
                return self._execute_subprocess(script_path, language)

            norm_mount_path = os.path.abspath(temp_dir).replace("\\", "/")

            docker_cmd = [
                "docker", "run", "--rm", "-i",
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
                input=DEFAULT_STDIN,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode

            if "docker: error during connect" in stderr or "open //./pipe/dockerDesktopLinuxEngine" in stderr or exit_code == 125:
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
            return self._execute_subprocess(script_path, language)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    executor = CodeExecutor(timeout=5)
    print("=== Testing CodeExecutor with resilient daemon fallback ===")
    print(f"IS_RENDER mode: {IS_RENDER}")

    code_index_error = "numbers = [10, 20, 30]\nprint(numbers[10])"
    res1 = executor.execute(code_index_error)
    print("Test 1 - IndexError caught:", "IndexError" in res1["error_raw"])
    assert "IndexError" in res1["error_raw"]

    code_clean = "print('Subprocess / Sandbox test passed!')"
    res2 = executor.execute(code_clean)
    print("Test 2 - Clean execution:", res2["success"])
    assert res2["success"] is True

    code_with_input = "x = input('enter: ')\nprint('got:', x)"
    res3 = executor.execute(code_with_input)
    print("Test 3 - input() no longer hangs:", res3["success"], res3["stdout"])
    assert res3["timed_out"] is False

    print("\n[+] CodeExecutor verified!")