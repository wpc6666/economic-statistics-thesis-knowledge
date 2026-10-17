# 04 Stata / R 实操速查（从导数据到出结果）

## 一、为什么要学这个

前面 01-03 章教了你"选什么方法"，这一章教你"怎么用软件把方法跑出来"。

论文实证部分会用到的命令，按操作顺序排成一张清单。每条命令给一个可直接复制运行的最小例子，并注释输出怎么读。看不懂的参数先别管，先把能跑通的版本跑通，再回头调参。

---

## 二、Stata 部分

### 2.1 导数据：把外部数据搬进 Stata

Stata 自己的数据格式是 `.dta`，但我们拿到的往往是 Excel 或 CSV。

```stata
* === 1. 从 Excel 导入 ===
* firstrow：把第一行当变量名（而不是数据）
* clear：清掉当前内存里已有的数据
import excel "/Users/你的名字/data/宏观数据.xlsx", sheet(Sheet1) firstrow clear

* === 2. 直接打开 .dta 文件 ===
use "/Users/你的名字/data/样本.dta", clear

* === 3. 从 CSV 导入 ===
* delim(",") 指定分隔符是逗号；制表符分隔写 delim("\t")
insheet using "/Users/你的名字/data/样本.csv", delim(",") clear

* === 4. 导入后第一件事：看看长什么样 ===
* list 前5行，确认列名和数据类型对不对
list in 1/5

* === 5. 清洗完另存为 .dta，下次直接 use ===
* replace：文件已存在就覆盖
save "/Users/你的名字/data/清洗后.dta", replace
```

**输出怎么读**：`list in 1/5` 弹出一个表格，第一行是变量名。如果看到变量名是 `A B C` 而不是有意义的英文，说明 `firstrow` 没生效，回去检查 Excel 第一行是不是真的是表头。

---

### 2.2 [[05_数据清洗|数据清洗]]：drop / keep / rename / replace / gen / egen

拿到原始数据，第一步永远是清洗，不要急着跑回归。

```stata
* === 1. 删变量（删列） ===
drop 备注

* === 2. 删观测（删行）：用 if 条件 ===
* 删除年份小于2000的样本（早期数据质量差）
drop if 年份 < 2000

* === 3. 只想要的样本：keep ===
keep if 年份 >= 2010 & 年份 <= 2020

* === 4. 改变量名：rename 旧名 新名 ===
rename gdp gdp_total

* === 5. 生成新变量：gen ===
* 人均GDP = GDP总量 / 人口数
gen 人均gdp = gdp_total / pop

* === 6. 条件生成：replace ===
* 注意：缺失值不能随便填0，这里只是演示语法
replace 人均gdp = 0 if 人均gdp == .

* === 7. 分组汇总生成新变量：egen ===
* 按"省份"分组，算每个省的GDP均值
egen 省均gdp = mean(gdp), by(省份)

* === 8. 生成对数变量（回归里最常用） ===
* 取对数前必须确保 gdp 都是正数
gen ln_gdp = ln(gdp)

* === 9. 生成虚拟变量（0-1变量） ===
* 括号里条件成立=1，不成立=0
gen 东部 = (省份 == "北京" | 省份 == "上海" | 省份 == "广东")
```

**输出怎么读**：这些命令跑完只显示 `(X real changes made)` 或 `(X observations deleted)`。如果 X=0，说明条件没匹配上，回去检查变量名和条件。

---

### 2.3 描述统计：summarize / tabulate / correlation

写论文"描述性统计"那一节，就靠这三个命令。

```stata
* === 1. 全样本描述统计 ===
* 输出N、均值、标准差、最小值、最大值
summarize gdp pop 人均gdp ln_gdp

* === 2. 更详细的描述统计 ===
* 输出偏度、峰度、四分位数，检查分布
summarize gdp, detail

* === 3. 分类频数 ===
tabulate 省份

* === 4. 交叉列联表 ===
tab 地区 年份

* === 5. 相关系数矩阵 ===
* 回归前必跑：两个自变量相关系数>0.8要警惕多重共线性
correlate gdp pop 人均gdp ln_gdp
```

