#!/usr/bin/env python3
"""Convert README.md and tutorial.md to PDF using pandoc + xelatex.

Two-step process:
1. pandoc generates LaTeX from markdown
2. Post-process LaTeX to move figure captions above images
3. xelatex compiles to PDF
"""

import subprocess
import re
import os
import tempfile

REPO_DIR = "/Users/rise/WorkBuddy/2026-07-06-00-40-23/nk-ai-learning-guide"
OUTPUT_DIR = os.path.join(REPO_DIR, "pdf")
HEADER_TEX = os.path.join(REPO_DIR, "header.tex")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def preprocess_markdown(text):
    """Expand <details> tags and merge caption text into images for PDF."""
    # Expand <details> tags so content is always visible in PDF
    text = re.sub(r'<details[^>]*>', '', text)
    text = text.replace('</details>', '')
    text = re.sub(r'<summary>(.*?)</summary>', r'**\1**\n', text)

    # Merge attribution into roadmap image caption
    text = text.replace(
        '![南开数统人 AI 学习教程路线图](images/ai-learning-roadmap.png)\n*本图由 nanobanana2 制作*',
        '![南开数统人 AI 学习教程路线图（本图由 nanobanana2 制作）](images/ai-learning-roadmap.png)'
    )

    # Handle side-by-side images: split into two separate figures with captions
    side_by_side_old = (
        '这样你就在不会写一行前端代码的基础上，完成了自己的网页设计（还可以继续修改）：\n\n'
        '![alt text](images/task2_result1.png) ![alt text](images/task2_result2.png)'
    )
    side_by_side_new = (
        '![这样你就在不会写一行前端代码的基础上，完成了自己的网页设计（还可以继续修改）（一）](images/task2_result1.png)\n\n'
        '![这样你就在不会写一行前端代码的基础上，完成了自己的网页设计（还可以继续修改）（二）](images/task2_result2.png)'
    )
    text = text.replace(side_by_side_old, side_by_side_new)

    # Merge preceding text line into image alt text for proper figure captions
    # Pattern: "caption：\n\n![alt text](image.png)"  ->  "![caption](image.png)"
    single_re = re.compile(r'([^\n]+)：\n\n!\[alt text\]\(([^)]+)\)')

    def merge_caption(m):
        caption = m.group(1).rstrip('：')
        image = m.group(2)
        return f'![{caption}]({image})'

    text = single_re.sub(merge_caption, text)

    return text


def move_captions_above(latex):
    """Post-process LaTeX to move \\caption before \\includegraphics in figures."""
    # Pattern: \centering\n\pandocbounded{...}\n\caption{...}
    # Result:  \centering\n\caption{...}\n\pandocbounded{...}
    pattern = re.compile(
        r'(\\centering\n)(\\pandocbounded\{.*?\})(\n\\caption\{.*?\})',
        re.DOTALL
    )

    def rearrange(m):
        centering = m.group(1)
        image = m.group(2)
        caption = m.group(3).strip()
        return f'{centering}{caption}\n{image}'

    return pattern.sub(rearrange, latex)


def md_to_pdf(md_path, pdf_path, title):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    text = preprocess_markdown(text)

    # Write temp markdown
    tmp_md = os.path.join(tempfile.gettempdir(), os.path.basename(md_path))
    with open(tmp_md, 'w', encoding='utf-8') as f:
        f.write(text)

    # Step 1: Generate LaTeX with pandoc
    tmp_tex = os.path.join(tempfile.gettempdir(), os.path.basename(md_path).replace('.md', '.tex'))
    cmd_pandoc = [
        "pandoc",
        tmp_md,
        "-o", tmp_tex,
        "-t", "latex",
        "--standalone",
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
        "--include-in-header", HEADER_TEX,
        "-f", "markdown+raw_html+tex_math_dollars",
        "--resource-path", REPO_DIR,
    ]

    result = subprocess.run(cmd_pandoc, capture_output=True, text=True, cwd=REPO_DIR)
    if result.returncode != 0:
        print(f"Error generating LaTeX for {md_path}:")
        print(result.stderr)
        return False

    # Step 2: Post-process LaTeX to move captions above images
    with open(tmp_tex, 'r', encoding='utf-8') as f:
        latex = f.read()

    latex = move_captions_above(latex)

    with open(tmp_tex, 'w', encoding='utf-8') as f:
        f.write(latex)

    # Step 3: Compile with xelatex
    cmd_xelatex = [
        "xelatex",
        "-interaction=nonstopmode",
        "-output-directory", OUTPUT_DIR,
        tmp_tex,
    ]

    result = subprocess.run(cmd_xelatex, capture_output=True, text=True, cwd=REPO_DIR)
    if result.returncode != 0:
        print(f"Error compiling PDF for {md_path}:")
        print(result.stderr[-2000:])
        return False

    # Rename output to desired name
    default_pdf = os.path.join(OUTPUT_DIR, os.path.basename(tmp_tex).replace('.tex', '.pdf'))
    if default_pdf != pdf_path:
        os.rename(default_pdf, pdf_path)

    # Clean up aux files
    base_name = os.path.basename(tmp_tex).replace('.tex', '')
    for ext in ['.aux', '.log', '.out']:
        aux_file = os.path.join(OUTPUT_DIR, base_name + ext)
        if os.path.exists(aux_file):
            os.remove(aux_file)

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
