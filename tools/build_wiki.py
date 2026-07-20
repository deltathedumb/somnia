"""Build the Somnia GitHub Wiki from the canonical Markdown documentation.

The repository's ``docs/`` directory remains the source of truth for both the
MkDocs HTML site and GitHub Wiki. This tool rewrites local Markdown links to
GitHub Wiki page names and creates Home/_Sidebar navigation pages.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


PAGES = [
    ("index.md", "Home", "Home"),
    ("architecture.md", "Architecture", "Unified object model"),
    ("editor-model.md", "Editor-Data-Model", "Editor data model"),
    ("model-formats.md", "Model-Formats", "SEM and SEMJ"),
    ("native-libraries.md", "Native-Libraries", "Native libraries"),
    ("embedded-python.md", "Embedded-Python", "Embedded Python and PortaPy"),
    ("foundation-status.md", "Foundation-Status", "Foundation status"),
    ("roadmap.md", "Roadmap", "Roadmap"),
    ("testing.md", "Testing", "Testing"),
    ("contributing.md", "Contributing", "Contributing"),
    ("security.md", "Security", "Security"),
]


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)(#[^)]+)?\)")


def page_map() -> dict[str, str]:
    return {source: page for source, page, _ in PAGES}


def rewrite_links(text: str) -> str:
    pages = page_map()

    def replace(match: re.Match[str]) -> str:
        label = match.group(1)
        source = match.group(2)
        fragment = match.group(3) or ""
        target = pages.get(source)
        if target is None:
            return match.group(0)
        return f"[{label}]({target}{fragment})"

    return LINK_RE.sub(replace, text)


def build_sidebar() -> str:
    lines = ["## Somnia Engine", ""]
    for _, page, label in PAGES:
        lines.append(f"- [{label}]({page})")
    lines.extend(
        [
            "",
            "---",
            "",
            "- [Repository](https://github.com/deltathedumb/somnia)",
            "- [HTML documentation](https://github.com/deltathedumb/somnia/actions/workflows/docs.yml)",
            "",
        ]
    )
    return "\n".join(lines)


def build_footer() -> str:
    return (
        "Somnia Engine documentation is generated from the canonical "
        "[`docs/`](https://github.com/deltathedumb/somnia/tree/main/docs) sources.\n"
    )


def build_wiki(docs_dir: Path, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    for source_name, page_name, _ in PAGES:
        source_path = docs_dir / source_name
        if not source_path.is_file():
            raise FileNotFoundError(f"missing documentation source: {source_path}")
        text = source_path.read_text(encoding="utf-8")
        rewritten = rewrite_links(text)
        generated_notice = (
            "<!-- Generated from docs/"
            + source_name
            + "; edit the source file, not this wiki page. -->\n\n"
        )
        (output_dir / f"{page_name}.md").write_text(
            generated_notice + rewritten,
            encoding="utf-8",
        )

    (output_dir / "_Sidebar.md").write_text(build_sidebar(), encoding="utf-8")
    (output_dir / "_Footer.md").write_text(build_footer(), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument("--output", type=Path, default=Path(".wiki-build"))
    args = parser.parse_args()
    build_wiki(args.docs, args.output)
    print(f"Built {len(PAGES)} wiki pages in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