**输出怎么读**：
- Mean 列：看均值是不是离谱（人均GDP算出负数说明单位错了）；
- Std Dev 列：标准差远大于均值，说明数据很散，可能要取对数；
- [[01_相关系数|相关系数]]矩阵：对角线下是相关系数，**0.8 以上要警惕[[04_多重共线性|多重共线性]]**。

---

### 2.4 回归命令：最常用的五种

```stata
* === 1. 基准回归：OLS ===
regress gdp pop fdi 教育水平 基础设施

* === 2. 面板固定效应：xtreg ===
* 先声明面板结构
xtset 省份 年份
* 固定效应 fe：控制每个省份不随时间变的特征
xtreg gdp pop fdi, fe robust
* 随机效应 re
xtreg gdp pop fdi, re

* === 3. 工具变量回归：ivregress ===
* 语法：ivregress 2sls 因变量 (内生变量=工具变量) 控制变量
ivregress 2sls gdp (开放度=距离港口) pop 教育水平

* === 4. 二元选择模型：logit ===
* 因变量是0-1变量时用
logit 是否创新 研发投入 企业规模 年龄

* === 5. Probit 模型 ===
* 和 logit 结果方向几乎一样，选一个就行
probit 是否创新 研发投入 企业规模 年龄
```

**输出怎么读**：看 `P>|t|` 那一列，小于 0.05 就是显著。回归结果怎么读、怎么写进论文，详见../10_论文写作全流程/05_[[05_结果怎么读怎么写|结果怎么读怎么写]].md。

---

### 2.5 检验命令：回归完必做的体检

```stata
* === 1. 异方差检验：White ===
* 跑完 regress 之后马上跑
* 原假设：方差齐性；p<0.05 说明有异方差，要加 robust
estat imtest, white

* === 2. 自相关检验：DW ===
* 时间序列必跑；DW值接近2说明无自相关，<1或>3有问题
estat dwatson

* === 3. Hausman 检验：选 FE 还是 RE ===
* 必须先存 fe 和 re 两个模型
xtreg gdp pop fdi, fe
estimates store fe_model
xtreg gdp pop fdi, re
estimates store re_model
hausman fe_model re_model
* p<0.05 拒绝RE → 选FE；p>0.05 → 选RE

* === 4. ADF 单位根检验：时间序列平稳性 ===
* 原假设：有单位根（不平稳）
* p<0.05 → 平稳；p>0.05 → 不平稳要差分
dfuller gdp
```

**输出怎么读**：所有检验逻辑都一样——**p 值小于 0.05 就拒绝原假设**。先搞清楚原假设是什么，再看 p 值下结论，不要死记"显著就是好"。

---

### 2.6 稳健性与结果导出：winsor2 / outreg2 / esttab

```stata
* === 1. 缩尾处理：winsor2 ===
* 把极端值压缩到1%和99%分位数，防止超大值带偏结果
* 第一次用先装：ssc install winsor2, replace
winsor2 gdp, cuts(1 99) replace
* cuts(1 99)：小于1%分位和大于99%分位的值替换为分位数值

* === 2. 导出回归结果到 Word：outreg2 ===
* 第一次用先装：ssc install outreg2, replace
regress gdp pop fdi
outreg2 using "回归结果.doc", replace tstat

* 多列回归放一张表
regress gdp pop fdi
estimates store m1
regress gdp pop fdi 教育水平
estimates store m2
outreg2 [m1 m2] using "基准回归.doc", replace ctitle(模型1 模型2)

* === 3. 更美观的输出：esttab ===
* 第一次用先装：ssc install estout, replace
esttab m1 m2 using "回归结果.rtf", ///
    b(%9.3f) star(* 0.1 ** 0.05 *** 0.01) ///
    title("基准回归结果表") ///
    keep(pop fdi) ///
    addnote("注：括号内为t值；***、**、*分别表示1%、5%、10%水平显著。")
* b(%9.3f)：系数保留三位小数
* keep：只展示核心变量，控制变量不放进表里
```

