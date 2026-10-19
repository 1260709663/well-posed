---
name: well-posed
display_name: Well-Posed（适定）
description: "Well-Posed｜数学 PDE 文献阅读器：输入一篇论文 PDF，输出排版好的中文 PDF（LaTeX 编译）。三种模式——速览（主要定理+论文骨架+方法+期刊水平+作者介绍）、精读笔记（补全跳过的证明步骤+核心参考文献）、导师提问（按论文章节逐节追问+参考答案）。Triggers on: 读这篇论文, 精读, 论文速览, 这篇 PDE 文章讲了什么, 帮我读文献, 生成精读笔记, 导师提问, paper brief, deep read, tutor questions, 期刊档次, 作者是谁. 仅限数学/PDE/分析类论文。"
description_zh: "PDE 论文三模式精读：速览 / 精读补证 / 导师提问，输出 LaTeX 排版 PDF"
category: 学术研究
tags: PDE,数学,文献阅读,精读,LaTeX,PDF
version: 1.0.0
homepage: https://github.com/
license: MIT
---

# Well-Posed（适定）

> 一个"适定"的读论文工具：读得准（定理逐条核对原文）、问得对（按节追问，读一节测一节）、不胡说（补证与推测分开标）。
>
> 名字取自 Hadamard 的适定性：**存在、唯一、稳定**——正好对应它的三种产出：速览给存在性判断，精读给唯一确定的证明链，提问给稳定的自测。

把一篇论文 PDF 变成**可读、可验、可自测**的中文 PDF 笔记。三种模式共用同一套解析与排版管线。

## 触发与模式判定

用户上传/给出论文 PDF 后，判断要哪种模式：

| 用户说法 | 模式 | 产出 |
|---|---|---|
| "速览/告诉我主要定理/这篇讲了什么/值不值得读" | **A 速览** | `01_brief.pdf`，4–7 页 |
| "精读/精读笔记/补全证明/详细读一遍" | **B 精读** | `02_deepread.pdf`，15–30 页 |
| "导师提问/考考我/出题/面试问题" | **C 提问** | `03_tutor.pdf`，20–30 题，按节分组 |
| "全流程/三份都要" | A → B → C | 三个 PDF |
| 没说清 | **先跑 A**，交付时问要不要 B/C | `01_brief.pdf` |

**不要反问"你要哪种模式"**——默认跑 A。A 本身就是"决定要不要深入"的工具。

---

## 工作流

### 第 0 步：定位与建目录

```
工作目录 = <PDF 所在目录>/<PDF 主名>_reader/
```

所有中间文件（页面图、抽取文本、.tex）放这里，最终 PDF 也放这里。
**保留 .tex**：用户可能要改。

### 第 1 步：体检

```bash
PY="C:/Users/王浩/.workbuddy/binaries/python/versions/3.13.12/python.exe"
SK="C:/Users/王浩/.workbuddy/skills/well-posed"

"$PY" "$SK/scripts/prep.py" info "<paper.pdf>"
```

读返回的 `advice` 字段，据此决定策略：

- `scanned_likely: true` → 无文本层，**所有页都要 render + 视觉读**，先告诉用户"这份是扫描件，会慢一些"。
- `two_column_likely: true` → 文本抽取会串行，**公式一律以渲染图为准**。
- `replacement_chars` 多 → 字体映射坏了，符号只能靠看图。
- **`math_text_suspect: true` → 最危险的情况**：文本层看着是正常英文，但数学符号编码是错的。典型症状：

  ```
  抽出来:  Btu “ ∆u`Bpu, uq
  实际是:  ∂_t u = Δu + B(u,u)
  ```

  这是老版 pdfTeX 把 TeX 字体槽位直接映射成 Unicode 导致的（`\partial`→`B`，`=`→`“`，`+`→`` ` ``，`(`→`p`，`)`→`q`）。
  **文字部分仍可放心用**（摘要、引言、证明的叙述性句子都是对的），但**任何公式、定理陈述、定理编号都必须以渲染图重读**。
  不要试图从这个文本层"猜"公式——会错，而且错得很隐蔽。

### 第 2 步：分块读取（关键，决定质量上限）

**先抽文本拿结构，再对关键页出图核对。** 两条腿走路：

`info` 返回的 `bookmarks` 字段若非空，**直接用它当论文骨架**（节号+页码+标题），比自己数节标题快且准；为空则从文本里找 `^\d+\.` 形式的节标题。

```bash
# 骨架：摘要 + 引言 + 定理陈述（通常前 6 页包含全部主结果）
"$PY" "$SK/scripts/prep.py" text "<paper.pdf>" --pages 1-6 --clean --out "<workdir>/t_1-6.txt"

# 后续按 10–14 页一块
"$PY" "$SK/scripts/prep.py" text "<paper.pdf>" --pages 7-20 --clean --out "<workdir>/t_7-20.txt"
```

