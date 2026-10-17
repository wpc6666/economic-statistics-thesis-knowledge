#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竖版三列思维导图 SVG 生成器（参考 05_统计学原理/01_绪论 风格）

用法：
    from gen_svg import generate
    generate(
        output_path=".../思维导图.svg",
        title="第一章 绪论",
        branches=[
            {"name": "第一节 含义·作用·任务", "points": ["统计三含义", "三特点", ...]},
            {"name": "第二节 研究对象·方法",   "points": [...]},
            {"name": "第三节 基本概念",         "points": [...]},
        ],
        concept_chain="总体 → 总体单位 → 标志 → 变量 → 指标 → 指标体系",
        summary="本章是全书的词汇表",
        palette="cyan",   # cyan/green/purple/orange/blue/rose/teal
    )

或者命令行：
    python3 gen_svg.py output.svg "标题" palette '[{"name":"...","points":["..."]}]' "概念链" "说明"
"""
import json
import html
import sys
from pathlib import Path

# 配色方案：(root_fill, root_stroke, sec_fill, kp_fill, txt_kp, line_color, bg)
PALETTES = {
    "cyan":    ("#0e7490", "#164e63", "#06b6d4", "#ecfeff", "#164e63", "#0e7490", "#f0fdfa"),
    "green":   ("#166534", "#14532d", "#22c55e", "#dcfce7", "#14532d", "#166534", "#f0fdf4"),
    "purple":  ("#6d28d9", "#4c1d95", "#a78bfa", "#f5f3ff", "#4c1d95", "#6d28d9", "#faf5ff"),
    "orange":  ("#c2410c", "#7c2d12", "#fb923c", "#fff7ed", "#7c2d12", "#c2410c", "#fff7ed"),
    "blue":    ("#1e40af", "#1e3a8a", "#3b82f6", "#eff6ff", "#1e3a8a", "#1e40af", "#eff6ff"),
    "rose":    ("#be123c", "#881337", "#fb7185", "#fff1f2", "#881337", "#be123c", "#fff1f2"),
    "teal":    ("#0f766e", "#134e4a", "#14b8a6", "#f0fdfa", "#134e4a", "#0f766e", "#f0fdfa"),
    "slate":   ("#334155", "#0f172a", "#64748b", "#f1f5f9", "#0f172a", "#334155", "#f8fafc"),
}

FONT = "PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif"


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def generate(output_path: str,
             title: str,
             branches: list,
             concept_chain: str = "",
             summary: str = "",
             related: str = "",
             palette: str = "cyan") -> str:
    """
    branches: [{"name": str, "points": [str, ...]}, ...]  通常 3 个分支（左/中/右），
              也支持 2 个分支（左右居中）或 4 个分支（双列双排）。
    返回写出的绝对路径。
    """
    if palette not in PALETTES:
        palette = "cyan"
    root_c, root_s, sec_c, kp_c, txt_kp, line_c, bg = PALETTES[palette]

    n = len(branches)
    # 三列布局的中心 x
    if n <= 3:
        col_x = [180, 450, 720][:n]
        box_w = [280, 300, 280][:n]
    else:
        # 4 分支：2x2 网格
        col_x = [225, 675, 225, 675][:n]
        box_w = [380, 380, 380, 380][:n]

    # 计算高度
    SEC_Y = 150
    SEC_H = 50
    KP_H = 42
    KP_GAP = 8  # 节点间距（含边距）
    PAD_TOP = 30
    ROOT_H = 60

    # 每列从 SEC_Y+SEC_H+20 开始，依次排 kp
    col_bottoms = []
    for b in branches:
        y = SEC_Y + SEC_H + 20
        for _ in b["points"]:
            y += KP_H + KP_GAP
        col_bottoms.append(y)

    max_body = max(col_bottoms) if col_bottoms else SEC_Y + SEC_H + 40

    # 底部概念链区
    chain_y = max_body + 30
    chain_h = 80 if concept_chain else 0
    summary_y = chain_y + chain_h + 20
    summary_h = 50 if summary else 0
    related_y = summary_y + summary_h + 10
    related_h = 40 if related else 0

    total_h = related_y + related_h + 30
    # 最小高度
    total_h = max(total_h, 700)

    W = 900
    parts = []
    parts.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {total_h}" '
        f'width="{W}" height="{total_h}" font-family="{FONT}">'
    )
    parts.append(f'  <rect width="100%" height="100%" fill="{bg}"/>')

    # 根节点
    parts.append(
        f'  <rect x="300" y="{PAD_TOP}" width="300" height="{ROOT_H}" rx="14" '
        f'fill="{root_c}" stroke="{root_s}" stroke-width="2"/>'
    )
    parts.append(
        f'  <text x="450" y="{PAD_TOP+38}" text-anchor="middle" '
        f'fill="#ffffff" font-size="20" font-weight="bold">{_esc(title)}</text>'
    )

    root_bottom = PAD_TOP + ROOT_H  # = 90

    # 分支连接线 & sec 节点
    for i, (cx, bw, b) in enumerate(zip(col_x, box_w, branches)):
        left = cx - bw // 2
        # 从根节点出来的折线
        if n == 3:
            # M450 90 L450 120 Lcx 120 Lcx SEC_Y
            parts.append(
                f'  <path d="M450 {root_bottom} L450 120 L{cx} 120 L{cx} {SEC_Y}" '
                f'stroke="{line_c}" stroke-width="1.8" fill="none"/>'
            )
        elif n == 2:
            parts.append(
                f'  <path d="M450 {root_bottom} L450 120 L{cx} 120 L{cx} {SEC_Y}" '
                f'stroke="{line_c}" stroke-width="1.8" fill="none"/>'
            )
        else:
            parts.append(
                f'  <path d="M450 {root_bottom} L450 120 L{cx} 120 L{cx} {SEC_Y}" '
                f'stroke="{line_c}" stroke-width="1.8" fill="none"/>'
            )

        # sec 节点
        parts.append(
            f'  <rect x="{left}" y="{SEC_Y}" width="{bw}" height="{SEC_H}" rx="10" '
            f'fill="{sec_c}" stroke="{root_c}" stroke-width="1.5"/>'
        )
        parts.append(
            f'  <text x="{cx}" y="{SEC_Y+31}" text-anchor="middle" '
            f'fill="#ffffff" font-size="15" font-weight="bold">{_esc(b["name"])}</text>'
        )

        # kp 节点
        y = SEC_Y + SEC_H + 10
        for pt in b["points"]:
            # 连线
            parts.append(
                f'  <line x1="{cx}" y1="{y-10}" x2="{cx}" y2="{y}" '
                f'stroke="{line_c}" stroke-width="1.2"/>'
            )
            # 节点框
            parts.append(
                f'  <rect x="{left}" y="{y}" width="{bw}" height="{KP_H}" rx="8" '
                f'fill="{kp_c}" stroke="{sec_c}" stroke-width="1.2"/>'
            )
            # 文字（过长截断到约 22 字）
            txt = str(pt)
            if len(txt) > 26:
                txt = txt[:25] + "…"
            parts.append(
                f'  <text x="{cx}" y="{y+KP_H//2+5}" text-anchor="middle" '
                f'fill="{txt_kp}" font-size="12">{_esc(txt)}</text>'
            )
            y += KP_H + KP_GAP

    # 概念关系链
    if concept_chain:
        parts.append(
            f'  <rect x="80" y="{chain_y}" width="740" height="{chain_h}" rx="12" '
            f'fill="#ffffff" stroke="{line_c}" stroke-width="1.5" stroke-dasharray="4,3"/>'
        )
        parts.append(
            f'  <text x="450" y="{chain_y+28}" text-anchor="middle" '
            f'fill="{root_s}" font-size="14" font-weight="bold">🔗 概念关系链</text>'
        )
        # 自动换行：超过 50 字折两行
        chain_txt = str(concept_chain)
        if len(chain_txt) > 48:
            mid = len(chain_txt) // 2
            # 找最近的箭头分隔
            for off in range(0, 15):
                if mid + off < len(chain_txt) and chain_txt[mid+off] == "→":
                    mid = mid + off + 1
                    break
                if mid - off >= 0 and chain_txt[mid-off] == "→":
                    mid = mid - off + 1
                    break
            l1 = chain_txt[:mid].strip()
            l2 = chain_txt[mid:].strip()
            parts.append(
                f'  <text x="450" y="{chain_y+52}" text-anchor="middle" '
                f'fill="{txt_kp}" font-size="12.5">{_esc(l1)}</text>'
            )
            parts.append(
                f'  <text x="450" y="{chain_y+72}" text-anchor="middle" '
                f'fill="{txt_kp}" font-size="12.5">{_esc(l2)}</text>'
            )
        else:
            parts.append(
                f'  <text x="450" y="{chain_y+52}" text-anchor="middle" '
                f'fill="{txt_kp}" font-size="13">{_esc(chain_txt)}</text>'
            )

    # 一句话总结
    if summary:
        parts.append(
            f'  <text x="450" y="{summary_y+22}" text-anchor="middle" '
            f'fill="{root_c}" font-size="13" font-style="italic">💡 {_esc(summary)}</text>'
        )

    # 相关章节
    if related:
        parts.append(
            f'  <text x="450" y="{related_y+22}" text-anchor="middle" '
            f'fill="{line_c}" font-size="11.5">📚 相关：{_esc(related)}</text>'
        )

    parts.append('</svg>')

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out.resolve())


# 命令行入口
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: gen_svg.py <output.svg> <title> <palette> <branches_json> [concept_chain] [summary] [related]")
        sys.exit(1)
    out = sys.argv[1]
    title = sys.argv[2]
    palette = sys.argv[3]
    branches = json.loads(sys.argv[4])
    chain = sys.argv[5] if len(sys.argv) > 5 else ""
    summary = sys.argv[6] if len(sys.argv) > 6 else ""
    related = sys.argv[7] if len(sys.argv) > 7 else ""
    p = generate(out, title, branches, chain, summary, related, palette)
    print(f"OK -> {p}")