---

### 2.7 画图：scatter / line / histogram

```stata
* === 1. 散点图：看两个变量关系 ===
scatter gdp fdi
* 加拟合线
twoway (scatter gdp fdi) (lfit gdp fdi)

* === 2. 折线图：时间趋势 ===
xtset 年份
line gdp 年份

* === 3. 直方图：看变量分布 ===
* normal：叠加正态分布曲线做对比
histogram gdp, normal

* === 4. 导出图片 ===
* width(1200)：论文里至少1200像素才清晰
graph export "散点图.png", replace width(1200)
```

---

### 2.8 抽样估计与置信区间（论文里最容易讲错的部分）

前面 2.1-2.7 教你怎么导数据、跑回归。但你写论文时一定会碰到这几个词：**抽样分布、标准误、中心极限定理、95%置信区间**。这节把它们一次讲透，并给出 Stata/R 代码。

> 📖 统计学原理：[[../../教材笔记/05_统计学原理/06_抽样与参数估计/00_章节总结|第6章 抽样与参数估计]]

#### 2.8.1 先分清四对概念（不然整篇论文都讲错）

打个比方：你想知道全校 8000 个学生的平均月生活费（这是**总体**，真值 μ），但你只抽了 200 人打电话问（这是**样本**，算出来的平均值是 x̄）。

| | 总体（你真正想知道的） | 样本（你实际查到的） |
|---|---|---|
| 单位数 | N（8000） | n（200） |
| 均值 | **μ**（希腊字母，未知常数） | **x̄**（拉丁字母，已知统计量） |
| 标准差 | **σ**（希腊字母） | **s**（拉丁字母） |
| 成数（比例） | **P**（大写） | **p**（小写） |

**口诀：总体用希腊字母，样本用拉丁字母。** 这是国际惯例，论文里写错会被导师挑。

- **参数**是总体那个你想知道但不知道的真数字（μ）——它是固定的常数。
- **统计量**是你从样本算出来猜参数的数字（x̄）——它是随机变量，换一个样本就算出不同的数。

**抽样调查的灵魂是"随机"**（[[../../教材笔记/05_统计学原理/06_抽样与参数估计/知识点/KP01_抽样调查与随机原则|随机原则]]）：从教务处拿到全校名单，用随机数表抽 200 人。如果你去食堂门口堵人，那叫"随意抽样"，不叫随机抽样——因为早八晚八没在食堂的人就漏了，抽样框从一开始就偏了。

#### 2.8.2 什么是抽样分布？（新手最容易懵）

你只抽了一个样本，算出一个 x̄=1500 元。但理论上你可以抽 1000 次样本，每次都算一个 x̄，把这 1000 个 x̄ 摆出来看它们怎么分布——这就是**抽样分布**。

三种分布别搞混：

| 分布 | 是什么 | 例子 |
|---|---|---|
| 总体分布 | 全部 8000 个学生的生活费分布 | 全校学生的直方图 |
| 样本分布 | 你抽的那 200 个人的生活费分布 | 你这 200 个人的直方图 |
| **抽样分布** | **所有可能样本的 x̄ 的分布** | "200人样本平均生活费"这个随机变量的分布 |

**关键结论**：抽样分布的均值 = μ（还是那个真值），抽样分布的方差 = σ²/n（不是 σ²！）。

#### 2.8.3 标准误 vs 标准差——新手最大混淆点

| | 标准差 σ | **标准误 σ/√n** |
|---|---|---|
| 衡量什么 | 单个学生生活费散多开 | 200人样本平均生活费散多开 |
| 和 n 的关系 | 与 n 无关 | n 越大越小 |
| 例子 | 学生生活费从 800 到 5000，σ=800 | 每次抽200人算平均，平均会在1500上下波动，标准误=800/√200≈57元 |

