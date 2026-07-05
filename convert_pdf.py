#!/usr/bin/env python3
"""Convert README.md and tutorial.md to PDF using pandoc + xelatex."""

import subprocess
import re
import os
import tempfile

REPO_DIR = "/Users/rise/WorkBuddy/2026-07-06-00-40-23/nk-ai-learning-guide"
OUTPUT_DIR = os.path.join(REPO_DIR, "pdf")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def preprocess_markdown(text):
    """Expand <details> tags so content is always visible in PDF."""
    text = re.sub(r'<details[^>]*>', '', text)
    text = text.replace('</details>', '')
    text = re.sub(r'<summary>(.*?)</summary>', r'**\1**\n', text)
    return text


def md_to_pdf(md_path, pdf_path, title):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    text = preprocess_markdown(text)

    # Write temp markdown
    tmp_md = os.path.join(tempfile.gettempdir(), os.path.basename(md_path))
    with open(tmp_md, 'w', encoding='utf-8') as f:
        f.write(text)

    cmd = [
        "pandoc",
        tmp_md,
        "-o", pdf_path,
        "--pdf-engine=xelatex",
        "-V", "mainfont=PingFang SC",
        "-V", "CJKmainfont=PingFang SC",
        "-V", "monofont=Menlo",
        "-V", "geometry:margin=2.5cm",
        "-V", "fontsize=12pt",
        "-V", "linestretch=1.4",
        "-V", "colorlinks=true",
        "-V", "linkcolor=blue",
        "-V", f"title={title}",
        "--highlight-style=tango",
        "--standalone",
        "-f", "markdown+raw_html+tex_math_dollars",
        "--resource-path", REPO_DIR,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_DIR)
    if result.returncode != 0:
        print(f"Error converting {md_path}:")
        print(result.stderr)
        return False
    print(f"Generated: {pdf_path}")
    return True


if __name__ == "__main__":
    ok1 = md_to_pdf(
        os.path.join(REPO_DIR, "README.md"),
        os.path.join(OUTPUT_DIR, "README.pdf"),
        "南开数统人 AI 学习指南",
    )
    ok2 = md_to_pdf(
        os.path.join(REPO_DIR, "tutorial.md"),
        os.path.join(OUTPUT_DIR, "tutorial.pdf"),
        "南开数统人 AI 学习教程",
    )
    if ok1 and ok2:
        print("All PDFs generated!")
    else:
        print("Some conversions failed.")
