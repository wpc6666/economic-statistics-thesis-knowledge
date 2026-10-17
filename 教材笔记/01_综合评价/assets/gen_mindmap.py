#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯 Python 生成 XMind 风格"左右展开"思维导图（SVG 矢量，中文字体）。
不依赖 graphviz。用法：python3 gen_mindmap.py
布局：中心节点；一级分支左右分布；二/三级节点向外展开；贝塞尔曲线连接。
"""
import html

FONT = "PingFang SC, Hiragino Sans GB, STHeiti, Heiti SC, sans-serif"
# 层级样式：(字号, 填充, 字色, 圆角)
STY = {
    0: (22, "#2c3e50", "#ffffff", 12),   # 中心
    1: (15, None, "#ffffff", 9),          # 一级，填充取分支色
    2: (13, None, "#1a1a1a", 7),          # 二级，浅色填充
    3: (12, None, "#333333", 6),          # 三级
}
PAD_H, PAD_V = 12, 7
GAP_V3, GAP_V2, GAP_V1 = 6, 12, 26   # 同级垂直间距（按层级）
GAP_H = 34                            # 层间水平间距

# 分支配色（一级）：深色（节点）/浅色（二级底）/连线
PALETTE = [
    ("#c0392b", "#f7dedb"), ("#d35400", "#fbe5d6"), ("#b7950b", "#f7eeb8"),
    ("#27ae60", "#d8f0e2"), ("#16a085", "#d4efe9"), ("#2980b9", "#d6e8f5"),
    ("#8e44ad", "#ead9f2"), ("#2c3e50", "#dde2e6"), ("#c0392b", "#f7dedb"),
    ("#d35400", "#fbe5d6"), ("#27ae60", "#d8f0e2"), ("#2980b9", "#d6e8f5"),
    ("#8e44ad", "#ead9f2"), ("#16a085", "#d4efe9"),
]

def text_w(s, fs):
    cn = sum(1 for c in s if ord(c) > 0x2e7f)
    other = len(s) - cn
    return cn * fs + other * fs * 0.6

class N:
    __slots__ = ("t", "ch", "lv", "w", "h", "x", "y", "color", "light", "_h")
    def __init__(self, t, ch=None, lv=1):
        self.t = t; self.ch = ch or []; self.lv = lv
        fs = STY[lv][0]
        self.w = text_w(t, fs) + 2 * PAD_H
        self.h = fs + 2 * PAD_V
        self.x = self.y = 0; self.color = self.light = None

def gap(lv):
    return GAP_V1 if lv == 1 else (GAP_V2 if lv == 2 else GAP_V3)

def calc_h(n):
    if not n.ch:
        n._h = n.h; return n._h
    tot = sum(calc_h(c) for c in n.ch) + (len(n.ch) - 1) * gap(n.lv + 1)
    n._h = max(n.h, tot)
    return n._h

def place(n, x, top, side, color=None, light=None):
    """side=+1 向右（节点左缘=x）；side=-1 向左（节点右缘=x）。"""
    n.color, n.light = color, light
    n.x = x if side == 1 else x - n.w
    n.y = top + (n._h - n.h) / 2
    if n.ch:
        g = gap(n.lv + 1)
        tot = sum(c._h for c in n.ch) + (len(n.ch) - 1) * g
        cur = top + (n._h - tot) / 2
        if side == 1:
            cx = x + n.w + GAP_H
        else:
            cx = x - n.w - GAP_H
        for c in n.ch:
            place(c, cx, cur, side, color, light)
            cur += c._h + g

def collect(n, out):
    out.append(n)
    for c in n.ch:
        collect(c, out)

def edge_x(n):
    return (n.x + n.w) if n is not None else 0

def render_side(roots, side, cx, cy, top_pad):
    """roots: 一级节点列表；返回该侧所有节点 + 连线。"""
    total = sum(r._h for r in roots) + (len(roots) - 1) * GAP_V1
    top = cy - total / 2
    nodes, edges = [], []
    cur = top
    for i, r in enumerate(roots):
        color, light = PALETTE[i % len(PALETTE)]
        if side == 1:
            x0 = cx + GAP_H
        else:
            x0 = cx - GAP_H
        place(r, x0, cur, side, color, light)
        cur += r._h + GAP_V1
        grp = []
        collect(r, grp)
        nodes += grp
        for nn in grp:
            for c in nn.ch:
                edges.append((nn, c, color))
    return nodes, edges

def esc(s):
    return html.escape(s, quote=True)

def draw_node(n):
    fs, fill, tcol, rad = STY[n.lv]
    if n.lv == 0:
        fill, tcol = "#2c3e50", "#ffffff"
    elif n.lv == 1:
        fill, tcol = n.color, "#ffffff"
    elif n.lv == 2:
        fill, tcol = n.light, "#1a1a1a"
    else:
        fill, tcol = "#ffffff", "#333333"
    ty = n.y + n.h / 2 + fs * 0.35
    rect = (f'<rect x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" '
            f'rx="{rad}" ry="{rad}" fill="{fill}" stroke="{n.color or "#2c3e50"}" '
            f'stroke-width="{1 if n.lv>=2 else 1.4}"/>')
    txt = (f'<text x="{n.x+n.w/2:.1f}" y="{ty:.1f}" font-size="{fs}" fill="{tcol}" '
           f'text-anchor="middle" font-family="{FONT}">{esc(n.t)}</text>')
    return rect + txt

def curve(p, c, color):
    # 水平 S 贝塞尔
    if c.x >= p.x:   # 向右
        x1, y1 = p.x + p.w, p.y + p.h / 2
        x2, y2 = c.x, c.y + c.h / 2
    else:
        x1, y1 = p.x, p.y + p.h / 2
        x2, y2 = c.x + c.w, c.y + c.h / 2
    mx = (x1 + x2) / 2
    d = f"M {x1:.1f} {y1:.1f} C {mx:.1f} {y1:.1f}, {mx:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}"
    w = 2.2 if p.lv == 1 else 1.2
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" opacity="0.85"/>'

def build(center_text, left_roots, right_roots, out_path, title):
    for r in left_roots + right_roots:
        calc_h(r)
    # 估算尺寸
    allr = left_roots + right_roots
    total_h = max(sum(r._h for r in left_roots) + (len(left_roots)-1)*GAP_V1,
                  sum(r._h for r in right_roots) + (len(right_roots)-1)*GAP_V1)
    # 中心
    cn = N(center_text, lv=0)
    cn.w = max(cn.w, text_w(center_text, 22) + 2*PAD_H)
    cn.h = max(cn.h, 44)
    # 宽度（粗略）：中心半宽 + 一级 + 二级 + 三级
    def side_w(roots):
        m = 0
        for r in roots:
            grp = []; collect(r, grp)
            rightmost = max((n.x + n.w) for n in grp)
            leftmost = min(n.x for n in grp)
            m = max(m, rightmost - 0, 0 - leftmost)
        return m
    # 先以中心 cx=0 临时布局度量
    nodes_r, edges_r = render_side(right_roots, 1, 0, 0, 0)
    nodes_l, edges_l = render_side(left_roots, -1, 0, 0, 0)
    w_r = max((n.x + n.w) for n in nodes_r)
    w_l = max((-n.x) for n in nodes_l)
    H = total_h + 80
    cx = w_l + cn.w / 2 + 20
    W = w_l + cn.w + w_r + 40
    cy = H / 2
    # 重新布局（真实 cx）
    for r in allr:
        pass
    nodes_r, edges_r = render_side(right_roots, 1, cx, cy, 0)
    nodes_l, edges_l = render_side(left_roots, -1, cx, cy, 0)
    cn.x = cx - cn.w / 2; cn.y = cy - cn.h / 2
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
             f'viewBox="0 0 {W:.0f} {H:.0f}">']
    parts.append(f'<rect width="100%" height="100%" fill="#fbfcfd"/>')
    # 连线
    for p, c, col in edges_r + edges_l:
        parts.append(curve(p, c, col))
    # 节点
    for n in nodes_l + nodes_r:
        parts.append(draw_node(n))
    parts.append(draw_node(cn))
    parts.append(f'<text x="{W/2:.0f}" y="26" font-size="15" fill="#7f8c8d" '
                 f'text-anchor="middle" font-family="{FONT}">{esc(title)}</text>')
    parts.append("</svg>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("written:", out_path, f"{W:.0f}x{H:.0f}")

# ============ 全书思维导图数据 ============
def L(t, *ch):
    return N(t, list(ch), 1)
def L2(t, *ch):
    return N(t, list(ch), 2)
def L3(t):
    return N(t, [], 3)

intro = L("绪论",
    L2("评价与统计评价"), L2("评价标准", L3("时间"), L3("空间"), L3("经验/理论"), L3("计划/目标")),
    L2("单指标评价局限"), L2("综合评价"))
ch1 = L("第一章 一般问题",
    L2("问题提出"), L2("一般步骤（5步）"), L2("数学思想：两次投影"))
ch2 = L("第二章 指标体系",
    L2("指标概念"), L2("选择方法", L3("定性法"), L3("系统聚类"), L3("极小广义方差"),
        L3("极大不相关"), L3("主成分/因子")))
ch3 = L("第三章 无量纲化",
    L2("定性数量化"), L2("逆向/适度正向化"),
    L2("定量无量纲", L3("直线型"), L3("折线型"), L3("曲线型")))
ch4 = L("第四章 赋权",
    L2("主观赋权", L3("专家评判"), L3("AHP")),
    L2("客观赋权", L3("变异系数"), L3("相关系数"), L3("熵值"), L3("坎蒂雷")),
    L2("方法选择与组合"))
ch5 = L("第五章 数值综合",
    L2("线性综合"), L2("几何综合"), L2("混合综合"), L2("模型综合(含DEA)"))
ch6 = L("第六章 常规方法",
    L2("综合评分"), L2("综合指数"), L2("秩和比 RSR"), L2("功效系数"))
ch7 = L("第七章 灰色关联",
    L2("关联度方法"), L2("评价应用"))
ch8 = L("第八章 模糊综合",
    L2("基本概念"), L2("基本步骤"), L2("舍去评语等级集"))
ch9 = L("第九章 主成分",
    L2("原理"), L2("步骤"), L2("实例"), L2("特点"), L2("改进"))
ch10 = L("第十章 因子分析",
    L2("原理"), L2("步骤"), L2("与主成分异同"), L2("结合应用"))
case1 = L("案例一 企业入驻")
case2 = L("案例二 城市竞争力·房价")
case3 = L("案例三 社会发展")

left = [intro, ch1, ch2, ch3, ch4, ch5, ch6]
right = [ch7, ch8, ch9, ch10, case1, case2, case3]

build("综合评价技术及应用", left, right,
      "/Users/wangpengcheng/IT/综合评价/学习笔记/assets/全书思维导图.svg",
      "《综合评价技术及应用》（陈正伟）全书思维导图")