**一句话**：标准差说"一个人差异多大"，标准误说"平均多少个人的平均会差多远"。

**为什么除以 √n 还开根号？**——直觉：你抽 1 个人，生活费可能 800 也可能 5000；抽 200 个人平均，高的和低的互相抵消，平均值就稳多了。波动缩小的倍数是 √n——因为方差是"平方"的平均，再开根号还原。

**论文里写错就翻车**：写"样本均值 1500，标准差 57"——错！57 是**标准误**，不是标准差。标准差是 800。

#### 2.8.4 中心极限定理（CLT）——统计学的灵魂

> **不管原来的分布长什么样，只要样本量 n 够大（一般 n≥30），样本均值 x̄ 的分布就近似正态。**

人的生活费分布是极度右偏的（大部分人 1000-3000，少数富二代几万）——这跟正态八竿子打不着。但你抽 200 人算平均，x̄ 的分布就是正态的！

**为什么？** 一个学生的生活费 = 家庭背景 + 地区 + 专业 + 运气……一堆独立小因素叠加。抽 200 人平均，正负波动互相抵消，剩下的就是"真实均值"这个稳定信号，形状是对称的钟形。

**这就是为什么我们能对任意总体用 Z 检验、能写 95% 置信区间**——只要样本够大。

**注意**：n 大了变正态的是**样本均值的抽样分布**，不是总体本身。总体还是那个右偏的总体。

#### 2.8.5 点估计三标准：无偏、有效、一致

用 x̄ 猜 μ，不是随便一个数都能猜得好。好的估计量要满足三条：

| 标准 | 直觉 | 例子 |
|---|---|---|
| **无偏性** | 反复抽样，估计值平均等于真值 | E(x̄)=μ，不偏高也不偏低 |
| **有效性** | 同样无偏，方差小的更准 | 抽 30 人平均比抽 1 个人准（方差 σ²/30 < σ²） |
| **一致性** | 样本越大越准 | n→∞ 时 x̄→μ |

**冷知识**：样本方差为什么除以 n-1 而不是 n？——就是为了无偏。除以 n 会系统性偏小，除以 n-1 才能让 E(s²)=σ²。

#### 2.8.6 95% 置信区间到底什么意思？（90%的人讲错）

**错误理解（最常见）**："全市平均工资有 95% 的概率落在 [6200, 6800] 里。"

**为什么错？**——全市平均工资是个固定数字，它要么在区间里要么不在，不存在"概率"。就像你不能说"张三身高 175，他有 95% 概率是 175"——他就是 175。

**正确理解**："我用同样的方法抽 100 次样本，每次算一个区间，大约有 95 个区间会套住真均值 μ。这次算出来的 [6200, 6800] 就是这 100 个区间之一，我对它有 95% 的信心。"

**生活比喻（钓鱼）**：你撒网 100 次，95 次能捕到鱼。这次撒了一网，你说"我有 95% 信心网里有鱼"——鱼是不是真在网里不知道，但网的可靠度是 95%。

**置信区间公式**：
$$\bar{x} \pm z_{\alpha/2} \times \frac{s}{\sqrt{n}}$$

| 置信水平 | α | z 值 |
|---|---|---|
| 90% | 0.10 | 1.645 |
| 95% | 0.05 | **1.96** |
| 99% | 0.01 | 2.576 |

**注意**：置信水平越高区间越宽（要更保险就把网撒大）。99% 的区间比 95% 宽。

#### 2.8.7 样本量怎么算？（调查之前先算好）

调查之前要先想："我得抽多少人？"抽少了不准，抽多了浪费。从置信区间公式反推：

**估计均值时**：
$$n = \frac{z_{\alpha/2}^2 \sigma^2}{\Delta^2}$$

- z：95% 取 1.96
- σ：总体标准差（未知就用过去数据或预调查）
- Δ：你允许的最大误差（比如"平均工资误差不超过 200 元"）

