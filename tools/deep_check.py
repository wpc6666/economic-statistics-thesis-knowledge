#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深度断链检查：锚点 + 图片 + mermaid语法"""
import os
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/wangpengcheng/IT/03_知识库/综合评价")

# ── 排除目录（非用户实际看的内容）──
EXCLUDE_DIRS = {".git", ".obsidian", "tools", "_tools", "原文件"}

def in_excluded(rel_path):
    parts = Path(rel_path).parts
    return any(p in EXCLUDE_DIRS for p in parts)

# ── 收集所有 md 文件 ──
all_md_stems = {}       # stem -> [path]
all_md_rel = set()      # 带路径无后缀
all_images = set()      # 图片文件名
all_images_rel = set()

for p in ROOT.rglob("*"):
    if not p.is_file():
        continue
    rel = p.relative_to(ROOT)
    if in_excluded(rel):
        continue
    if p.suffix == ".md":
        all_md_stems.setdefault(p.stem, []).append(p)
        all_md_rel.add(str(rel.with_suffix("")))
    elif p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif"}:
        all_images.add(p.stem)
        all_images_rel.add(str(rel))

# ── 预扫描每个md文件的标题锚点 ──
# Obsidian锚点：# 标题，或 {#custom-anchor}
heading_anchor_re = re.compile(r'^#{1,6}\s+(.+?)\s*$', re.MULTILINE)
custom_anchor_re = re.compile(r'\{#([^}]+)\}')

file_anchors = defaultdict(set)  # md_path -> set of anchor names

for p in ROOT.rglob("*.md"):
    rel = p.relative_to(ROOT)
    if in_excluded(rel):
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    for m in heading_anchor_re.finditer(text):
        heading = m.group(1).strip()
        # Obsidian锚点：去掉格式符号，转小写，空格转连字符
        anchor = re.sub(r'[*_`~\[\]()]', '', heading).strip().lower()
        anchor = re.sub(r'\s+', '-', anchor)
        file_anchors[p].add(anchor)
        file_anchors[p].add(heading.lower())  # 也存原始标题
    for m in custom_anchor_re.finditer(text):
        file_anchors[p].add(m.group(1).strip())

# ── 正则 ──
WIKILINK_RE = re.compile(r'\[\[([^\[\]]+)\]\]')
IMAGE_WIKILINK_RE = re.compile(r'!\[\[([^\[\]]+)\]\]')
MD_IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
MERMAID_BLOCK_RE = re.compile(r'```mermaid\s*\n([\s\S]*?)```')

