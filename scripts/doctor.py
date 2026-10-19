#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""环境自检：判断本机能把 well-posed 跑到哪一档。

只用标准库，因此在"什么都没装"的机器上也能给出可读结论。

三档
----
full             Python + PyMuPDF + xelatex + 全部宏包都有 → 可产出 PDF
markdown-only    有 Python + PyMuPDF，但 LaTeX 不全 → 退化为 Markdown 笔记
host-read-only   连 PyMuPDF 都没有 → 脚本用不了，只能靠宿主自己读 PDF

用法:
    python scripts/doctor.py           # 人说人话
    python scripts/doctor.py --json    # 给 agent 解析
退出码: 0 = full，1 = markdown-only，2 = host-read-only
"""

import json
import os
import shutil
import subprocess
import sys

REQUIRED_PY = (3, 9)
REQUIRED_PKGS = ["ctex.sty", "tcolorbox.sty", "amsmath.sty", "amsthm.sty",
                 "booktabs.sty", "enumitem.sty", "fancyhdr.sty", "mathtools.sty"]
TEX_CANDIDATES = [
    r"D:\TinyTeX\bin\windows\xelatex.exe",
    r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe",
    r"C:\texlive\2024\bin\windows\xelatex.exe",
    "/usr/local/texlive/2024/bin/x86_64-linux/xelatex",
    "/Library/TeX/texbin/xelatex",
]
# .sty 文件名 → TeX Live / TinyTeX 的包名（用于生成 tlmgr 命令）
PKG_NAME = {
    "ctex.sty": "ctex", "tcolorbox.sty": "tcolorbox", "amsmath.sty": "amsmath",
    "amsthm.sty": "amscls", "booktabs.sty": "booktabs", "enumitem.sty": "enumitem",
    "fancyhdr.sty": "fancyhdr", "mathtools.sty": "mathtools",
}

INSTALL = {
    "python": [
        "Windows: winget install --id Python.Python.3.12",
        "macOS:   brew install python",
        "Ubuntu:  sudo apt install python3 python3-pip",
    ],
    "pymupdf": [
        "python -m pip install pymupdf",
    ],
    # 只列真正能装出 xelatex 的方式。注意：tectonic 虽然是 TeX 引擎，
    # 但本项目的 build_pdf.py 调用的是 xelatex，装了 tectonic 也跑不通。
    "latex": [
        "Windows: winget install --id MiKTeX.MiKTeX        (已验证该 ID 存在)",
        "Windows: 或用 TinyTeX 官方脚本 → irm https://yihui.org/tinytex/install-bin-windows.ps1 | iex",
        "macOS:   brew install --cask mactex-no-gui",
        "Ubuntu:  sudo apt install texlive-xetex texlive-lang-chinese texlive-latex-extra",
    ],
}


def check_python():
    v = sys.version_info
    ok = (v.major, v.minor) >= REQUIRED_PY
    return {"ok": ok, "version": "%d.%d.%d" % v[:3],
            "path": sys.executable,
            "note": "" if ok else "需要 Python >= %d.%d" % REQUIRED_PY}


def check_pymupdf():
    try:
        import pymupdf
        return {"ok": True, "module": "pymupdf", "version": getattr(pymupdf, "__version__", "?")}
    except ImportError:
        pass
    try:
        import fitz
        return {"ok": True, "module": "fitz", "version": getattr(fitz, "__version__", "?")}
    except ImportError:
        return {"ok": False, "module": None, "version": None}


def find_xelatex():
    p = shutil.which("xelatex")
    if p:
        return p
    for c in TEX_CANDIDATES:
        if os.path.isfile(c):
            return c
    return None


def check_latex():
    xe = find_xelatex()
    out = {"xelatex": xe, "packages": {}, "missing": []}
    if not xe:
        out["missing"] = REQUIRED_PKGS
        return out
    kpse = shutil.which("kpsewhich")
    if not kpse:
        cand = os.path.join(os.path.dirname(xe), "kpsewhich.exe")
        kpse = cand if os.path.isfile(cand) else None
    if not kpse:
        out["packages"] = {p: None for p in REQUIRED_PKGS}
        return out
    for pkg in REQUIRED_PKGS:
        try:
            r = subprocess.run([kpse, pkg], capture_output=True, timeout=20)
            out["packages"][pkg] = bool(r.stdout.strip())
            if not r.stdout.strip():
                out["missing"].append(pkg)
        except Exception:
            out["packages"][pkg] = None
    return out


def main():
    as_json = "--json" in sys.argv
    py = check_python()
    mu = check_pymupdf()
    tex = check_latex()

    if not mu["ok"]:
        level = "host-read-only"
    elif not tex["xelatex"] or tex["missing"]:
        level = "markdown-only"
    else:
        level = "full"

    advice, install = [], []
    if level == "host-read-only":
        advice.append("脚本无法解析 PDF：缺 PyMuPDF。仍可让宿主直接读取 PDF，"
                      "但会失去文本层质量检测（公式编码损坏、扫描件、双栏）这些判断。")
        advice.append("先解决 PyMuPDF；要产出 PDF 还需要装 LaTeX（见 README）。")
        if not py["ok"]:
            advice.append("Python 版本过低或不存在，连自检本身都不可靠。")
            install += INSTALL["python"]
        install += INSTALL["pymupdf"]
    elif level == "markdown-only":
        advice.append("LaTeX 不可用或宏包不全，无法编译 PDF。"
                      "降级为 Markdown 笔记：结构不变，公式用 $...$ / $$...$$，"
                      "语义盒改为文字标记，交付文件名用 .md。")
        if not tex["xelatex"]:
            advice.append("找不到 xelatex。")
            install += INSTALL["latex"]
        elif tex["missing"]:
            # 已装 TeX 但缺宏包：给可直接执行的补齐命令，别让用户自己查包名
            pkgs = sorted({PKG_NAME.get(m, m.replace(".sty", "")) for m in tex["missing"]})
            advice.append("已装 xelatex，但缺少宏包：%s" % ", ".join(tex["missing"]))
            install.append("tlmgr install %s        # TinyTeX / TeX Live 通用" % " ".join(pkgs))
            install.append("MiKTeX 用户可不手动补：编译时会自动下载缺失宏包")
    else:
        advice.append("环境完整，可产出 PDF。")

    result = {"level": level,
              "can_pdf": level == "full",
              "python": py, "pymupdf": mu, "latex": tex,
              "advice": advice, "install": install}

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        mark = lambda b: "OK  " if b else "MISS"
        print("[%s] Python        %s  (%s)" % (mark(py["ok"]), py["version"], py["path"]))
        print("[%s] PyMuPDF       %s" % (mark(mu["ok"]), mu["version"] if mu["ok"] else "未安装"))
        print("[%s] xelatex       %s" % (mark(bool(tex["xelatex"])), tex["xelatex"] or "未找到"))
        if tex["xelatex"]:
            miss = tex["missing"]
            print("[%s] LaTeX 宏包    %s" % (mark(not miss),
                                             "齐全" if not miss else "缺 " + ", ".join(miss)))
        print("\n可用级别：%s" % level)
        for a in advice:
            print("  - " + a)
        if install:
            print("\n需要安装：")
            for i in install:
                print("  " + i)

    return {"full": 0, "markdown-only": 1, "host-read-only": 2}[level]


if __name__ == "__main__":
    sys.exit(main())
