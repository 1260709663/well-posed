# Changelog

本文件的格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

对 skill 而言，破坏性变更指：**产出结构或标记体系改变**（下游若依赖 `\yi/\bz/\ts/\gap`
这类标记或固定文件名，需要跟着改）。

## [Unreleased]

### 计划中

- 模式 B 增加「对照版」版式：左栏原文页码、右栏笔记，便于打印后对照阅读
- `prep.py` 支持把整篇论文的定理陈述单独抽成清单（供模式 A 快速核对）
- 增加一个最小示例论文（自有版权）用于端到端测试，接通 CI 的 e2e 检查

## [1.2.1] - 2026-10-19

### 修复

- **安装命令有两条是错的**（1.2.0 里写的）：
  - `winget install --id=Distributions.TinyTeX` —— winget 里没有这个 ID
    （实测 `winget search` 查不到 TinyTeX 与 TeX Live）。改为已核实的
    `winget install --id MiKTeX.MiKTeX`，另附 TinyTeX 官方脚本。
  - `brew install tectonic` —— tectonic 不是 `xelatex`，而 `build_pdf.py` 调用的是
    `xelatex`，装了也跑不通。已删除该建议并在 README 里显式说明原因。
- **缺宏包时不给具体命令**。原先只说"可用 tlmgr install 补齐"，用户得自己查包名。
  现在按 `.sty → 包名` 映射生成可直接粘贴的命令，例如
  `tlmgr install ctex mathtools tcolorbox`；并注明 MiKTeX 会自动下载、无需手动补。
- `amsthm.sty` 的包名映射修正为 `amscls`（原来错误地映射到 `amsmath`，
  照抄那条命令并不能补上 amsthm）。

## [1.2.0] - 2026-10-19

### 新增

- **`scripts/doctor.py` 环境自检，以及三级降级链**。此前缺 LaTeX 或 Python 时只是"报错报得
  友好一点"，用户仍拿不到东西。现在先判档位再动手：

  | 档位 | 条件 | 产出 |
  |---|---|---|
  | `full` | Python + PyMuPDF + xelatex + 宏包齐全 | PDF |
  | `markdown-only` | 有 Python + PyMuPDF，无 LaTeX | Markdown（内容完整，仅无排版） |
  | `host-read-only` | 连 PyMuPDF 都没有 | Markdown（更保守，失去公式编码检测） |

  并规定了 `markdown-only` 的写法（`$$` 公式、语义盒降级为 `> **【补证】**` 这类文字标记、
  文件名改 `.md`），以及 `host-read-only` 下必须"默认按公式不可信处理"。

- `SKILL.md` 增加「第 0 步：环境自检」，并要求**动手前把档位告知用户**，不让用户等到最后
  才发现没有 PDF。
- 第 5 步补充唯一例外：若编译失败源于环境缺失（而非 .tex 写错），退回 Markdown 交付，
  但**正文一个字不许缩水**。

### 变更

- 步骤重新编号为 0–6（原 0–5）。
- README 的依赖章节改为三档表 + 各平台安装命令，并说明 Windows / Linux 的字体集差异。

## [1.1.1] - 2026-10-19

### 修复

- **`SKILL.md` 第 1 步写死了本机绝对路径**（`C:/Users/<用户名>/.workbuddy/binaries/python/versions/3.13.12/python.exe`
  与 skill 目录的绝对路径）。任何人克隆后照抄命令都会失败。现改为
  `PY=python` + `SK=<宿主告知的 skill 根目录>`，并给出多版本 Python 下的自检方法。
- `prep.py` 缺 PyMuPDF 时原先抛出裸 ImportError 栈；现给出可操作提示
  （装什么包、怎么换解释器）。

### 新增

- `validate_skill.py` 增加"写死的本机路径"检查：命中 `C:\Users\` 或 `/home/<name>/`
  这类路径直接判错。这类问题是跨机器失效的头号原因，必须在 CI 拦住。
- `SKILL.md` 环境依赖一节补充：Linux/macOS 上需把模板的 `fontset=windows`
  改为 `fontset=fandol`，否则因缺字体编译失败。

## [1.1.0] - 2026-10-19

### 变更

- **模式 C（导师提问）改为按论文节次组织**。原结构按 L1–L4 四个知识层次分章，读者无法与
  PDF 对照；现改为以论文自身的节号为骨架，每节 3–6 题，节内按
  「设定澄清 → 结论理解 → 技术机制 → 边界推广」递进，跨节问题统一收进「全局与推广」，
  薄弱环节诊断改为按节映射。
- 模式 C 题量上下限由 20–28 调整为 20–30。

### 新增

- 每节新增【本节考点】【读法提示】【本节小结】三个固定块，节标题必须带原文页码。
- 模式 C 规范新增「各节出题的侧重」对照表，规定不同类型章节该问什么、不该问什么。

## [1.0.0] - 2026-10-19

### 新增

- 三种模式：速览（A）、精读笔记（B）、导师提问（C），共用一套解析与排版管线。
- `scripts/prep.py`：PDF 体检（页数 / 书签 / 文本层质量 / 扫描件判定 / 双栏判定 /
  **数学符号编码损坏检测**）、按页范围抽文本、页面渲染。
- `scripts/build_pdf.py`：xelatex 两遍编译，失败时返回带 `hints` 的可读报错。
- `assets/template.tex`：ctexart 模板，四色语义盒（原文 / 补证 / 跳步 / 不确定性）。
- `references/`：三模式的输出规范，以及期刊分区与作者信息的检索规范。
- 标记体系：`[原文]` / `[补证]` / `[推测]` / `[gap]` / `[坑]`，用于区分作者的内容与补充的内容。