def strip_code_blocks(text):
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]*`', '', text)
    return text

# ── 收集问题 ──
broken_links = []      # (file, raw, reason)
broken_anchors = []    # (file, raw, target_file, anchor)
broken_images = []     # (file, raw, image_name)
mermaid_issues = []    # (file, block_idx, issue)

md_count = 0
for md_path in ROOT.rglob("*.md"):
    rel = md_path.relative_to(ROOT)
    if in_excluded(rel):
        continue
    md_count += 1
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    text_nocode = strip_code_blocks(text)

    # ── 1. wikilink 检查 ──
    for m in WIKILINK_RE.finditer(text_nocode):
        raw = m.group(1).strip()
        raw_clean = raw.replace("\\|", "|")
        # 分离目标和锚点
        parts = raw_clean.split("|")[0].split("#")
        target = parts[0].strip()
        anchor = parts[1].strip() if len(parts) > 1 else None

        if not target:
            # 纯锚点链接 [[#heading]]，只检查当前文件
            if anchor:
                anchors = file_anchors.get(md_path, set())
                anchor_lower = anchor.lower()
                anchor_dash = re.sub(r'\s+', '-', anchor_lower)
                if anchor_lower not in anchors and anchor_dash not in anchors:
                    broken_anchors.append((str(rel), raw, str(rel), anchor))
            continue

        if re.match(r'^(path|text|xxx|example|foo|bar)$', target, re.IGNORECASE):
            continue

        if target.endswith(".md"):
            target = target[:-3]

        # 解析目标文件
        target_file = None
        if "/" in target or target.startswith("../") or target.startswith("./"):
            resolved = (md_path.parent / target).resolve()
            if resolved.with_suffix(".md").exists():
                target_file = resolved.with_suffix(".md")
            elif resolved.with_suffix(".svg").exists():
                target_file = resolved.with_suffix(".svg")
            else:
                broken_links.append((str(rel), raw, f"相对路径不存在: {target}"))
                continue
        else:
            if target in all_md_stems:
                target_file = all_md_stems[target][0]
            else:
                broken_links.append((str(rel), raw, f"全局文件名未找到: {target}"))
                continue

        # 检查锚点
        if anchor and target_file.suffix == ".md":
            anchors = file_anchors.get(target_file, set())
            anchor_lower = anchor.lower()
            anchor_dash = re.sub(r'\s+', '-', anchor_lower)
            if anchor_lower not in anchors and anchor_dash not in anchors:
                broken_anchors.append((str(rel), raw, str(target_file.relative_to(ROOT)), anchor))

    # ── 2. 图片 wikilink 检查 ──
    for m in IMAGE_WIKILINK_RE.finditer(text_nocode):
        raw = m.group(1).strip()
        img_target = raw.split("|")[0].split("#")[0].strip()
        if not img_target:
            continue
        img_stem = Path(img_target).stem
        if img_stem not in all_images and img_target not in all_images_rel:
            broken_images.append((str(rel), raw, img_target))

    # ── 3. md图片语法检查 ──
    for m in MD_IMAGE_RE.finditer(text_nocode):
        img_path = m.group(2).strip()
        if img_path.startswith("http") or img_path.startswith("data:"):
            continue
        # 去掉query参数
        img_path_clean = img_path.split("?")[0].split("#")[0]
        resolved = (md_path.parent / img_path_clean).resolve()
        if not resolved.exists():
            broken_images.append((str(rel), m.group(0), img_path))

    # ── 4. mermaid 语法粗检 ──
    for idx, m in enumerate(MERMAID_BLOCK_RE.finditer(text)):
        block = m.group(1).strip()
        if not block:
            mermaid_issues.append((str(rel), idx, "空mermaid块"))
            continue
        first_line = block.split("\n")[0].strip()
        if not re.match(r'^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|journey|gantt|pie|gitGraph|C4Component|mindmap|timeline)', first_line):
            mermaid_issues.append((str(rel), idx, f"未知图类型: {first_line[:30]}"))

# ── 输出报告 ──
print("=" * 60)
print("深度断链检查报告")
print("=" * 60)
print(f"扫描 md 文件（排除tools/_tools/原文件）: {md_count} 个")
print()

print(f"【1】断链: {len(broken_links)} 个")
if broken_links:
    by_file = defaultdict(list)
    for f, raw, reason in broken_links:
        by_file[f].append((raw, reason))
    for f in sorted(by_file.keys())[:20]:
        print(f"  📄 {f}")
        for raw, reason in by_file[f][:5]:
            print(f"     [[{raw}]] → {reason}")
    if len(by_file) > 20:
        print(f"  ... 还有 {len(by_file)-20} 个文件")
print()

print(f"【2】坏锚点: {len(broken_anchors)} 个")
if broken_anchors:
    by_file = defaultdict(list)
    for f, raw, tf, anchor in broken_anchors:
        by_file[f].append((raw, tf, anchor))
    for f in sorted(by_file.keys())[:20]:
        print(f"  📄 {f}")
        for raw, tf, anchor in by_file[f][:5]:
            print(f"     [[{raw}]] → 目标[{tf}]锚点[{anchor}]未找到")
    if len(by_file) > 20:
        print(f"  ... 还有 {len(by_file)-20} 个文件")
print()

print(f"【3】坏图片: {len(broken_images)} 个")
if broken_images:
    by_file = defaultdict(list)
    for f, raw, img in broken_images:
        by_file[f].append((raw, img))
    for f in sorted(by_file.keys())[:20]:
        print(f"  📄 {f}")
        for raw, img in by_file[f][:5]:
            print(f"     {raw} → 图片[{img}]未找到")
    if len(by_file) > 20:
        print(f"  ... 还有 {len(by_file)-20} 个文件")
print()

print(f"【4】mermaid问题: {len(mermaid_issues)} 个")
if mermaid_issues:
    for f, idx, issue in mermaid_issues[:20]:
        print(f"  📄 {f} 块#{idx}: {issue}")
    if len(mermaid_issues) > 20:
        print(f"  ... 还有 {len(mermaid_issues)-20} 个")
print()

total = len(broken_links) + len(broken_anchors) + len(broken_images) + len(mermaid_issues)
print(f"总计问题: {total} 个")
if total == 0:
    print("✅ 全部通过！")
