#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全库 wikilink 断链检查脚本"""
import os
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/wangpengcheng/IT/03_知识库/综合评价")

# 收集所有 md 和 svg 文件（Obsidian 会把 .svg 也当可链接目标）
all_md_files = set()
all_svg_files = set()
for p in ROOT.rglob("*"):
    if p.is_file():
        rel = p.relative_to(ROOT)
        if ".git" in rel.parts:
            continue
        if p.suffix == ".md":
            all_md_files.add(p.stem)  # 无后缀文件名
            all_md_files.add(str(rel.with_suffix("")))  # 带路径无后缀
        elif p.suffix == ".svg":
            all_svg_files.add(p.stem)
            all_svg_files.add(str(rel.with_suffix("")))

# 全局文件名索引（无路径时按文件名找）
global_index = defaultdict(list)
for p in ROOT.rglob("*.md"):
    if ".git" in p.parts:
        continue
    global_index[p.stem].append(p)

WIKILINK_RE = re.compile(r'\[\[([^\[\]]+)\]\]')

def strip_code_blocks(text):
    """去掉代码块和行内代码，避免误判示例链接"""
    # 去掉 ``` 包裹的块
    text = re.sub(r'```[\s\S]*?```', '', text)
    # 去掉行内代码 `...`
    text = re.sub(r'`[^`]*`', '', text)
    return text

broken = []
checked = 0
global_hits = 0
relative_hits = 0

for md_path in ROOT.rglob("*.md"):
    if ".git" in md_path.parts:
        continue
    rel_path = md_path.relative_to(ROOT)
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    text = strip_code_blocks(text)

    for m in WIKILINK_RE.finditer(text):
        raw = m.group(1).strip()
        checked += 1

        # 先把 Obsidian 表格里的转义竖线 \| 当作普通 | 处理
        raw_clean = raw.replace("\\|", "|")
        # 去掉显示名 | 和锚点 #
        target = raw_clean.split("|")[0].split("#")[0].strip()
        if not target:
            continue

        # 归一化：去掉 .md 后缀
        if target.endswith(".md"):
            target = target[:-3]

        # 判断是相对路径还是全局文件名
        if "/" in target or target.startswith("../") or target.startswith("./"):
            # 相对路径：基于当前文件位置解析
            resolved = (md_path.parent / target).resolve()
            # 尝试 .md 和 .svg
            if resolved.with_suffix(".md").exists() or resolved.with_suffix(".svg").exists() or resolved.exists():
                relative_hits += 1
            else:
                broken.append((str(rel_path), raw, target, "相对路径不存在"))
        else:
            # 全局文件名匹配
            if target in global_index:
                global_hits += 1
            else:
                broken.append((str(rel_path), raw, target, "全局文件名未找到"))

print(f"=== 断链检查报告 ===")
print(f"扫描 md 文件: {len(list(ROOT.rglob('*.md')))} 个")
print(f"检查 wikilink: {checked} 个")
print(f"  相对路径命中: {relative_hits}")
print(f"  全局文件名命中: {global_hits}")
print(f"  疑似断链: {len(broken)}")
print()

if broken:
    print("--- 断链清单（按文件分组）---")
    by_file = defaultdict(list)
    for src, raw, target, reason in broken:
        by_file[src].append((raw, target, reason))
    for src in sorted(by_file.keys()):
        print(f"\n📄 {src}")
        for raw, target, reason in by_file[src]:
            print(f"   [[{raw}]]  →  {reason}")
else:
    print("✅ 无断链！")
