#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合思维导图：教材知识 → 方法选择 → 论文写作 → 组合评价。
竖版：4 阶段主干自上而下，各阶段子项向下展开为卡片。
"""
import html
FONT = "PingFang SC, Hiragino Sans GB, STHeiti, Heiti SC, sans-serif"
def esc(s): return html.escape(s, quote=True)
def tw(s, fs):
    cn=sum(1 for c in s if ord(c)>0x2e7f)
    return cn*fs+(len(s)-cn)*fs*0.6
def wrap(s,fs,maxw):
    lines,cur=[],""
    for ch in s:
        if tw(cur+ch,fs)>maxw and cur: lines.append(cur);cur=ch
        else: cur+=ch
    if cur: lines.append(cur)
    return lines

STAGES=[
    ("① 教材知识","学方法、懂原理","#2980b9",[
        ("赋权方法","权重从哪来（主观/客观）"),
        ("合成方法","线性/几何/混合"),
        ("常规成套","评分/指数/RSR/功效"),
        ("不确定性","灰色关联 / 模糊综合"),
        ("降维方法","主成分 / 因子分析"),
    ]),
    ("② 方法选择","按数据选方法","#16a085",[
        ("定指标体系","目标层-准则层-指标层"),
        ("定性指标量化","次序/等级/主观"),
        ("正逆适度处理","先同向化"),
        ("选无量纲化","极差/标准化/比重"),
        ("选择赋权","主观/客观/组合"),
        ("合成或成套","按能否补偿选"),
    ]),
    ("③ 论文写作","规范成文","#27ae60",[
        ("第1章 绪论","背景、综述、意义"),
        ("第2章 指标与数据","体系、来源、预处理"),
        ("第3章 方法","赋权与评价方法"),
        ("第4章 实证","得分、排名、分析"),
        ("第5章 结论对策","结论、建议、不足"),
    ]),
    ("④ 组合评价","多方法互证","#8e44ad",[
        ("多方法分别评价","各出得分与排名"),
        ("事前一致性检验","Kendall W / Spearman"),
        ("组合合成","Borda / 加权平均"),
        ("得到稳健排名","结论不依赖单一方法"),
    ]),
]

W=900; PAD=30
HDR=50; CARD_H=66; GY=12; SGAP=26; COLS=3
layout=[]; y=104
for name,sub,color,items in STAGES:
    rows=(len(items)+COLS-1)//COLS
    h=HDR+12+rows*CARD_H+(rows-1)*GY
    layout.append((name,sub,color,items,y,h,rows))
    y+=h+SGAP
H=y+20
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
 '<rect width="100%" height="100%" fill="#fbfcfd"/>',
 f'<text x="{W/2}" y="40" font-size="22" fill="#2c3e50" text-anchor="middle" font-weight="bold" '
 f'font-family="{FONT}">综合评价研究 · 从教材到论文全景图</text>',
 f'<text x="{W/2}" y="66" font-size="13" fill="#7f8c8d" text-anchor="middle" '
 f'font-family="{FONT}">教材知识 → 方法选择 → 论文写作 → 组合评价</text>']
cw=(W-2*PAD-(COLS-1)*GY)/COLS
for si,(name,sub,color,items,sy,h,rows) in enumerate(layout):
    # 阶段头
    parts.append(f'<rect x="{PAD}" y="{sy}" width="{W-2*PAD}" height="{HDR}" rx="10" fill="{color}"/>')
    parts.append(f'<text x="{PAD+20}" y="{sy+32}" font-size="17" fill="#fff" text-anchor="start" '
                 f'font-weight="bold" font-family="{FONT}">{esc(name)}</text>')
    parts.append(f'<text x="{W-PAD-20}" y="{sy+32}" font-size="13" fill="#eef5fb" text-anchor="end" '
                 f'font-family="{FONT}">{esc(sub)}</text>')
    if si==0:
        parts.append(f'<line x1="{W/2}" y1="82" x2="{W/2}" y2="{sy-4}" stroke="#5a6b7b" stroke-width="2" '
                     f'marker-end="url(#ah)"/>')
    # 卡片
    for i,(t,d) in enumerate(items):
        r=i//COLS; c=i%COLS
        x=PAD+c*(cw+GY); yy=sy+HDR+12+r*(CARD_H+GY)
        parts.append(f'<rect x="{x}" y="{yy}" width="{cw}" height="{CARD_H}" rx="9" fill="#ffffff" '
                     f'stroke="#dfe6ea" stroke-width="1.2"/>')
        parts.append(f'<rect x="{x}" y="{yy}" width="5" height="{CARD_H}" rx="2.5" fill="{color}"/>')
        parts.append(f'<text x="{x+15}" y="{yy+28}" font-size="14.5" font-weight="bold" fill="#1a1a1a" '
                     f'font-family="{FONT}">{esc(t)}</text>')
        for k,ln in enumerate(wrap(d,12,cw-26)[:2]):
            parts.append(f'<text x="{x+15}" y="{yy+50+k*15}" font-size="12" fill="#666" '
                         f'font-family="{FONT}">{esc(ln)}</text>')
    if si<len(layout)-1:
        parts.append(f'<line x1="{W/2}" y1="{sy+h}" x2="{W/2}" y2="{sy+h+SGAP-4}" stroke="#9aa7b4" '
                     f'stroke-width="2" marker-end="url(#ah)"/>')
parts.append(f'<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" '
             f'markerUnits="strokeWidth"><path d="M0,0 L8,3 L0,6 z" fill="#5a6b7b"/></marker></defs>')
parts.append("</svg>")
out="/Users/wangpengcheng/IT/综合评价/assets/综合思维导图.svg"
open(out,"w",encoding="utf-8").write("\n".join(parts))
print("written",out,f"{W}x{H} ratio {W/H:.2f}")
