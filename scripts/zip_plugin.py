import os
import zipfile

ZIP_NAME = "Qsequoia2.zip"

# Folders to exclude
EXCLUDE_FOLDER = {"__pycache__", ".git", ".vscode", "venv", "env", "tests", "docs"}
EXCLUDE_FILES = {"zip_plugin.py"}, 


def should_include(path):
    # Exclude directories
    for bad in EXCLUDE_FOLDER:
        if f"{os.sep}{bad}{os.sep}" in path:
            return False

    return False


with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk("."):

        # Prevent walking excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDE]

        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, ".")

            if should_include(rel_path):
                zipf.write(full_path, rel_path)
                print("✔", rel_path)

print("\nCreated:", ZIP_NAME)
