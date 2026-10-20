#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量生成计量经济学 01-14 章思维导图 SVG"""
import sys
sys.path.insert(0, '/Users/wangpengcheng/IT/02_知识库/综合评价/tools')
from gen_svg import generate

BASE = '/Users/wangpengcheng/IT/02_知识库/综合评价/教材笔记/02_计量经济学'

CHAPTERS = [
    # 01 Stata入门
    {
        'dir': '01_Stata入门',
        'title': '第2章 Stata入门',
        'branches': [
            {'name': 'Stata基础与窗口', 'points': [
                '五大窗口:Results/Command/Review',
                '命令=空格分隔,区分大小写',
                'use file.dta, clear 打开数据',
                'clear 清空内存,无undo慎drop',
                'PgUp/PgDn 调历史命令',
            ]},
            {'name': '数据探索命令', 'points': [
                'describe/list 看数据结构',
                'summarize, detail 偏度峰度',
                'histogram s, freq 看分布',
                'scatter lnw s 看两变量关系',
                'pwcorr x y, sig star(.05) 相关',
            ]},
            {'name': '变量与日志管理', 'points': [
                'gen lns=log(s) 生成新变量',
                'gen col=(s>=16) 虚拟变量',
                'rename/replace 修改数据',
                'log using/close 记录输出',
                'ssc install 装外部命令',
            ]},
        ],
        'concept_chain': 'use载入 → describe/sum审视 → 画图看分布 → 相关分析 → 回归',
        'summary': '实证工具课:命令可复现,先描述统计再回归',
        'related': '第1章导论｜第3章数学回顾｜第4章一元回归',
    },
    # 02 数学回顾
    {
        'dir': '02_数学回顾',
        'title': '第3章 数学回顾',
        'branches': [
            {'name': '四大统计分布', 'points': [
                '正态 N(μ,σ²),钟形对称',
                'χ²(k)=k个独立Z²之和',
                't(k)=Z/√(χ²/k),厚尾',
                'F(k1,k2)=(χ²₁/k₁)/(χ²₂/k₂)',
                'k→∞时 t(k)→N(0,1)',
            ]},
            {'name': '数字特征与定律', 'points': [
                'Var(X)=E(X²)-[E(X)]²',
                'Cov(X,Y)=E(XY)-EX·EY',
                '迭代期望 E(Y)=E[E(Y|X)]',
                'MSE=Var(θ̂)+Bias²',
                '相关系数ρ=Cov/√(VarX·VarY)',
            ]},
            {'name': '无关性三层次', 'points': [
                '相互独立⇒均值独立⇒不相关',
                '均值独立 E(Y|x)=E(Y)',
                '不相关 Cov(X,Y)=0',
                'LLN: X̄ → E(X)',
                'CLT: √n(X̄-μ)/σ → N(0,1)',
            ]},
        ],
        'concept_chain': '正态Z → 平方得χ² → 除√χ²/k得t → 两χ²相比得F',
        'summary': 'OLS与假设检验的数学工具箱',
        'related': '第4章一元回归｜第6章大样本OLS｜第11章MLE',
    },
    # 03 一元线性回归
    {
        'dir': '03_一元线性回归',
        'title': '第4章 一元线性回归',
        'branches': [
            {'name': '模型与OLS推导', 'points': [
                'PRF: y=α+βx+ε',
                'β̂=Σ(x-x̄)(y-ȳ)/Σ(x-x̄)²',
                'α̂=ȳ-β̂x̄,过样本均值点',
                '最小化 Σeᵢ²',
                'eᵢ=yᵢ-ŷᵢ 残差',
            ]},
            {'name': '正交性与R²', 'points': [
                '一阶条件 Σeᵢ=0',
                'Σxᵢeᵢ=0 残差与X正交',
                'TSS=ESS+RSS 平方和分解',
                'R²=ESS/TSS=1-RSS/TSS',
                'R²=[Corr(y,ŷ)]²',
            ]},
            {'name': '四大基本假设', 'points': [
                '线性于参数(可对x非线性)',
                '随机抽样 iid',
                'x有变异 Σ(x-x̄)²≠0',
                'E(ε|x)=0 外生性命根子',
                '无常数项R²不可比',
            ]},
        ],
        'concept_chain': '最小化Σe² → 正规方程 → β̂ → 正交性 → TSS=ESS+RSS → R²',
        'summary': '全书理论核心:外生性假设E(ε|x)=0是命根子',
        'related': '第3章数学回顾｜第5章多元回归｜第6章大样本OLS',
    },
    # 04 多元线性回归
    {
        'dir': '04_多元线性回归',
        'title': '第5章 多元线性回归',
        'branches': [
            {'name': '矩阵形式OLS', 'points': [
                'y=Xβ+ε 矩阵形式',
                'β̂=(X\'X)⁻¹X\'y',
                '正规方程 X\'e=0',
                'Var(β̂|X)=σ²(X\'X)⁻¹',
                's²=SSR/(n-K) σ²无偏估计',
            ]},
            {'name': '古典五假定', 'points': [
                '线性于参数',
                '严格外生 E(ε|X)=0',
                'X满列秩,无严格共线',
                '球形扰动 Var=σ²I',
                'ε|X ~ N(0,σ²I)',
            ]},
            {'name': '统计推断', 'points': [
                't=(β̂ₖ-c)/SE ~ t(n-K)',
                'F=(SSR*-SSR)/m ÷ SSR/(n-K)',
                'F=R²/(K-1) ÷ (1-R²)/(n-K)',
                'Gauss-Markov: OLS=BLUE',
                '校正R̄²惩罚多余变量',
            ]},
        ],
        'concept_chain': 'X满秩+外生+球形扰动 → OLS=BLUE → t/F检验 → 预测',
        'summary': '偏回归系数=控制其他变量后的净效应',
        'related': '第4章一元回归｜第6章大样本OLS｜第7章异方差',
    },
    # 05 大样本OLS
    {
        'dir': '05_大样本OLS',
        'title': '第6章 大样本OLS',
        'branches': [
            {'name': '收敛与极限定理', 'points': [
                '依概率收敛 plim θ̂ₙ→θ',
                '均方收敛 E[(θ̂-θ)²]→0',
                'LLN: X̄ → E(X)',
                'CLT: √n(X̄-μ)/σ → N(0,1)',
                '分布收敛→已知分布',
            ]},
            {'name': '大样本性质', 'points': [
                '一致性 plim β̂=β 更基本',
                '渐近正态 √n(β̂-β)→N(0,σ²Q⁻¹)',
                '渐近有效',
                '条件:外生+X\'X/n渐近满秩',
                '无偏≠一致,有偏可渐近一致',
            ]},
            {'name': '大样本推断', 'points': [
                't=β̂/SE → N(0,1)',
                'F渐近 χ²/m',
                'CI: β̂±1.96·SE',
                '不要求扰动正态',
                'n>30即可用渐近结论',
            ]},
        ],
        'concept_chain': 'LLN+CLT → 一致性 → 渐近正态 → t≈N(0,1),F≈χ²/m',
        'summary': '放松正态假设:不要求扰动正态,只要样本够大',
        'related': '第5章小样本OLS｜第7章异方差稳健SE｜第9章IV',
    },
    # 06 异方差
    {
        'dir': '06_异方差',
        'title': '第7章 异方差',
        'branches': [
            {'name': '后果与检验', 'points': [
                'Var(εᵢ|X)=σᵢ² 方差随观测变',
                'OLS仍无偏,但SE有偏',
                't/F检验失真,OLS非BLUE',
                'BP检验: e²对X回归',
                'White检验: 加平方+交叉项',
            ]},
            {'name': '处理方法', 'points': [
                'White稳健SE(XX)⁻¹Σe²xx\'(XX)⁻¹',
                'reg y x, robust 首选',
                'WLS权重 wᵢ=1/σᵢ',
                'FWLS先估σᵢ²再加权',
                '只修SE,不动系数',
            ]},
            {'name': '决策流程', 'points': [
                '先跑BP/White检验',
                'p>0.05 同方差用OLS',
                'p<0.05 存在异方差',
                '不知σ²形式→robust',
                '知σ²∝某变量→WLS',
            ]},
        ],
        'concept_chain': 'BP/White检验 → 存在异方差 → OLS系数不动只修SE(robust)',
        'summary': '异方差不破坏一致性,只让标准误失真',
        'related': '第5章球形扰动｜第8章自相关｜第6章大样本OLS',
    },
    # 07 自相关
    {
        'dir': '07_自相关',
        'title': '第8章 自相关',
        'branches': [
            {'name': '模型与后果', 'points': [
                'AR(1): εₜ=ρεₜ₋₁+uₜ',
                'Cov(εₜ,εₜ₋ₛ)≠0',
                '时间序列有惯性',
                'OLS无偏但SE通常低估',
                't检验过度拒绝',
            ]},
            {'name': '检验方法', 'points': [
                'DW≈2(1-ρ̂), d≈2无自相关',
                'd<2正自相关,d>2负自相关',
                'BG检验 estat bgodfrey 高阶',
                'Q检验 Ljung-Box相关图',
                '含滞后因变量时DW失灵',
            ]},
            {'name': '处理方法', 'points': [
                'Newey-West HAC修两者',
                '滞后阶 L≈n^(1/4)',
                'newey y x, lag(L)',
                '准差分 yₜ-ρyₜ₋₁',
                'FGLS先估ρ再变换',
            ]},
        ],
        'concept_chain': 'DW/BG检验 → 存在自相关 → Newey-West HAC修标准误',
        'summary': '与异方差平行:只修标准误,不动系数',
        'related': '第7章异方差｜第13章平稳时间序列｜第6章大样本OLS',
    },
    # 08 模型设定与数据问题
    {
        'dir': '08_模型设定与数据问题',
        'title': '第9章 模型设定',
        'branches': [
            {'name': '变量选择问题', 'points': [
                '遗漏变量 β̂₂→β₂+β₃δ',
                'Cov(x2,x3)≠0则不一致',
                '无关变量:无偏但方差大',
                'VIF=1/(1-Rₖ²)>10',
                '极端值 leverage判断',
            ]},
            {'name': '函数形式问题', 'points': [
                'RESET: 加ŷ²,ŷ³联合显著',
                'estat ovtest 函数形式',
                '对数模型系数=弹性',
                '截距虚拟D平移δ',
                '交互项Dx改斜率γ',
            ]},
            {'name': '结构变动与数据', 'points': [
                'Chow F=(SSR*-SSR1-SSR2)/K',
                '等价联合F检验D和Dx',
                'winsorize 1%/99%去极值',
                'ipolate线性插值缺失值',
                '诊断顺序:符号→显著→影响→形式',
            ]},
        ],
        'concept_chain': '回归可疑 → 查符号(遗漏) → 查VIF(共线) → 查leverage(极值) → RESET(形式)',
        'summary': '遗漏变量和函数误设最严重:破坏一致性',
        'related': '第5章多元回归｜第7章异方差｜第9章工具变量IV',
    },
    # 09 工具变量法
    {
        'dir': '09_工具变量法',
        'title': '第10章 工具变量法',
        'branches': [
            {'name': '内生性与IV条件', 'points': [
                '三来源:遗漏/测量误差/双向因果',
                'IV两条件:相关性+外生性',
                '排他性:只通过x影响y',
                'β̂_IV=Σ(z-z̄)(y-ȳ)/Σ(z-z̄)(x-x̄)',
                '恰好识别时外生性无法统计检验',
            ]},
            {'name': '2SLS流程', 'points': [
                '第一阶段: x̂=π₀+π₁z+外生',
                '第二阶段: y~x̂+外生',
                'ivregress 2sls y x (endo=iv)',
                'ivregress liml 弱IV稳健',
                '识别LATE局部平均处理效应',
            ]},
            {'name': '三大检验', 'points': [
                '弱IV: 第一阶段F>10',
                'estat firststage 报F值',
                '过度识别: Hansen J~χ²(L-K)',
                'estat overid p>0.05',
                'Hausman/DWH p<0.05用IV',
            ]},
        ],
        'concept_chain': '内生性 → 找IV(相关+外生) → 第一阶段F>10 → 2SLS → J检验外生',
        'summary': 'IV识别的是LATE,不是总体ATE',
        'related': '第8章遗漏变量｜第11章面板FE｜第14章实证指南',
    },
    # 10 二值选择模型
    {
        'dir': '10_二值选择模型',
        'title': '第11章 二值选择模型',
        'branches': [
            {'name': 'LPM问题与模型', 'points': [
                'LPM预测概率可出[0,1]',
                '扰动必异方差 Var=p(1-p)',
                'Probit: P(y=1|x)=Φ(xβ)',
                'Logit: P=1/(1+e^(-xβ))',
                'S型CDF压缩到0~1',
            ]},
            {'name': '估计与解释', 'points': [
                'MLE最大似然估计',
                '对数几率 ln(P/(1-P))=xβ',
                '边际效应=φ(·)·β₁',
                'probit/logit y x1 x2',
                'Logit系数≈Probit×1.6',
            ]},
            {'name': '报告规范', 'points': [
                'margins,dydx(x)算AME',
                '不能直接抄β进结论',
                '伪R² (McFadden)',
                'estat classify分类准确率',
                'AME随x取值变化',
            ]},
        ],
        'concept_chain': '0/1因变量 → LPM失效 → Probit/Logit(MLE) → margins算AME',
        'summary': '必须报告平均边际效应,不能直接抄系数',
        'related': '第5章OLS｜第12章面板｜大牛库06受限因变量',
    },
    # 11 面板数据
    {
        'dir': '11_面板数据',
        'title': '第12章 面板数据',
        'branches': [
            {'name': '三种面板模型', 'points': [
                '混合Pooled OLS:忽略个体效应',
                '固定效应FE:组内去均值',
                '随机效应RE:GLS估计',
                'xtset id year 设定面板',
                'FE一致但损失时不变变量',
            ]},
            {'name': 'FE估计方法', 'points': [
                'LSDV:加个体虚拟变量',
                '组内估计 yᵢₜ-ȳᵢ',
                '一阶差分 Δyᵢₜ',
                '消除不随时间变化遗漏',
                '时变混淆仍需IV',
            ]},
            {'name': '模型选择', 'points': [
                'BP LM xttest0验个体效应',
                'Hausman检验选FE/RE',
                'p<0.05选FE(效应与X相关)',
                'p>0.05选RE更有效',
                'xtreg y x, fe/re',
            ]},
        ],
        'concept_chain': '面板数据 → LM检验个体效应 → Hausman选FE/RE → 报告系数',
        'summary': 'FE只能消时不变遗漏,时变混淆还需IV',
        'related': '第9章IV｜第8章模型设定｜大牛库05内生性面板',
    },
    # 12 平稳时间序列
    {
        'dir': '12_平稳时间序列',
        'title': '第13章 平稳时间序列',
        'branches': [
            {'name': 'ARMA模型族', 'points': [
                'AR(p): yₜ=Σφᵢyₜ₋ᵢ+εₜ',
                'MA(q): yₜ=εₜ+Σθⱼεₜ₋ⱼ',
                'ARMA(p,q)混合',
                'arima y, ar(p) ma(q)',
                '前提:序列平稳',
            ]},
            {'name': 'ACF/PACF识别', 'points': [
                'AR(p): ACF拖尾,PACF p截尾',
                'MA(q): ACF q截尾,PACF拖尾',
                'ARMA: 两者都拖尾',
                'Ljung-Box残差白噪声p>0.05',
                'AIC/BIC选最简洁模型',
            ]},
            {'name': 'VAR与格兰杰', 'points': [
                'VAR(p):每变量~自身+他变量滞后',
                'varsoc选滞后阶',
                'var y1 y2, lag(1/2)',
                'IRF脉冲响应动态影响',
                'vargranger=预测力非因果',
            ]},
        ],
        'concept_chain': '平稳序列 → ACF/PACF识别阶数 → ARMA/VAR → 残差白噪声诊断',
        'summary': '格兰杰因果≠经济因果,只是预测力',
        'related': '第8章自相关｜第14章单位根协整｜大牛库09时间序列',
    },
    # 13 单位根与协整
    {
        'dir': '13_单位根与协整',
        'title': '第14章 单位根与协整',
        'branches': [
            {'name': '单位根与伪回归', 'points': [
                '随机游走=非平稳',
                '两独立随机游走回归=伪回归',
                'R²高t大但全是假的',
                'ADF原假设有单位根',
                'p<0.05拒绝才平稳',
            ]},
            {'name': 'ADF检验形式', 'points': [
                'dfuller y, lags(p)',
                'noconstant 无均值无趋势',
                '默认 有均值无趋势',
                'trend 有均值有趋势',
                '用MacKinnon临界值,左单尾',
            ]},
            {'name': '协整与VECM', 'points': [
                'I(1):一阶差分平稳',
                '协整=长期均衡关系',
                'vecrank定协整秩',
                'VECM误差修正系数为负',
                '无协整→差分后VAR',
            ]},
        ],
        'concept_chain': 'ADF检验 → I(1) → 查协整 → 有协整用VECM,无协整差分VAR',
        'summary': 'p>0.05=默认有单位根,不是证明平稳',
        'related': '第13章平稳时间序列｜大牛库09时间序列',
    },
    # 14 实证研究指南
    {
        'dir': '14_实证研究指南',
        'title': '第15章 实证研究指南',
        'branches': [
            {'name': '研究全流程', 'points': [
                '选题四要素:具体有趣新颖可行',
                '数据清理+描述统计先行',
                '建模型选识别方法',
                '估计:符号+大小+显著性',
                '诊断+稳健性后才写作',
            ]},
            {'name': '诊断检验清单', 'points': [
                '异方差 estat imtest,white',
                '自相关 estat bgodfrey',
                '多重共线 estat vif',
                '遗漏变量 estat ovtest',
                'IV弱工具第一阶段F>10',
            ]},
            {'name': '稳健性与写作', 'points': [
                '换样本/去极值/换函数形式',
                'OLS→FE→IV换方法',
                '安慰剂检验随机分组',
                '统计显著≠经济显著',
                '结构:引言→文献→数据→结果→结论',
            ]},
        ],
        'concept_chain': '选题 → 数据 → 模型 → 估计 → 诊断 → 稳健性 → 写作投稿',
        'summary': '只报最佳结果=数据挖掘,换设定都稳才是真稳健',
        'related': '全方法回顾｜大牛库10论文写作｜12毕业论文实战',
    },
]


def main():
    ok = []
    for ch in CHAPTERS:
        out = f"{BASE}/{ch['dir']}/思维导图.svg"
        p = generate(
            output_path=out,
            title=ch['title'],
            branches=ch['branches'],
            concept_chain=ch['concept_chain'],
            summary=ch['summary'],
            related=ch['related'],
            palette='green',
        )
        ok.append((ch['dir'], ch['title'], p))
        print(f"OK {ch['dir']}")
    print(f"\n共生成 {len(ok)} 个SVG")


if __name__ == '__main__':
    main()