**必须出图核对的页**（用 `render`，dpi ≥ 170，然后 Read 看 PNG）：

1. 所有**定理/引理/命题/推论**的陈述页。
2. 主证明中**核心估计**所在页（作者自己写"the key estimate"的地方）。
3. **参考文献列表**（核对引用编号，避免张冠李戴）。
4. 文本层出现明显乱码的页。

```bash
"$PY" "$SK/scripts/prep.py" render "<paper.pdf>" --pages 3-5 --dpi 180 --out "<workdir>/pages"
```

然后逐张 `Read` 这些 PNG。**不做这一步，定理里的指数和常数就会错**——这是本 skill 最容易失败的地方。

**长论文（> 40 页）**：先读 §1、定理陈述、§5 结论，判断哪些节是技术性的、可略读；不要平均用力。

**内部结构笔记**：每读完一块，在草稿里记 3–5 行（本节目标 / 用到的引理 / 跳步位置）。不交付，但保证跨块一致——否则写到第 20 页就忘了第 5 页的记号。

### 第 3 步：写正文（.tex）

```bash
cp "$SK/assets/template.tex" "<workdir>/01_brief.tex"
```

只改**填写区**（`\PaperTitle` 等 5 个宏）和正文，导言区别动。
内容规范看对应模式文件：

- **模式 A** → `references/mode-brief.md`
- **模式 B** → `references/mode-deep.md`
- **模式 C** → `references/mode-tutor.md`
- **期刊/作者检索**（A 必需，B/C 视需要）→ `references/sources.md`

写 .tex 时的硬要求：

- 正文里的 `_` `^` `%` `&` `#` 必须处理（数学放进 `$...$`；文本里用 `\_`）。
- 定理编号用 `\refo{(p.4, Theorem 1.2)}` 这种形式，让人能翻回原文。
- 补证一律用 `proofbox`，跳步用 `gapbox`，不确定用 `warnbox`，别混用。

### 第 4 步：编译

```bash
"$PY" "$SK/scripts/build_pdf.py" "<workdir>/01_brief.tex" --out "<workdir>/01_brief.pdf"
```

成功返回 `{"ok": true, "pdf": ...}`。
失败返回 `errors` + `log_tail`：按报错行号改 .tex 再编，**不要降级成 Markdown**。
典型病因已在 `hints` 字段里给了（裸下划线、缺宏包、字体）。

### 第 5 步：交付

`present_files` 给出 PDF，然后 3–5 行说明：

- 一句话结论（这篇干了什么）；
- 我认为最值得注意的一点；
- 下一步建议（要不要 B/C）。

**不要在聊天里复述整个 PDF 的内容**——用户点开就能看。

---

## 质量红线（违反即失败）

1. **定理陈述必须完整**：假设、结论、指标范围、常数依赖，一个不能少。写"证明了存在性"等于没写。
2. **编号必须来自原文**。不确定标 `[?]`，不许自创 "Theorem 2.1"。
3. **补证不许偷换假设**。必须加条件时，写明"需额外假设 X（原文未给）"并标 `\ts`。
4. **期刊分区/IF、作者职称**：查不到就写"未检索到"。编一个数字是最严重的错误。
5. **不确定的常数不写具体值**，用 $C=C(d,\Omega)$ 这种依赖形式。
6. **区分层次**：`\yi` 原文 / `\bz` 补证 / `\ts` 推断 / `\gap` 补不出 / `\kk` 隐患，不许混同。
7. 发现原文疑似错误要写出来并定位到"p.X, 式 (Y)",并判断是笔误还是实质问题。

---

## 环境依赖

- Python：`C:/Users/王浩/.workbuddy/binaries/python/versions/3.13.12/python.exe`（已装 PyMuPDF）
- LaTeX：TinyTeX，`xelatex` + `ctex` + `tcolorbox`（已验证可用）
- 若 xelatex 不在 PATH，`build_pdf.py` 会自动找 `D:\TinyTeX\bin\windows\xelatex.exe`

## 脚本速查

| 命令 | 用途 |
|---|---|
| `prep.py info <pdf>` | 页数、元数据、书签、文本层质量、扫描件/双栏判断 |
| `prep.py text <pdf> --pages 1-12 --clean --out f.txt` | 抽文本（带 `[p.N]` 标记） |
| `prep.py render <pdf> --pages 3-5 --dpi 180 --out dir` | 渲染 PNG 供视觉核对 |
| `build_pdf.py <tex> --out out.pdf` | xelatex 两遍编译，失败给可读报错 |

---

## 交付前自检

- [ ] 每条定理的编号、假设、指标都对着渲染图核过？
- [ ] 所有推导都标了 `\yi` / `\bz` / `\ts` / `\gap`？
- [ ] 期刊信息带来源和查询日期？作者信息区分了"自述"与"检索"？
- [ ] 目录、页码、页眉正常？中文没有乱码/缺字？
- [ ] .tex 保留在工作目录，用户可改？
