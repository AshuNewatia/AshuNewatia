import json
import re
import xml.etree.ElementTree as ET

from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent

DATA_FILE = ROOT / "data.json"
TEMPLATE_FILE = ROOT / "terminal.template.svg"
OUTPUT_FILE = ROOT / "terminal.svg"


def escape_svg_text(value):
    return escape(str(value), quote=True)


def validate_data(data):
    required_fields = [
        "name",
        "title",
        "bio",
        "roles",
        "tech_stack",
        "projects",
        "contact",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(data["roles"], list) or len(data["roles"]) != 3:
        raise ValueError("roles must contain exactly three entries.")

    if not isinstance(data["projects"], list) or len(data["projects"]) != 3:
        raise ValueError("projects must contain exactly three entries.")

    if not isinstance(data["tech_stack"], list) or not data["tech_stack"]:
        raise ValueError("tech_stack must be a non-empty list.")

    for index, project in enumerate(data["projects"], start=1):
        for field in ["name", "description", "highlight"]:
            if field not in project:
                raise ValueError(
                    f"Project {index} is missing required field: {field}"
                )


def split_tech_stack(tech_stack):
    midpoint = (len(tech_stack) + 1) // 2

    first_half = tech_stack[:midpoint]
    second_half = tech_stack[midpoint:]

    first_line = "  /  ".join(str(item) for item in first_half)
    second_line = "  /  ".join(str(item) for item in second_half)

    return first_line, second_line


def build_replacements(data):
    stack_1, stack_2 = split_tech_stack(data["tech_stack"])

    replacements = {
        "NAME": data["name"],
        "TITLE": data["title"],
        "BIO": data["bio"],
        "ROLE_1": data["roles"][0],
        "ROLE_2": data["roles"][1],
        "ROLE_3": data["roles"][2],
        "TECH_STACK_1": stack_1,
        "TECH_STACK_2": stack_2,
        "CONTACT": data["contact"],
    }

    for index, project in enumerate(data["projects"], start=1):
        replacements[f"PROJECT_{index}_NAME"] = project["name"]
        replacements[f"PROJECT_{index}_DESCRIPTION"] = project["description"]
        replacements[f"PROJECT_{index}_HIGHLIGHT"] = project["highlight"]

    return replacements


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Could not find {DATA_FILE.name}")

    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"Could not find {TEMPLATE_FILE.name}")

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    validate_data(data)

    template = TEMPLATE_FILE.read_text(encoding="utf-8")

    replacements = build_replacements(data)

    output = template

    for key, value in replacements.items():
        placeholder = "{{" + key + "}}"

        output = output.replace(
            placeholder,
            escape_svg_text(value),
        )

    remaining = re.findall(r"{{\s*[A-Z0-9_]+\s*}}", output)

    if remaining:
        raise ValueError(
            "Unreplaced placeholders found: "
            + ", ".join(sorted(set(remaining)))
        )

    # Validate the generated document before writing it.
    ET.fromstring(output)

    OUTPUT_FILE.write_text(output, encoding="utf-8")

    print(f"Successfully generated {OUTPUT_FILE.name}")


if __name__ == "__main__":
    main()