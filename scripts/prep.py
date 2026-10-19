#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PDF 预处理工具（well-posed skill 专用）。

子命令
------
info   : 输出页数、元数据、书签、文本层质量、是否扫描件、是否双栏
text   : 按页范围抽取文本（带页码标记，便于引用"原文 p.12"）
render : 把指定页渲染成 PNG（供多模态模型核对公式/定理编号）

设计原则：文本层便宜但对公式不可靠；凡涉及定理陈述、常数、指标，必须用
render 出图二次确认。
"""

import argparse
import json
import os
import re
import sys

try:
    import pymupdf as fitz
except ImportError:  # 旧版包名
    try:
        import fitz
    except ImportError:
        sys.exit(
            "缺少依赖 PyMuPDF，无法解析 PDF。\n"
            "  安装：%s -m pip install pymupdf\n"
            "  若本机有多个 Python，请用装了 PyMuPDF 的那个解释器运行本脚本\n"
            "  （先用 `python -c \"import pymupdf\"` 确认）。" % sys.executable
        )


def _open(path):
    if not os.path.isfile(path):
        sys.exit(json.dumps({"error": "file not found: %s" % path}, ensure_ascii=False))
    return fitz.open(path)


def _page_list(spec, npages):
    """解析 '1-5,8,10-' 形式的页范围（1-based，含端点）。"""
    if not spec:
        return list(range(1, npages + 1))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            a = int(a) if a.strip() else 1
            b = int(b) if b.strip() else npages
        else:
            a = b = int(part)
        a = max(1, a)
        b = min(npages, b)
        out.extend(range(a, b + 1))
    return sorted(set(out))


def _math_encoding_check(doc, npages):
    r"""检测文本层的数学符号编码是否损坏。

    老 pdfTeX 论文常把 TeX 字体槽位直接映射成 Unicode：
        \partial -> 'B', '=' -> '“', '+' -> '`', '(' -> 'p', ')' -> 'q'
    于是 "∂_t u = Δu + B(u,u)" 被抽成 "Btu “ ∆u`Bpu, uq"。
    这种文本拿去写笔记，公式会全错，必须改走渲染图。
    """
    sample = ""
    for i in range(min(npages, 8)):
        sample += doc[i].get_text("text")
    if not sample.strip():
        return {"suspect": False, "reason": "no_text"}

    weird = sum(sample.count(c) for c in "“”˜˚˘`´")
    # p...q 当作括号的形态
    paren_bug = len(re.findall(r"\bp[A-Za-z][^pq]{0,12}q\b", sample))
    # 正常 LaTeX 论文里这些字符极少出现，出现密度高就是编码坏了
    density = weird / max(len(sample), 1) * 1000
    suspect = (density > 3.0 and paren_bug > 3) or paren_bug > 15
    return {
        "suspect": bool(suspect),
        "weird_chars": weird,
        "weird_density_per_1k": round(density, 2),
        "paren_ligature_hits": paren_bug,
        "sample": sample[:260].replace("\n", " "),
    }


def cmd_info(args):
    doc = _open(args.pdf)
    npages = doc.page_count
    per_page = []
    total = 0
    replacement = 0
    for i in range(npages):
        page = doc[i]
        txt = page.get_text("text")
        n = len(txt.strip())
        rep = txt.count("\ufffd")
        total += n
        replacement += rep
        per_page.append({"p": i + 1, "chars": n, "images": len(page.get_images(full=True))})

    thin = [x["p"] for x in per_page if x["chars"] < 200]
    scanned = len(thin) > max(3, npages * 0.5)

    # 版式启发式：看**页宽中线上有多少字**。
    # 双栏在中缝留白，中线附近的词很少；单栏的正文必然压在中线上。
    # 实测（4 篇样张）：双栏 0.13，单栏 0.18–0.24，故阈值取 0.16。
    # 注意：这只是启发式，两头都有误判可能，不要把布尔值当事实；
    # JSON 里同时给出原始比值 gutter_ratio，便于人自己判断。
    mid_words = 0
    all_words = 0
    for i in range(min(npages, 6)):
        page = doc[i]
        w = page.rect.width or 1
        for wd in page.get_text("words"):
            all_words += 1
            c = (wd[0] + wd[2]) / 2 / w
            if 0.44 <= c <= 0.56:
                mid_words += 1
    gutter_ratio = round(mid_words / max(all_words, 1), 3)
    two_col = bool(all_words >= 150 and gutter_ratio < 0.16)

    toc = []
    try:
        toc = [{"level": lv, "title": t, "page": p} for lv, t, p in doc.get_toc()]
    except Exception:
        pass

    meta = {k: v for k, v in (doc.metadata or {}).items() if v}
    math_check = _math_encoding_check(doc, npages)

    result = {
        "file": os.path.abspath(args.pdf),
        "pages": npages,
        "page_size": [round(doc[0].rect.width), round(doc[0].rect.height)] if npages else [],
        "metadata": meta,
        "bookmarks": toc,
        "text_layer": {
            "total_chars": total,
            "avg_chars_per_page": round(total / npages, 1) if npages else 0,
            "replacement_chars": replacement,
            "low_text_pages": thin[:40],
            "scanned_likely": scanned,
        },
        "two_column_likely": two_col,
        "column_gutter_ratio": gutter_ratio,
        "math_text_suspect": math_check["suspect"],
        "math_check": math_check,
        "per_page": per_page,
        "advice": [],
    }
    if math_check["suspect"]:
        result["advice"].append(
            "数学符号编码损坏（TeX 字体槽位映射问题）：文本层里的公式不可信，"
            "所有公式、定理陈述必须 render 出图后视觉读取并重写为 LaTeX。")
    if scanned:
        result["advice"].append("疑似扫描件/无文本层：全部页面需 render 后视觉读取，耗时显著增加，先在回复中告知用户。")
    elif len(thin) > 3:
        result["advice"].append("部分页面文本稀少（可能含大图/公式页）：这些页需 render 视觉核对。")
    if replacement > 30:
        result["advice"].append("替换字符较多，字体映射异常：公式与符号务必以渲染图为准。")
    if two_col:
        result["advice"].append(
            "疑似双栏排版（中线词占比 %.2f，阈值 0.16）：文本抽取可能串行，"
            "公式与跨栏的定理陈述必须渲染核对。该判断是启发式，若肉眼是单栏可忽略。"
            % gutter_ratio)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    doc.close()


def _sanitize(txt):
    """去掉 PDF 里混入的控制字节（NUL、\\x01 等），否则下游会当成二进制文件。"""
    return "".join(ch for ch in txt
                   if ch == "\n" or ch == "\t" or ch >= " ")


def _clean(txt):
    # 合并软连字符换行；保留段落
    txt = re.sub(r"-\n(?=[a-z])", "", txt)
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    return txt


def cmd_text(args):
    doc = _open(args.pdf)
    pages = _page_list(args.pages, doc.page_count)
    chunks = []
    for p in pages:
        t = doc[p - 1].get_text("text")
        t = _sanitize(t)
        if args.clean:
            t = _clean(t)
        chunks.append("\n\n===== [p.%d] =====\n%s" % (p, t.rstrip()))
    body = "".join(chunks)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(body)
        print(json.dumps({"out": os.path.abspath(args.out), "pages": pages,
                          "chars": len(body)}, ensure_ascii=False))
    else:
        print(body)
    doc.close()


def cmd_render(args):
    doc = _open(args.pdf)
    pages = _page_list(args.pages, doc.page_count)
    outdir = args.out or os.path.join(os.path.dirname(os.path.abspath(args.pdf)), "_pages")
    os.makedirs(outdir, exist_ok=True)
    written = []
    for p in pages:
        page = doc[p - 1]
        pix = page.get_pixmap(dpi=args.dpi)
        fp = os.path.join(outdir, "p%03d.png" % p)
        pix.save(fp)
        written.append(fp)
    doc.close()
    print(json.dumps({"pages": pages, "files": written, "dpi": args.dpi,
                      "note": "用 Read 工具逐张查看这些 PNG，核对定理陈述与公式。"},
                     ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="PDF 预处理")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("info", help="元信息与文本层质量")
    p1.add_argument("pdf")
    p1.set_defaults(func=cmd_info)

    p2 = sub.add_parser("text", help="抽取文本")
    p2.add_argument("pdf")
    p2.add_argument("--pages", default="", help="如 1-12,15 （默认全部）")
    p2.add_argument("--out", default="", help="输出 txt 路径，省略则打印到 stdout")
    p2.add_argument("--clean", action="store_true", help="清理换行连字符")
    p2.set_defaults(func=cmd_text)

    p3 = sub.add_parser("render", help="渲染页面为 PNG")
    p3.add_argument("pdf")
    p3.add_argument("--pages", default="", help="如 3-6")
    p3.add_argument("--dpi", type=int, default=180)
    p3.add_argument("--out", default="")
    p3.set_defaults(func=cmd_render)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
