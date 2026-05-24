import os
import subprocess

from google.genai import types


schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python file relative to the working directory",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="Path to the Python file relative to the working directory",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Optional command line arguments",
            ),
        },
    ),
)


def run_python_file(
    working_directory: str,
    file_path: str,
    args: list[str] | None = None,
) -> str:
    try:
        working_dir_abs = os.path.abspath(working_directory)

        absolute_file_path = os.path.normpath(
            os.path.join(working_dir_abs, file_path)
        )

        valid_target_file = (
            os.path.commonpath([working_dir_abs, absolute_file_path])
            == working_dir_abs
        )

        if not valid_target_file:
            return (
                f'Error: Cannot execute "{file_path}" '
                "as it is outside the permitted working directory"
            )

        if not os.path.isfile(absolute_file_path):
            return f'Error: "{file_path}" does not exist or is not a regular file'

        if not file_path.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file'

        command = ["python", absolute_file_path]

        if args:
            command.extend(args)

        completed_process = subprocess.run(
            command,
            cwd=working_dir_abs,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = []

        if completed_process.returncode != 0:
            output.append(f"Process exited with code {completed_process.returncode}")

        if completed_process.stdout:
            output.append(f"STDOUT:\n{completed_process.stdout}")

        if completed_process.stderr:
            output.append(f"STDERR:\n{completed_process.stderr}")

        if not completed_process.stdout and not completed_process.stderr:
            output.append("No output produced")

        return "\n".join(output)

    except Exception as error:
        return f"Error: executing Python file: {error}"