**估计成数（比例）时**：
$$n = \frac{z_{\alpha/2}^2 p(1-p)}{\Delta^2}$$

**不知道 p 时最保险取 p=0.5**，因为 p(1-p)=0.25 最大，算出来的 n 最大最保险。

**关键直觉**：**误差要求缩一半，样本量要翻 4 倍！**（n 与 Δ² 成反比）所以问卷调查不是"越多越好"，要权衡成本。

**算出来的小数一律向上取整**（384.16 取 385，不是 384）——少一个都达不到精度。

#### 2.8.8 Stata 实操

```stata
* === 1. 单样本 t 检验 + 置信区间 ===
* 检验样本均值是否等于某个值（比如全校平均工资是否=6000）
* 命令：ttest 工资 = 6000
ttest wage = 6000
* 输出会给：样本均值、标准误、95%置信区间、t值、p值
* p>0.05 不能拒绝"均值=6000"的假设

* === 2. 双样本 t 检验（两组均值是否不同）===
* 比如男生平均工资 vs 女生平均工资
ttest wage, by(gender)

* === 3. 算置信区间 ===
* 用 ci 命令直接算均值的置信区间
ci means wage
* 95%置信区间 = [下限, 上限]
* 想看99%：ci means wage, level(99)

* === 4. 样本量计算（调查之前先算）===
* 估计均值：n = (z^2 * σ^2) / Δ^2
* 例：σ=2000，要求误差Δ=200，95%置信
* n = 1.96^2 * 2000^2 / 200^2 = 384.16 → 向上取整385
disp 1.96^2 * 2000^2 / 200^2
* 估计成数（不知道p取0.5）：n = 1.96^2 * 0.25 / 0.05^2 = 384.16 → 385
disp 1.96^2 * 0.25 / 0.05^2

* === 5. 标准误 vs 标准差（别搞混）===
sum wage
* Std Dev 列 = 标准差 σ
* 标准误 = Std Dev / √n，输出里不直接给
* 置信区间 = Mean ± 1.96 * (Std Dev / √N)
```

#### 2.8.9 R 实操

```r
# 目的：置信区间、t检验、样本量计算
# === 1. 单样本t检验 + 置信区间 ===
# 检验平均工资是否=6000元
t.test(data$wage, mu = 6000)
# 输出：样本均值、t值、p值、95%置信区间

# === 2. 双样本t检验（男vs女）===
t.test(wage ~ gender, data = data)

# === 3. 样本量计算函数 ===
# 估计均值：n = z^2 * sigma^2 / delta^2
n_mean <- function(sigma, delta, conf.level = 0.95) {
  z <- qnorm(1 - (1 - conf.level)/2)
  n <- z^2 * sigma^2 / delta^2
  return(ceiling(n))   # ceiling向上取整
}
n_mean(sigma = 2000, delta = 200)   # 输出385

# 估计成数：p未知取0.5最保险
n_prop <- function(p = 0.5, delta, conf.level = 0.95) {
  z <- qnorm(1 - (1 - conf.level)/2)
  n <- z^2 * p * (1-p) / delta^2
  return(ceiling(n))
}
n_prop(delta = 0.05)   # 输出385

# === 4. 中心极限定理可视化 ===
# 从右偏分布（指数分布）抽样，看样本均值的分布怎么变正态
set.seed(1)
pop <- rexp(100000, rate = 1/1000)   # 右偏的生活费分布
sample_means <- replicate(1000, mean(sample(pop, size = 30)))
hist(sample_means, breaks = 30, main = "n=30样本均值的抽样分布（近似正态）")
# 总体是右偏的，但样本均值的直方图是钟形的——这就是CLT
```

**输出怎么读**：
- `t.test` 的 `95 percent confidence interval` 就是置信区间；
- p 值 <0.05 说明"均值≠6000"；
- 样本量函数返回的是至少要抽多少个。

