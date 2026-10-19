#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""校验 SKILL.md 是否符合 Agent Skills 规范，以及仓库内部引用是否完整。

不依赖第三方库（CI 上不需要 pip install）。逐条检查：

1. frontmatter 存在，且能被简单解析
2. name 必填、≤64、kebab-case、等于所在目录名
3. description 必填、≤1024
4. license 字段若给出，LICENSE 文件应存在
5. SKILL.md 正文里引用的相对路径（references/、scripts/、assets/）都存在
6. SKILL.md 行数建议 ≤500
7. 不许出现占位链接（如 https://github.com/ 结尾无仓库名）

用法:
    python scripts/validate_skill.py            # 校验当前仓库
    python scripts/validate_skill.py path/to/skill
退出码 0 = 通过，1 = 有错误（warnings 不影响退出码）。
"""

import os
import re
import sys

MAX_NAME = 64
MAX_DESC = 1024
MAX_LINES = 500

# 允许的规范字段 + 宿主扩展字段（WorkBuddy / Claude 等会读 display_name 之类）
SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
EXT_FIELDS = {"display_name", "display_name_en", "description_zh", "description_en",
              "category", "tags", "version", "homepage", "author"}


def parse_frontmatter(text):
    """返回 (顶层 dict, metadata dict, 正文字符串, 错误列表)。只支持本仓库用到的 YAML 子集。"""
    errs = []
    if not text.startswith("---"):
        return {}, {}, text, ["文件未以 '---' 开头，缺少 frontmatter"]
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not m:
        return {}, {}, text, ["frontmatter 未正确闭合（需要 --- ... ---）"]
    raw, body = m.group(1), m.group(2)

    top, meta = {}, {}
    in_meta = False
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indented = line[:1] in (" ", "\t")
        if in_meta and indented:
            mm = re.match(r"^\s+([\w-]+):\s*(.*)$", line)
            if mm:
                meta[mm.group(1)] = _strip_quotes(mm.group(2))
            continue
        in_meta = False
        mm = re.match(r"^([\w-]+):\s*(.*)$", line)
        if not mm:
            errs.append("无法解析的行：%r" % line)
            continue
        key, val = mm.group(1), mm.group(2)
        if key == "metadata" and not val.strip():
            in_meta = True
            continue
        if val.strip().startswith("["):
            top[key] = [x.strip() for x in val.strip("[]").split(",") if x.strip()]
        else:
            top[key] = _strip_quotes(val)
    return top, meta, body, errs


def _strip_quotes(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def check(root):
    errors, warns = [], []
    skill = os.path.join(root, "SKILL.md")
    if not os.path.isfile(skill):
        return ["根目录缺少 SKILL.md"], warns

    text = open(skill, encoding="utf-8").read()
    top, meta, body, errs = parse_frontmatter(text)
    errors.extend(errs)

    # --- name ---
    name = top.get("name", "")
    if not name:
        errors.append("缺少必填字段 name")
    else:
        if len(name) > MAX_NAME:
            errors.append("name 超过 %d 字符：%d" % (MAX_NAME, len(name)))
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            errors.append("name 必须是 kebab-case（小写字母/数字/连字符，且不含连续连字符）：%r" % name)
        dirname = os.path.basename(os.path.abspath(root))
        if name != dirname:
            warns.append("name(%r) 与目录名(%r) 不一致；规范要求二者相同（克隆时目录名即仓库名）"
                         % (name, dirname))

    # --- description ---
    desc = top.get("description", "")
    if not desc:
        errors.append("缺少必填字段 description")
    elif len(desc) > MAX_DESC:
        errors.append("description 超过 %d 字符：%d" % (MAX_DESC, len(desc)))

    # --- license ---
    lic = top.get("license", "") or meta.get("license", "")
    if lic and not any(os.path.isfile(os.path.join(root, f))
                       for f in ("LICENSE", "LICENSE.md", "LICENSE.txt")):
        warns.append("声明了 license=%r 但根目录没有 LICENSE 文件" % lic)

    # --- 占位链接 ---
    for m in re.finditer(r"https?://github\.com/?(\s|$|\"|\))", text):
        errors.append("发现占位链接 https://github.com/（缺少仓库名）")

    # --- 写死的本机路径（跨机器必失效） ---
    abs_patterns = [
        (r"[A-Za-z]:[\\/]Users[\\/]", "Windows 用户目录"),
        (r"(?<![\w.:/])/(?:home|Users)/[A-Za-z_]", "Unix 用户目录"),
    ]
    for pat, label in abs_patterns:
        for m in re.finditer(pat, body):
            snippet = body[max(0, m.start() - 20):m.end() + 40].replace("\n", " ")
            errors.append("SKILL.md 里有写死的%s路径（换机器即失效）：…%s…" % (label, snippet.strip()))
            break  # 每种模式只报一次，避免刷屏

    # --- 字段名 ---
    for k in top:
        if k not in SPEC_FIELDS and k not in EXT_FIELDS:
            warns.append("未知 frontmatter 字段 %r（既不在规范内，也不是已知的宿主扩展）" % k)

    # --- 内部引用 ---
    for m in re.finditer(r"(?:\(|`)((?:references|scripts|assets|docs)/[\w./-]+\.(?:md|py|tex|png|pdf))",
                         body):
        rel = m.group(1)
        if not os.path.exists(os.path.join(root, rel)):
            errors.append("SKILL.md 引用了不存在的文件：%s" % rel)

    # --- 篇幅 ---
    n = len(text.splitlines())
    if n > MAX_LINES:
        warns.append("SKILL.md 有 %d 行，建议压缩到 %d 行以内（规范建议 <5000 tokens）" % (n, MAX_LINES))

    # --- metadata 一致性 ---
    if meta.get("version") and top.get("version") and meta["version"] != top["version"]:
        errors.append("version 不一致：顶层 %s vs metadata %s" % (top["version"], meta["version"]))

    return errors, warns


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    errors, warns = check(root)
    print("校验目录：%s" % os.path.abspath(root))
    for w in warns:
        print("  [warn]  %s" % w)
    for e in errors:
        print("  [error] %s" % e)
    if errors:
        print("\n失败：%d 个错误，%d 个警告" % (len(errors), len(warns)))
        return 1
    print("\n通过：0 个错误，%d 个警告" % len(warns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
