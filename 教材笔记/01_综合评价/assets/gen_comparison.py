#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成"综合评价方法对比总览"（3 列网格竖版，宽度 1080，比例合理）。
"""
import html
FONT = "PingFang SC, Hiragino Sans GB, STHeiti, Heiti SC, sans-serif"
def esc(s): return html.escape(s, quote=True)
def tw(s, fs):
    cn = sum(1 for c in s if ord(c) > 0x2e7f)
    return cn*fs + (len(s)-cn)*fs*0.6
def wrap(s, fs, maxw):
    lines, cur = [], ""
    for ch in s:
        if tw(cur+ch, fs) > maxw and cur:
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines

W = 1080; PAD = 40
COLS = 3; GAP_X = 16
CARD_W = (W - 2*PAD - (COLS-1)*GAP_X)//COLS   # 322
CARD_H = 90; GAP_Y = 14; HEADER_H = 34

FAMILIES = [
    ("一、赋权方法 · 权重从哪来", "#2980b9", [
        ("专家评判法", "主观 · 专家独立打分后平均归一", "有专家资源"),
        ("AHP 层次分析", "主观 · 两两比较 + 一致性检验", "指标分层"),
        ("变异系数法", "客观 · 按指标离散程度赋权", "数据差异大"),
        ("相关系数法", "客观 · 按重复信息赋权", "指标相关"),
        ("熵值法", "客观 · 按信息量/离散度赋权", "数据完整"),
        ("坎蒂雷法", "客观 · 同时利用变异与相关", "信息兼顾"),
        ("组合赋权", "主客观乘法/线性合成", "稳健折中"),
    ]),
    ("二、合成方法 · 怎么把指标合起来", "#16a085", [
        ("线性综合", "加权求和 · 指标可线性补偿", "可相互替代"),
        ("几何综合", "连乘 · 一票否决、要求均衡", "不可偏废"),
        ("混合综合", "加 + 乘叠加", "部分补偿"),
        ("模型综合", "建函数 Z=F(X) · 投影", "有明确机制"),
        ("空间距离法", "实际点到目标点距离", "有标杆点"),
        ("DEA 数据包络", "多投入多产出 · 线性规划效率", "评价相对效率"),
    ]),
    ("三、常规成套方法 · 确定性数据", "#27ae60", [
        ("综合评分法", "实际值转分数后加权", "有标准、易打分"),
        ("综合指数法", "个体指数加权", "有基期/计划标准"),
        ("秩和比 RSR", "按位次加权 · 抗异常值", "仅知位次"),
        ("功效系数法", "满意/不允许映射 60~100", "有双边界"),
    ]),
    ("四、不确定性方法 · 模糊/灰色", "#8e44ad", [
        ("灰色关联度", "信息不完全 · 曲线形状相似", "贫信息·小样本"),
        ("模糊综合评价", "边界模糊 · 隶属度矩阵合成", "有评语等级"),
    ]),
    ("五、降维方法 · 指标多且相关", "#b7950b", [
        ("主成分分析", "方差最大 · 客观综合得分", "重综合排序"),
        ("因子分析", "公共因子 · 旋转后结构解释", "重潜在结构"),
    ]),
]

# 计算高度
y = 64
bands = []
for title, color, cards in FAMILIES:
    rows = (len(cards)+COLS-1)//COLS
    h = HEADER_H + rows*CARD_H + (rows-1)*GAP_Y
    bands.append((title, color, cards, y, h))
    y += h + GAP_Y + 14
H = y + 26

parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<rect width="100%" height="100%" fill="#fbfcfd"/>',
         f'<text x="{W/2}" y="36" font-size="21" fill="#2c3e50" text-anchor="middle" '
         f'font-family="{FONT}" font-weight="bold">综合评价方法对比总览</text>',
         f'<text x="{W/2}" y="58" font-size="13" fill="#7f8c8d" text-anchor="middle" '
         f'font-family="{FONT}">陈正伟《综合评价技术及应用》 · 五大方法家族</text>']

for title, color, cards, by, bh in bands:
    parts.append(f'<rect x="{PAD}" y="{by}" width="8" height="26" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{PAD+18}" y="{by+19}" font-size="16" fill="{color}" '
                 f'font-family="{FONT}" font-weight="bold">{esc(title)}</text>')
    cy = by + HEADER_H
    for i,(name, feat, tag) in enumerate(cards):
        r = i//COLS; c = i%COLS
        cx = PAD + c*(CARD_W+GAP_X)
        yy = cy + r*(CARD_H+GAP_Y)
        parts.append(f'<rect x="{cx}" y="{yy}" width="{CARD_W}" height="{CARD_H}" rx="9" '
                     f'fill="#ffffff" stroke="#dfe6ea" stroke-width="1.2"/>')
        parts.append(f'<rect x="{cx}" y="{yy}" width="{CARD_W}" height="6" rx="3" fill="{color}"/>')
        parts.append(f'<text x="{cx+15}" y="{yy+31}" font-size="15" font-weight="bold" fill="#1a1a1a" '
                     f'font-family="{FONT}">{esc(name)}</text>')
        for k,ln in enumerate(wrap(feat,12.5,CARD_W-30)[:2]):
            parts.append(f'<text x="{cx+15}" y="{yy+53+k*17}" font-size="12.5" fill="#555" '
                         f'font-family="{FONT}">{esc(ln)}</text>')
        twp = tw(tag,11)+16
        parts.append(f'<rect x="{cx+13}" y="{yy+CARD_H-24}" width="{twp:.0f}" height="18" rx="9" '
                     f'fill="{color}" opacity="0.14"/>')
        parts.append(f'<text x="{cx+21}" y="{yy+CARD_H-11}" font-size="11" fill="{color}" '
                     f'font-family="{FONT}">{esc(tag)}</text>')

parts.append("</svg>")
out = "/Users/wangpengcheng/IT/综合评价/学习笔记/assets/方法对比总览.svg"
open(out,"w",encoding="utf-8").write("\n".join(parts))
print("written",out,f"{W}x{H} ratio {W/H:.2f}")
