#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯 Python 生成"综合评价方法选择决策树"（竖版：根在顶，分支向下，SVG 矢量）。
"""
import html
FONT = "PingFang SC, Hiragino Sans GB, STHeiti, Heiti SC, sans-serif"

def esc(s): return html.escape(s, quote=True)
def text(x,y,s,size=14,anchor="middle",weight="normal",color="#1f2d3d"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{color}">{esc(s)}</text>')
def box(x,y,w,h,fill,stroke,r=8,sw=1.5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def line(x1,y1,x2,y2,color="#5a6b7b",w=2,arrow=False):
    m=' marker-end="url(#ah)"' if arrow else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{m}/>'

# (分支名, 分支色, [(叶子, 边标签)], 叶子色)
branches=[
 ("信息不完全 · 贫信息 · 小样本","#8e44ad",
   [("灰色关联度法","")]),
 ("边界模糊 · 有评语等级","#8e44ad",
   [("模糊综合评价","")]),
 ("指标众多 · 高相关 · 需降维","#27ae60",
   [("主成分分析","重综合得分"),("因子分析","重结构解释")]),
 ("多投入 · 多产出 · 评效率","#27ae60",
   [("DEA 数据包络分析","")]),
 ("确定性数据 · 按补偿关系","#27ae60",
   [("线性综合","可补偿"),("几何综合","要均衡"),("混合综合","混合型"),("模型综合","有机制")]),
 ("常规成套方法","#27ae60",
   [("综合评分法","易打分"),("综合指数法","有基期"),("秩和比 RSR","知位次"),("功效系数法","双边界")]),
]

W=780; PAD=30
HDR=44; LH=34; LG=12; SGAP=22
layout=[]; y=118
for name,c,leaves in branches:
    rows=(len(leaves)+1)//2
    h=HDR+10+rows*LH+(rows-1)*LG
    layout.append((name,c,leaves,y,h,rows))
    y+=h+SGAP
H=y+24
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
 '<rect width="100%" height="100%" fill="#fbfcfd"/>',
 '<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,3 L0,6 z" fill="#5a6b7b"/></marker></defs>']
parts.append(text(W/2,38,"综合评价方法选择决策树",22,weight="bold",color="#2c3e50"))
# 根
rw,rh=320,46; rx=(W-rw)/2; ry=64
parts.append(box(rx,ry,rw,rh,"#fcf3cf","#b7950b",10,2))
parts.append(text(W/2,ry+29,"如何选择综合评价方法？",16,weight="bold"))
cw=(W-2*PAD-12)/2
for bi,(name,c,leaves,sy,sh,rows) in enumerate(layout):
    parts.append(box(PAD,sy,W-2*PAD,HDR,c,c,9,1.6))
    parts.append(text(PAD+18,sy+28,name,14.5,anchor="start",weight="bold",color="#ffffff"))
    if bi==0:
        parts.append(line(W/2,ry+rh,W/2,sy-4,"#5a6b7b",2,arrow=True))
    for i,(leaf,elbl) in enumerate(leaves):
        r=i//2; col=i%2
        lx=PAD+col*(cw+12)
        ly=sy+HDR+10+r*(LH+LG)
        parts.append(box(lx,ly,cw,LH,"#ffffff","#c4d0db",7,1.3))
        if elbl:
            parts.append(text(lx+14,ly+22,f"{leaf}（{elbl}）",13,anchor="start",color="#33414f"))
        else:
            parts.append(text(lx+14,ly+22,leaf,13,anchor="start",color="#33414f"))
    if bi<len(layout)-1:
        parts.append(line(W/2,sy+sh,W/2,sy+sh+SGAP-4,"#9aa7b4",2,arrow=True))
parts.append("</svg>")
out="/Users/wangpengcheng/IT/综合评价/学习笔记/assets/方法选择决策树.svg"
open(out,"w",encoding="utf-8").write("\n".join(parts))
print("written",out,f"{W}x{H} ratio {W/H:.2f}")
