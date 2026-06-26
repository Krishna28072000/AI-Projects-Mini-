import io
import re
import zipfile


def sanitize_skill_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")

    if not name:
        return "generated-skill"

    return name


def extract_skill_name(skill_md: str) -> str:
    lines = skill_md.strip().splitlines()

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("name:"):
            name = stripped.replace("name:", "", 1).strip()
            name = name.strip('"').strip("'")
            return sanitize_skill_name(name)

    return "generated-skill"


def is_safe_relative_path(path: str) -> bool:
    path = path.replace("\\", "/").strip()

    if not path:
        return False

    if path.startswith("/"):
        return False

    if ".." in path:
        return False

    allowed_prefixes = ("scripts/", "references/", "assets/")

    if not path.startswith(allowed_prefixes):
        return False

    return True


def create_skill_zip_bytes(platform: str, skill_name: str, skill_md: str, files: list) -> tuple[bytes, str]:
    skill_name = sanitize_skill_name(skill_name) or extract_skill_name(skill_md)
    zip_filename = f"{skill_name}-{platform}.zip"

    zip_buffer = io.BytesIO()

    included_paths = set()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        main_file_name = "SKILL.md"

        skill_md_path = f"{skill_name}/{main_file_name}"
        zip_file.writestr(skill_md_path, skill_md)
        included_paths.add(skill_md_path)

        has_scripts = False
        has_references = False
        has_assets = False

        for file in files:
            path = file.get("path", "").replace("\\", "/").strip()
            content = file.get("content", "")

            if not is_safe_relative_path(path):
                continue

            full_path = f"{skill_name}/{path}"

            if full_path in included_paths:
                continue

            zip_file.writestr(full_path, content)
            included_paths.add(full_path)

            if path.startswith("scripts/"):
                has_scripts = True

            if path.startswith("references/"):
                has_references = True

            if path.startswith("assets/"):
                has_assets = True

        if not has_scripts:
            zip_file.writestr(f"{skill_name}/scripts/.gitkeep", "")

        if not has_references:
            zip_file.writestr(f"{skill_name}/references/.gitkeep", "")

        if not has_assets:
            zip_file.writestr(f"{skill_name}/assets/.gitkeep", "")

    zip_buffer.seek(0)

    return zip_buffer.getvalue(), zip_filename