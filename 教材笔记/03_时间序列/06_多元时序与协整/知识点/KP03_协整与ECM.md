# KP03 [[07_协整与误差修正ECM|协整与误差修正]]模型ECM

<div style="text-align:right;margin:10px 0;"><a href="../../../../exam.html" target="_blank" style="display:inline-block;padding:6px 16px;background:#2563eb;color:#fff;border-radius:6px;text-decoration:none;font-size:14px;">📝 开始做题</a></div>


## 1. 是什么

**协整**（cointegration）：两个或多个非平稳时间序列的某个线性组合是平稳的。虽然每个序列自身非平稳（随机游走），但它们之间存在长期均衡关系。

**误差修正模型**（Error Correction Model, ECM）：把短期波动和长期均衡结合起来的模型——短期偏离均衡时，会有一个"修正力"把它拉回长期均衡。

**直觉类比**：两个喝醉的人手拉手在广场上走。各自的步子随机歪歪扭扭（非平稳/随机游走），但手拉手让两人之间的距离保持稳定（线性组合平稳=协整）。ECM就是"如果走偏了，手会把你拉回来"的那个力。

**解决什么问题**：非平稳序列之间可能有长期经济关系（如收入和消费、价格和需求），协整理论告诉我们什么时候可以"合法地"回归非平稳序列。

## 2. 怎么用

### Engle-Granger两步法

**第一步：协整回归（长期均衡）**
$$y_t = \alpha + \beta x_t + \varepsilon_t$$
用[[KP02_OLS正交性|OLS]]估计$\hat{\alpha}, \hat{\beta}$，得到残差$\hat{\varepsilon}_t = y_t - \hat{\alpha} - \hat{\beta} x_t$

**第二步：检验残差[[02_平稳性|平稳性]]**
- 用[[KP02_DF与ADF检验|ADF]]检验$\hat{\varepsilon}_t$是否平稳
- 若$\hat{\varepsilon}_t$平稳 → $y_t$和$x_t$存在协整关系
- 若不平稳 → 没有协整关系，之前的回归是[[KP01_虚假回归|虚假回归]]

**第三步：建立ECM模型**
$$\Delta y_t = \beta \Delta x_t + \gamma \hat{\varepsilon}_{t-1} + u_t$$
其中$\hat{\varepsilon}_{t-1} = y_{t-1} - \hat{\alpha} - \hat{\beta} x_{t-1}$是误差修正项。

### 关键公式

**协整定义**：$y_t \sim I(1), x_t \sim I(1)$，若存在$\beta$使得$y_t - \beta x_t \sim I(0)$（平稳），则$y_t$和$x_t$协整。

**ECM模型**：
$$\Delta y_t = \beta_0 \Delta x_t + \gamma (y_{t-1} - \alpha - \beta x_{t-1}) + u_t$$

- $\gamma < 0$：负反馈——偏离均衡会自动回调
- $\gamma$绝对值越大：调整速度越快
- $\Delta y_t, \Delta x_t$：短期波动部分
- $y_{t-1} - \alpha - \beta x_{t-1}$：上期偏离长期均衡的程度

### R代码

```r
# ========== 协整与ECM完整流程 ==========
library(tseries)
library(forecast)

# 目的：检验收入和消费是否协整

# 模拟数据（协整的两个I(1)序列）
set.seed(123)
n <- 200
# 共同随机趋势
common <- cumsum(rnorm(n, 0, 0.5))
income <- 100 + common + rnorm(n, 0, 1)      # 收入=常数+共同趋势+噪声
consumption <- 50 + 0.7*common + rnorm(n, 0, 1)  # 消费=常数+0.7*共同趋势+噪声

# 第一步：ADF检验单整阶数
adf_income <- adf.test(income)    # 非平稳→I(1)
adf_consump <- adf.test(consumption)  # 非平稳→I(1)
cat("收入ADF p值:", adf_income$p.value, "\n")
cat("消费ADF p值:", adf_consump$p.value, "\n")

# 第二步：协整回归（Engle-Granger第一步）
coint_fit <- lm(consumption ~ income)
summary(coint_fit)
# 预期：income系数≈0.7，R²很高
resid_coint <- residuals(coint_fit)

# 第三步：检验协整残差是否平稳
adf_resid <- adf.test(resid_coint)
cat("协整残差ADF p值:", adf_resid$p.value, "\n")
# p<0.05→残差平稳→存在协整关系！

# 第四步：建立ECM模型
# ECM: Δconsumption = βΔincome + γ*误差修正项 + ε_t
delta_consump <- diff(consumption)
delta_income <- diff(income)
error_correction <- resid_coint[-n]  # 滞后一期残差

ecm_data <- data.frame(
  d_consump = delta_consump,
  d_income = delta_income,
  ec = error_correction
)
ecm_fit <- lm(d_consump ~ d_income + ec, data=ecm_data)
summary(ecm_fit)
# ec系数为负且显著→误差修正机制存在
# 含义：上期消费偏离均衡越多，本期回调力度越大
```

### 计算演示

**ECM计算示例**：
- 长期均衡关系：$消费_t = 50 + 0.7 \times 收入_t$
- 上期偏离均衡：$ec_{t-1} = 消费_{t-1} - (50 + 0.7 \times 收入_{t-1}) = 5$（消费偏高5个单位）
- ECM模型：$\Delta 消费_t = 0.5 \times \Delta 收入_t - 0.3 \times ec_{t-1}$
- 若本期收入不变（$\Delta 收入=0$）：
  $$\Delta 消费_t = 0 - 0.3 \times 5 = -1.5$$
- 含义：因为上期消费偏高5个单位，本期会自动减少1.5个单位，向均衡回调

## 3. 什么时候用