---

## 三、R 部分

R 的定位：Stata 能做的 R 基本都能做，做图更漂亮。经济统计学本科论文，R 主要用在多元统计分析（聚类、主成分、[[03_因子分析|因子分析]]）和时间序列这两块。下面代码假设已安装 R 和 RStudio，第一次用某个包要先 `install.packages("包名")`。

### 3.1 导数据

```r
# === 1. 读 CSV ===
# stringsAsFactors=FALSE：字符串列保持文本，不自动转因子
data <- read.csv("/Users/你的名字/data/样本.csv", stringsAsFactors=FALSE, fileEncoding="UTF-8")

# === 2. 读 Excel ===
# 需要先安装 readxl 包：install.packages("readxl")
library(readxl)
data <- read_excel("/Users/你的名字/data/宏观数据.xlsx", sheet="Sheet1")
data <- as.data.frame(data)

# === 3. 看数据结构 ===
str(data)        # 每一列是什么类型
head(data)       # 前6行
summary(data)    # 每列描述统计
```

---

### 3.2 描述统计

```r
# === 1. 基础描述统计 ===
summary(data)

# === 2. 更专业的描述统计 ===
# 第一次用先装：install.packages("psych")
library(psych)
describe(data[, c("gdp", "pop", "人均gdp")])
# 输出比 summary 多：标准差、偏度、峰度、标准误
```

---

### 3.3 时间序列分析

```r
# === 1. 转成时间序列格式 ===
# frequency=12 月度；年度写1；季度写4
gdp_ts <- ts(data$gdp, start=c(2000, 1), frequency=12)

# === 2. 画时序图 ===
plot(gdp_ts, main="GDP时间序列图", xlab="年份", ylab="GDP")

# === 3. 平稳性检验：adf.test ===
# 原假设：不平稳；p<0.05 → 平稳
library(tseries)
adf.test(gdp_ts)

# === 4. ARIMA 手动定阶 ===
# p=自回归阶数, d=差分次数, q=移动平均阶数
arima_model <- arima(gdp_ts, order=c(1, 1, 1))
print(arima_model)

# === 5. 自动定阶：auto.arima ===
# 不用自己猜 p d q，函数按AIC自动选最优
# 第一次用先装：install.packages("forecast")
library(forecast)
auto_model <- auto.arima(gdp_ts)
summary(auto_model)

# === 6. GARCH 波动率建模（金融数据常用） ===
# 第一次用先装：install.packages("fGarch")
library(fGarch)
garch_model <- garchFit(~ garch(1,1), data=returns, trace=FALSE)
summary(garch_model)
```

---

### 3.4 多元统计分析

```r
# 先标准化：每列减均值除以标准差，消除量纲影响
data_scaled <- scale(data[, c("gdp", "pop", "教育", "医疗")])

# === 1. 系统聚类：hclust() ===
dist_matrix <- dist(data_scaled, method="euclidean")  # 欧氏距离
hc <- hclust(dist_matrix, method="ward.D2")           # ward.D2最常用
plot(hc, labels=data$省份, main="系统聚类谱系图")      # 画树状图
cluster_result <- cutree(hc, k=3)                     # 切成3类

# === 2. K-Means 聚类 ===
# nstart=25：随机选25个初始中心取最优，避免初值敏感
km <- kmeans(data_scaled, centers=3, nstart=25)
km$size                          # 每类样本量
data$kmeans分类 <- km$cluster    # 分类结果加回原数据

# === 3. 主成分分析：princomp() ===
pca <- princomp(data_scaled, cor=TRUE)
summary(pca)                                # 方差解释比例
screeplot(pca, type="lines", main="碎石图")  # 碎石图判断保留几个
loadings(pca)                               # 主成分载荷

# === 4. 因子分析：factanal() ===
# factors=3提取3个因子；rotation="varimax"方差最大旋转
fa <- factanal(data_scaled, factors=3, rotation="varimax")
print(fa, digits=2)

# === 5. 线性判别分析：lda() ===
# 第一次用先装：install.packages("MASS")
library(MASS)
lda_model <- lda(类别 ~ gdp + pop + 教育, data=data)
predict(lda_model, newdata=data)

# === 6. 多维标度分析：cmdscale() ===
# 把高维距离关系投影到二维平面
mds <- cmdscale(dist_matrix, k=2)
plot(mds, type="n", main="多维标度图")
text(mds, labels=data$省份, cex=0.7)
```

