# 期刊水平与作者信息：检索规范

## 为什么必须联网

分区、影响因子、作者任职都会变。模型记忆里的数字**必然**过时，写出来就是错的硬事实。
凡涉及这两类信息：**先检索，再落笔，并标来源与日期。**

---

## 一、期刊水平

### 检索流程

1. **确认正式出处**：从 PDF 首页 / 期刊官网 / Crossref（`doi.org/<DOI>`）拿到期刊全名、卷期、年份。
2. **查分区与因子**（用 WebSearch）：
   - `"<期刊全名>" 中科院分区`
   - `"<期刊全名>" JCR impact factor <最近年份>`
   - 英文期刊可加 `"<journal>" SJR quartile`
3. **判断预印本状态**：若首页只有 arXiv 编号，检索论文标题，看是否已在期刊见刊。已见刊则注明"arXiv:XXXX.XXXXX，后发表于 <期刊>"。
4. **领域口碑**：结合下表 + 检索到的信息，判断该刊在 PDE/分析圈的实际地位。

### 输出格式（三行，缺一不可）

```
中科院分区：<大类>/<小类>，<X> 区（<年份版>）　来源：<链接>　查询于 <日期>
JCR：IF = <数值>（<年份>），Q<x>　来源：<链接>　查询于 <日期>
领域定位：<一句话，如「PDE 领域公认的强刊，但低于 CPAM/ARMA 一档」>
```

**硬规则**：
- 查不到就写 **"未检索到"**。绝不用"通常在 2–3 区""影响因子大约 3"这类模糊说法凑数。
- 分区年份必须写（如"2025 年中科院版"），因为分区表每年调整。
- 中科院分区与 JCR 分区**经常不一致**，两个都要给，不要合并成一个结论。
- 若期刊不在 SCI 列表（如新刊、会议集），直接说明。

### 数学期刊分层参考（领域口碑，非权威分区）

**第一档（四大 + 顶级综合）**
Annals of Mathematics, Inventiones Mathematicae, Journal of the AMS, Acta Mathematica,
Publications Mathématiques de l'IHES, Duke Mathematical Journal, GAFA,
Cambridge Journal of Mathematics, Forum of Mathematics Pi

**第二档（分析/PDE 强刊）**
CPAM (Comm. Pure Appl. Math.), ARMA (Arch. Ration. Mech. Anal.),
JEMS, Annales de l'Institut Henri Poincaré (C) — Analyse Non Linéaire,
Annals of PDE, Analysis & PDE, Journal of Functional Analysis,
SIAM J. Math. Anal., Calc. Var. PDE, Comm. PDE,
Math. Annalen, IMRN, Advances in Mathematics, JMPA (J. Math. Pures Appl.)

**第三档（solid 专业刊）**
J. Differential Equations, Nonlinearity, Proc. AMS, Discrete Contin. Dyn. Syst.,
Asymptotic Analysis, ZAMP, J. Evol. Equ., Applied Math. Letters, JMAA, CPAA

**应用与计算**
SIAM J. Numer. Anal., Math. Comp., M3AS, SIAM J. Appl. Math., J. Comput. Phys.

**使用提醒**：中科院分区对数学刊普遍偏低（如 Annals of PDE 分区可能不如某些综合刊），
但圈内地位明显更高。**两者都给，让用户自己权衡**，不要只报分区了事。

---

## 二、作者信息

### 检索流程

1. **以论文首页为准**：affiliation（单位、院系）、邮箱域名——这是最可靠的一手信息。
2. 检索顺序：
   - `"<姓名>" "<单位>" PDE`（或具体方向，如 homogenization / fluid）
   - `"<姓名>" math google scholar`
   - arXiv 作者页（`arxiv.org/a/<name>_<initial>_1`）看全部预印本
   - 个人主页 / Math Genealogy（查师承，数学圈常用）
3. **防重名**：必须用"单位 + 研究方向"双重确认。看到同名且方向不符，直接排除。

### 输出格式

每位作者 3–4 行：

```
**张伟**（Wei Zhang）｜某大学数学系，教授
方向：流体力学方程、色散方程；代表作：<标题>（ARMA 2020）、<标题>（JFA 2022）
与本文关系：长期做 Navier–Stokes 的适定性，本文是其 2019 年结果的推广
来源：<单位主页/arXiv/Scholar>　查询于 <日期>
```

**硬规则**：
- 职称、职务若查不到，不猜。"教授/副教授"这类信息错得离谱会显得很不专业。
- 区分"论文中自述的信息"与"网络检索到的信息"，后者必须标来源。
- 通讯作者若可从 PDF 标注确认，明确写出。
- 作者人数 > 5 时，重点写前两位 + 通讯作者，其余一句带过（"其余合著者来自 XX 与 YY，方向为 …"）。

---

## 三、不确定性的呈现

用 `notebox` 或行内小字，明确区分三档：

- **已核实**：有来源链接，写"来源 + 日期"。
- **推测**：标 `\ts`，如"（推测：该作者近年转向随机 PDE，未见公开主页确认）"。
- **未检索到**：直接写这三个字，不修饰。

宁可显得信息少，不能显得信息假。
