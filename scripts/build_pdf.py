#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 .tex 编译成 PDF（xelatex，两遍），失败时返回可读的错误摘要。

用法:
    python build_pdf.py note.tex            # 输出同目录同名 pdf
    python build_pdf.py note.tex --out out.pdf
    python build_pdf.py note.tex --passes 3

成功: stdout 一行 JSON {"ok": true, "pdf": ...}
失败: stdout JSON {"ok": false, "errors": [...], "log_tail": "..."}，退出码 1
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

CANDIDATES = [
    "xelatex",
    r"D:\TinyTeX\bin\windows\xelatex.exe",
    r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe",
    r"C:\texlive\2024\bin\windows\xelatex.exe",
]


def find_xelatex():
    for c in CANDIDATES:
        if os.path.sep in c or "/" in c:
            if os.path.isfile(c):
                return c
        else:
            w = shutil.which(c)
            if w:
                return w
    return None


def extract_errors(log_text):
    errs = []
    lines = log_text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!") or "Undefined control sequence" in line \
                or "Missing $ inserted" in line or "Runaway argument" in line:
            ctx = "\n".join(lines[i:i + 6])
            errs.append(ctx.strip())
        if len(errs) >= 6:
            break
    if not errs:
        # 常见隐性错误
        for kw in ("File ended while scanning", "Emergency stop", "TeX capacity exceeded"):
            if kw in log_text:
                idx = log_text.find(kw)
                errs.append(log_text[max(0, idx - 200): idx + 200])
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tex")
    ap.add_argument("--out", default="")
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--keep-aux", action="store_true")
    args = ap.parse_args()

    tex = os.path.abspath(args.tex)
    if not os.path.isfile(tex):
        print(json.dumps({"ok": False, "errors": ["tex not found: %s" % tex]}, ensure_ascii=False))
        sys.exit(1)

    xe = find_xelatex()
    if not xe:
        print(json.dumps({"ok": False, "errors": [
            "未找到 xelatex。请安装 TinyTeX/TeXLive，或在 PATH 中提供 xelatex。"]},
            ensure_ascii=False))
        sys.exit(1)

    out_pdf = os.path.abspath(args.out) if args.out else os.path.splitext(tex)[0] + ".pdf"
    workdir = tempfile.mkdtemp(prefix="texbuild_")
    name = os.path.basename(tex)
    shutil.copy2(tex, os.path.join(workdir, name))

    # 复制同目录下被 \input / \includegraphics 引用的本地文件（保守：同目录所有文件）
    src_dir = os.path.dirname(tex)
    for f in os.listdir(src_dir):
        fp = os.path.join(src_dir, f)
        if os.path.isfile(fp) and not f.lower().endswith((".pdf", ".aux", ".log")):
            try:
                shutil.copy2(fp, os.path.join(workdir, f))
            except Exception:
                pass

    log_text = ""
    for n in range(args.passes):
        proc = subprocess.run(
            [xe, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", name],
            cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=300,
        )
        logpath = os.path.join(workdir, os.path.splitext(name)[0] + ".log")
        log_text = ""
        if os.path.isfile(logpath):
            with open(logpath, "r", encoding="utf-8", errors="replace") as f:
                log_text = f.read()
        if proc.returncode != 0:
            errs = extract_errors(log_text) or [
                proc.stdout.decode("utf-8", "replace")[-1500:]]
            # 提示常见病因
            hints = []
            if "fontset" in log_text or "Font" in log_text and "not found" in log_text:
                hints.append("字体问题：确认用 fontset=windows 或改用 fontset=fandol。")
            if "Missing $ inserted" in log_text:
                hints.append("正文里出现裸数学符号：下划线 _ ^ 需放进 $...$。")
            if "Undefined control sequence" in log_text:
                hints.append("宏包未加载或命令拼写错误。")
            print(json.dumps({"ok": False, "errors": errs, "hints": hints,
                              "log_tail": log_text[-2500:]}, ensure_ascii=False, indent=2))
            if not args.keep_aux:
                shutil.rmtree(workdir, ignore_errors=True)
            sys.exit(1)

    built = os.path.join(workdir, os.path.splitext(name)[0] + ".pdf")
    if not os.path.isfile(built):
        print(json.dumps({"ok": False, "errors": ["编译未报错但未生成 PDF"]}, ensure_ascii=False))
        sys.exit(1)

    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    shutil.copy2(built, out_pdf)

    pages = None
    try:
        with open(built, "rb") as f:
            head = f.read()
        pages = head.count(b"/Type /Page") or head.count(b"/Type/Page") or None
    except Exception:
        pass

    if not args.keep_aux:
        shutil.rmtree(workdir, ignore_errors=True)

    print(json.dumps({"ok": True, "pdf": out_pdf, "pages_estimate": pages,
                      "size_kb": round(os.path.getsize(out_pdf) / 1024, 1)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
