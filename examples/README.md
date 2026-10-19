# examples

## `toy-paper.pdf` 是什么

一篇 **3 页的虚构论文**，用来验证整条管线是否装对了。它不是真实发表的工作，
数学结论正确但极其初等，没有任何研究价值。

存在的理由：新用户刚 clone 下来，手边不一定有一篇想读的论文，但需要确认
"我这儿到底能不能跑通"。拿它跑一遍，30 秒就能知道答案。

## 怎么用

```bash
# 1. 先确认环境
python scripts/doctor.py

# 2. 拿它试跑体检
python scripts/prep.py info examples/toy-paper.pdf

# 3. 正常读它（模式 A 即可）
#    在对话里说："用 well-posed 速览 examples/toy-paper.pdf"
```

预期结果：`pages: 3`、`scanned_likely: false`、`math_text_suspect: false`、
`two_column_likely: false`。若与预期不符，说明环境或脚本有问题，先把这一关过了
再去读自己的论文。

## 为什么它长得像真的

这份样张刻意包含：摘要、两节正文、2 个定理、1 个引理、3 条参考文献、
一个**故意跳过的步骤**（§2 中 `|F| ≤ C₀E` 那句只写了"由 Cauchy–Schwarz 与
Poincaré 不等式可得"）。所以它也能用来试模式 B —— 看笔记会不会把这一步补出来，
以及补得对不对。

## 重新生成

```bash
python scripts/build_pdf.py examples/toy-paper.tex --out examples/toy-paper.pdf
```

改了 `toy-paper.tex` 记得重编，否则 PDF 与源码不一致。