- **数据条件**：
  - 两个序列都是I(1)（同阶单整）
  - 经济理论暗示它们有长期均衡关系
- **典型场景**：
  - 收入与消费
  - 价格与成交量
  - 利率期限结构（长期利率和短期利率）
  - 购买力平价（两国物价与汇率）
- **前提假设**：
  - 两个序列同阶单整（通常都是I(1)）
  - 协整回归残差平稳

## 4. 什么时候不能用/易错点

- **不同阶单整**：一个I(0)一个I(1)，不能协整
- **协整残差不平稳**：说明没有长期均衡关系，之前的回归是虚假回归
- **ECM系数为正**：正反馈会发散，经济上不合理
- **常见错误**：
  - 不检验单整阶数就直接做协整回归
  - 混淆协整回归和普通回归——协整回归的t值不能用普通t分布判断

## 5. 与相似方法对比表

| 方法 | 序列要求 | 用途 | 结果解释 |
|------|----------|------|----------|
| 普通回归 | 平稳序列 | 短期因果关系 | 系数有直接经济含义 |
| 差分回归 | 差分后平稳 | 短期波动关系 | 只解释变化量，损失长期信息 |
| 协整回归 | 非平稳但协整 | 长期均衡关系 | 系数是长期均衡参数 |
| ECM模型 | 协整序列 | 短期+长期结合 | 短期波动+长期修正 |

## 6. 为什么用这个不用那个

- **为什么用协整而不用差分回归？** 差分回归只能研究"变化量之间的关系"，损失了长期水平关系的信息。协整+ECM同时捕捉长期均衡和短期调整。
- **为什么不能直接回归非平稳序列？** 如果没有协整关系，直接回归就是虚假回归。

## 7. 完整例子

**经典经济学例子**：消费函数
- 凯恩斯消费理论：消费和收入有长期均衡关系
- 两个序列都是I(1)（随GDP增长而增长）
- 协整回归：$消费_t = \alpha + \beta 收入_t + \varepsilon_t$
- 检验残差平稳→存在协整→长期消费倾向$\beta$是稳定的
- ECM模型：短期消费变化 = 短期收入变化 + 上期偏离均衡的修正
- 经济含义：消费短期可能偏离长期均衡，但会自动回调

## 答辩常问（带标准答案）

1. **问：什么是协整？它和虚假回归是什么关系？** 答：两个各自非平稳（都是 I(1)）的序列，如果存在一个线性组合 $y_t-\beta x_t$ 是平稳的（I(0)），就说它们协整。直观上：两条各自随机游走的曲线，虽然都不平稳，但它们之间的"距离"长期稳定，说明背后有一条共同的长期均衡关系。协整是"非平稳序列能不能合法回归"的分界线：如果两个 I(1) 序列协整，直接回归不是虚假回归，而是长期均衡关系的估计；如果不协整，直接回归就是上一节讲的虚假回归。
2. **问：用 Engle-Granger 两步法做协整检验的完整步骤是什么？** 答：第一步，先用 OLS 估计长期均衡回归 $y_t=\alpha+\beta x_t+\varepsilon_t$，得到残差 $\hat\varepsilon_t=y_t-\hat\alpha-\hat\beta x_t$；第二步，对这个残差序列做 ADF [[KP01_单位根检验ADF|单位根检验]]（注意用协整检验专用临界值，比普通 ADF 更严格）。若残差平稳（p<0.05），说明 $y_t$ 和 $x_t$ 协整；若残差非平稳，说明没有长期关系、之前的回归是虚假回归。前提是两个变量先都用 ADF 验过是同阶单整（通常都是 I(1)）。
3. **问：误差修正模型（ECM）里 $\gamma$ 系数为什么必须是负的？它的经济含义是什么？** 答：ECM 的形式是 $\Delta y_t=\beta\Delta x_t+\gamma\hat\varepsilon_{t-1}+u_t$，其中 $\hat\varepsilon_{t-1}=y_{t-1}-\hat\alpha-\hat\beta x_{t-1}$ 是上一期偏离长期均衡的程度。$\gamma$ 叫误差修正系数，必须为负：如果上期 $y$ 偏高（$\hat\varepsilon_{t-1}>0$），负的 $\gamma$ 就让本期 $\Delta y_t$ 为负、自动往下调，把偏离拉回均衡——这是负反馈。$|\gamma|$ 越大调整速度越快。如果 $\gamma>0$，偏离会被放大、系统发散，经济上不合理。ECM 的好处是同时刻画短期波动（$\Delta x_t$ 项）和长期均衡回调（误差修正项），弥补了纯差分回归丢失长期信息的缺点。

## 8. 速记卡

- 协整 = 两个非平稳序列的线性组合是平稳的
- Engle-Granger两步：先回归→再验残差平稳
- ECM = 短期波动 + 误差修正项（把偏离拉回均衡）
- $\gamma<0$ = 负反馈 = 自动回调
- 一句话口诀：**各自乱跑手拉手，协整就是绳不断**

---

## 🔗 相关知识点

**同章关联：**
[[KP02_DF与ADF检验|DF与ADF检验]]｜[[KP01_虚假回归|虚假回归（协整解决它）]]

**跨章/跨课关联：**
[[../../../02_计量经济学/13_单位根与协整/知识点/KP02_协整与ECM|计量视角·协整与ECM]]｜[[../../../02_计量经济学/12_平稳时间序列/知识点/KP01_VAR模型|计量视角·VAR与VECM]]

**🐮 大牛库深入：**
[[../../../../经济统计学论文从0基础到精通/09_时间序列/07_协整与误差修正ECM|大牛库·长期均衡+短期修正]]

**📖 原书原文：**
[[../../../../原文件/时间序列分析/王燕_时间序列分析基于R_全书|王燕教材·第6章 协整]]
