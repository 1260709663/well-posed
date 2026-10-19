# 贡献指南

这个项目的核心是**规范文本**（`SKILL.md` 与 `references/*.md`），不是代码。
所以最有价值的贡献通常是：**指出某一处规范在真实论文上失效了**。

## 报告问题

优先开 issue，并在标题里带上模式：

- `[A] 速览把定理的条件写漏了`
- `[B] 补证在 XX 类型方程上给出错误结论`
- `[C] 某节的题目问的是复述题`

**最有用的报告长这样**：

> 论文：<标题>（arXiv 编号或 DOI）
> 模式：B
> 位置：笔记第 6 页，对应原文 p.12 的 Lemma 3.4
> 现象：补证写成了「由 Sobolev 嵌入直接得到」，但原文假设只有 $L^2$，嵌入用不了
> 期望：应当标 `[gap]` 并说明缺什么条件

带上一段**最小复现**（论文的哪一页、哪一句）比描述"效果不好"有用一百倍。

## 提交代码

```bash
git clone https://github.com/1260709663/well-posed.git
cd well-posed
make check          # 规范校验 + 语法检查 + 模板编译
```

没有 make 时（Windows 常见）：

```bash
python scripts/validate_skill.py .
python -m py_compile scripts/prep.py scripts/build_pdf.py scripts/validate_skill.py
python scripts/build_pdf.py assets/template.tex --out build/template.pdf
```

`make check` 必须全绿再提交 PR。CI 会在 Python 3.11 上重跑同样的检查，额外编译一次
模板（CI 用 `fontset=fandol` 替代 `fontset=windows`，因为 Linux 上没有 Windows 字体）。

## 改规范时的约定

1. **改 `references/` 前先想清楚代价**。这些文件本来就是为了让 agent 少犯错；
   新增一条规则，要能说清它防止的是哪一类具体错误。
2. **不要引入没有验证过的建议**。比如"用 XX 方法补证更简洁"——除非你实际补过一篇并编译通过。
3. **标记体系不许动**。`[原文]` / `[补证]` / `[推测]` / `[gap]` / `[坑]` 是可信度的基础，
   增删都属于破坏性变更，需要在 `CHANGELOG.md` 里写明。
4. **改 `assets/template.tex` 的导言区要谨慎**。新增宏包前先确认 TinyTeX 默认安装里有没有；
   没有的话要在 README 的依赖里写上。
5. 新增脚本请保持**零第三方依赖**（PyMuPDF 除外，它是 PDF 解析的硬需求）。

## 不要提交的内容

- **论文 PDF 及其读书笔记**。`*.pdf` 已在 `.gitignore` 里；笔记是对论文内容的再创作，
  不适合放进公开仓库。
- 期刊分区、影响因子的截图。这类数据有版本与版权问题，写进 issue 时给链接即可。

## PR 检查清单

- [ ] `make check` 通过
- [ ] 若改了规范，`CHANGELOG.md` 加了条目
- [ ] 若改了 `SKILL.md`，`metadata.version` 与顶层 `version` 同步
- [ ] 没有提交论文内容或第三方版权材料
- [ ] 破坏性变更已在 PR 描述里标出