---

### 3.5 回归分析

```r
# === 1. 线性回归：lm() ===
model <- lm(gdp ~ pop + fdi + 教育水平, data=data)
summary(model)

# === 2. 逻辑回归：glm ===
# family=binomial(link="logit") 就是 logit 模型
logit_model <- glm(是否创新 ~ 研发投入 + 企业规模 + 年龄,
                   family=binomial(link="logit"), data=data)
summary(logit_model)

# === 3. 面板回归：plm() ===
# 第一次用先装：install.packages("plm")
library(plm)
pdata <- pdata.frame(data, index=c("省份", "年份"))  # 声明面板结构
fe_model <- plm(gdp ~ pop + fdi, data=pdata, model="within")    # 固定效应
summary(fe_model)
re_model <- plm(gdp ~ pop + fdi, data=pdata, model="random")    # 随机效应
summary(re_model)
```

---

## 四、命令速查表

| 任务 | Stata 命令 | R 函数 |
|---|---|---|
| 导 Excel 数据 | `import excel` | `read_excel()` |
| 描述统计 | `summarize, detail` | `psych::describe()` |
| [[04_OLS截距和拟合值|OLS]] 回归 | `regress, robust` | `lm()` |
| 面板回归 | `xtreg, fe/re` | `plm(model="within/random")` |
| [[03_工具变量IV|工具变量]] | `ivregress 2sls` | `ivreg::ivreg()` |
| Logit | `logit` + `margins` | `glm(family=binomial)` |
| 时间序列 | `dfuller` + `arima` | `auto.arima()` |
| [[04_聚类分析|聚类分析]] | `cluster kmeans` | `hclust()` / `kmeans()` |
| 主成分 | `pca` | `princomp()` |
| 结果导出 | `outreg2` / `esttab` | `stargazer` 包 |

---

## 五、最后提醒

每跑完一步，把结果存下来（Stata 用 `save`，R 用 save.image 写 RData），不要从头到尾跑一遍才发现中间某步错了。命令里的注释就是你的实验记录，论文附录里可以附完整代码。

常用外部命令第一次用都要先装：
```stata
ssc install winsor2, replace    // 缩尾
ssc install outreg2, replace    // 导出结果
ssc install estout, replace    // esttab
ssc install reghdfe, replace   // 高维固定效应
ssc install ftools, replace    // reghdfe 依赖
```

---

上一篇：[[03_常见方法误用]]｜下一篇：[[05_SPSS操作指引]]


---

## 📖 配套教材笔记
- [[../../教材笔记/02_计量经济学/README|计量经济学总览]]
- [[../../教材笔记/02_计量经济学/09_工具变量法/00_章节总结|第9章 工具变量法]]
- [[../../教材笔记/02_计量经济学/11_面板数据/00_章节总结|第11章 面板数据]]
- [[../../教材笔记/02_计量经济学/10_二值选择模型/00_章节总结|第10章 二值选择模型]]
- [[../../教材笔记/05_统计学原理/06_抽样与参数估计/00_章节总结|统计学原理·第6章 抽样与参数估计]]（标准误、CLT、置信区间、样本量）

## 📚 配套原书
- [[../../原文件/计量经济学/陈强_计量经济学及Stata应用_全书|陈强《计量经济学及Stata应用》]]
- [[../../原文件/统计学原理/韩兆洲_统计学原理第7版_全书|韩兆洲《统计学原理（第7版）》]]
