# 第六节 Excel 抽样调查

<div style="text-align:right;margin:10px 0;"><a href="../../../exam.html" target="_blank" style="display:inline-block;padding:6px 16px;background:#2563eb;color:#fff;border-radius:6px;text-decoration:none;font-size:14px;">📝 开始做题</a></div>


> 所属：[[00_章节总结|第六章 抽样与参数估计]]

本节讲了哪几件事：
- 用 Excel 一次性算出样本均值、样本标准差、标准误、t 值、置信区间

## 本节内容

### 一、Excel 描述统计路径

数据输入一列 → 数据 → 数据分析 → 描述统计 → 勾选"平均数、标准差、标准误差、置信度"。

### 二、关键 Excel 函数

| 要算什么 | 函数 |
|---|---|
| 样本均值 | `=AVERAGE(A2:A29)` |
| 样本标准差（n-1） | `=STDEV(A2:A29)` |
| 标准误 | `=STDEV(...)/SQRT(n)` |
| t 临界值（双侧α） | `=TINV(α, n-1)` |
| Z 临界值 | `=NORM.S.INV(1-α/2)` |
| 置信区间上下限 | `=均值 ± t值*标准误` |

### 三、示例

原书例6-26：28 袋食品重量，用 Excel 算出：
- 均值 = 500.2143 克
- 标准差 = 2.3469 克
- 标准误 = 2.3469/√28 = 0.4435 克
- t(0.025, 27) = 2.0518
- 极限误差 = 2.0518 × 0.4435 = 0.91 克
- 95% 置信区间 = 500.21 ± 0.91，即 [499.30, 501.12] 克

---

## 本节与其他节/章的联系

本节是工具。手算一遍才能理解公式，Excel 只是重复劳动的自动化。第7章 Excel 假设检验用的是 `TDIST`、`T.TEST` 等函数。
