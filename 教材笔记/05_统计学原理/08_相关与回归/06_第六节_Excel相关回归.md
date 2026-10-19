# 第六节 Excel 相关与回归分析

<div style="text-align:right;margin:10px 0;"><a href="../../../exam.html" target="_blank" style="display:inline-block;padding:6px 16px;background:#2563eb;color:#fff;border-radius:6px;text-decoration:none;font-size:14px;">📝 开始做题</a></div>


> 所属：[[00_章节总结|第8章 相关与回归]]

本节是原书对 Excel 操作的总结性介绍，具体案例已在第二节（例 8-1）和第三节（例 8-4）中展示。

## 本节内容

### 一、Excel 能做什么

| 功能 | Excel 工具 |
|---|---|
| 相关系数 | `CORREL()` 函数 或 数据分析→相关系数 |
| 一元线性回归 | 数据分析→回归 |
| 多元线性回归 | 数据分析→回归（X 值区域选多列） |
| 散点图/拟合线 | 插入→散点图→添加趋势线 |

### 二、操作流程（一元回归）

1. **准备数据**：y 一列、x 一列（含表头）。
2. **加载宏**：如果"数据"选项卡没有"数据分析"，文件→选项→加载项→分析工具库。
3. **调回归对话框**：数据→数据分析→回归。
4. **填参数**：
   - Y 值输入区域：选 y 列（含表头）
   - X 值输入区域：选 x 列（含表头）
   - 勾选"标志"
   - 输出区域：选一个空白单元格
   - 可选：残差、残差图、线性拟合图、正态概率图
5. **读结果**：
   - `Multiple R`：复相关系数
   - `R Square`：$R^2$
   - `Adjusted R Square`：$\bar R^2$
   - `标准误差`：$s_y$
   - 方差分析表：F、Significance F（F 检验 p 值）
   - 系数表：Intercept、X Variable 的 Coefficients、标准误差、t Stat、P-value、95% 置信区间

### 三、多元回归（例 8-4 的 Excel 输出）

X 值区域选 x₁ 和 x₂ 两列即可。原书图 8-4 的关键结果：

| 项目 | 值 |
|---|---|
| Multiple R | 0.9985 |
| R Square | 0.9970 |
| Adjusted R Square | 0.9962 |
| 标准误差 | 2.75 |
| Intercept 系数 | -137.72 |
| x₁ 系数 | 0.2831 |
| x₂ 系数 | 1.7692 |
| F | 1310.03 |
| Significance F | 8.6e-11 |

Excel 与手算结果基本一致（微小差异来自四舍五入）。

### 四、Excel 的优势与局限

**优势**：操作简单、计算精确、自动给出检验和置信区间。

**局限**：
- 曲线回归、加权最小二乘、工具变量等高级功能不直接支持。
- 多重共线性、异方差检验需要自己算。
- 大样本（>10000 行）响应变慢。

**进阶工具**：SPSS、EViews、Stata、Python statsmodels、R。

## 本节与其他节/章的联系

- 本节是"落地工具"，前面五节讲的所有算法在 Excel 里都是点几下鼠标。
- 真正写论文、做大样本回归，要切换到专业统计软件（大牛库 04 会展开）。
