#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全库锚点完整性检查：
1. 收集每个 md 文件里定义的锚点：{#xxx} 自定义锚点 + 标题（slug 化）
2. 收集所有引用：[[file#anchor]]、[...](#anchor)
3. 报告断锚（定义不存在的引用）
"""
import os
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path("/Users/wangpengcheng/IT/02_知识库/综合评价")

# ---------- slugify（与 index.html 的 slugify 近似）----------
def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s

# ---------- 1) 收集所有 md 文件路径（与前端 pathSet 等价）----------
SKIP_PARTS = {".git", "node_modules", "_tools", "tools"}
md_rel_paths = set()
for p in ROOT.rglob("*.md"):
    if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
        continue
    md_rel_paths.add(str(p.relative_to(ROOT)).replace(os.sep, "/"))

# ---------- 2) 为每个文件收集锚点定义 ----------
# anchors[rel_path] = set of anchor names that exist in that file
anchors = {}  # rel_path -> set[str]
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
CUSTOM_ID_RE = re.compile(r"\{#([^}]+)\}")

for rel in md_rel_paths:
    fp = ROOT / rel
    if any(part in SKIP_PARTS for part in Path(rel).parts):
        continue
    text = fp.read_text(encoding="utf-8", errors="ignore")
    # 去掉代码块
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]*`", "", text)
    a_set = set()
    for m in HEADING_RE.finditer(text):
        title = m.group(2).strip()
        # 去掉 {#xxx} 后再 slug
        cm = CUSTOM_ID_RE.search(title)
        if cm:
            custom = cm.group(1)
            a_set.add(custom)  # 自定义 id 直接可用
            title_clean = CUSTOM_ID_RE.sub("", title).strip()
        else:
            title_clean = title
        a_set.add(slugify(title_clean))
        a_set.add(title_clean)  # 原文也存一份
    anchors[rel] = a_set

# ---------- 3) 收集所有锚点引用并检查 ----------
WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")
INLINE_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

broken_refs = []
checked = 0

def resolve_target(src_rel: str, target: str) -> str | None:
    """把 wikilink 目标（无锚点）解析成相对 ROOT 的路径"""
    target = target.strip()
    if target.endswith(".md"):
        target = target[:-3]
    if "/" in target:
        # 相对路径
        base_dir = (ROOT / src_rel).parent
        cand = (base_dir / target).resolve()
        if not str(cand).startswith(str(ROOT)):
            return None
        rel = str(cand.relative_to(ROOT))
        if rel in md_rel_paths:
            return rel
        # 可能没加 .md
        if rel + ".md" in md_rel_paths:
            return rel + ".md"
        return None
    else:
        # 全局 basename
        stem = Path(target).stem
        for rel in md_rel_paths:
            if Path(rel).stem == stem:
                return rel
        return None

for rel in md_rel_paths:
    fp = ROOT / rel
    if any(part in SKIP_PARTS for part in Path(rel).parts):
        continue
    text = fp.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]*`", "", text)

    # wikilink: [[target#anchor|display]]
    for m in WIKILINK_RE.finditer(text):
        raw = m.group(1).strip()
        raw = raw.replace("\\|", "|")
        target_part = raw.split("|")[0].strip()
        if "#" not in target_part:
            continue
        t, anc = target_part.split("#", 1)
        t = t.strip()
        anc = anc.strip()
        if not t or not anc:
            continue
        checked += 1
        resolved = resolve_target(rel, t)
        if not resolved:
            broken_refs.append((rel, f"[[{target_part}]]", "目标文件不存在"))
            continue
        if anc.startswith("^"):
            # 块 ID 难检查，跳过
            continue
        # 检查锚点是否在目标文件中
        if anc not in anchors.get(resolved, set()) and slugify(anc) not in anchors.get(resolved, set()):
            broken_refs.append((rel, f"[[{target_part}]]", f"目标 {resolved} 中无锚点 {anc!r}"))

    # 页内链接: [...](#anchor) 或 [...](file.md#anchor)
    for m in INLINE_LINK_RE.finditer(text):
        href = m.group(2).strip()
        if "#" not in href:
            continue
        if href.startswith("http://") or href.startswith("https://"):
            continue
        # 去掉可能的 URL 编码
        href = unquote(href)
        file_part, anc = href.split("#", 1)
        anc = anc.strip()
        if not anc:
            continue
        checked += 1
        if not file_part:
            # 页内锚点
            if anc not in anchors.get(rel, set()) and slugify(anc) not in anchors.get(rel, set()):
                broken_refs.append((rel, f"[{m.group(1)}](#{anc})", f"本文件中无锚点 {anc!r}"))
        else:
            # 跨文件链接
            if not file_part.endswith(".md"):
                continue  # 图片等，跳过
            resolved = resolve_target(rel, file_part)
            if not resolved:
                broken_refs.append((rel, f"[{m.group(1)}]({href})", "目标文件不存在"))
                continue
            if anc.startswith("^"):
                continue
            if anc not in anchors.get(resolved, set()) and slugify(anc) not in anchors.get(resolved, set()):
                broken_refs.append((rel, f"[{m.group(1)}]({href})", f"目标 {resolved} 中无锚点 {anc!r}"))

print(f"=== 锚点完整性检查 ===")
print(f"扫描文件: {len(md_rel_paths)}")
print(f"检查锚点引用: {checked}")
print(f"断锚数: {len(broken_refs)}")
print()
if broken_refs:
    from collections import defaultdict
    by_file = defaultdict(list)
    for src, raw, reason in broken_refs:
        by_file[src].append((raw, reason))
    for src in sorted(by_file.keys())[:50]:
        print(f"📄 {src}")
        for raw, reason in by_file[src]:
            print(f"   {raw}  →  {reason}")
    if len(by_file) > 50:
        print(f"\n... 还有 {len(by_file) - 50} 个文件")
else:
    print("✅ 所有锚点引用都能命中定义！")
