#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一知识库中所有 md 文件的图片引用路径。

- 将 Obsidian wikilink 图片 ![[name]] 改写为标准 markdown ![](相对路径)
- 校验标准 markdown 图片 ![alt](path) 的本地路径是否存在
- 跳过 http(s):// 远程 URL、data: URI
- 跳过代码块（``` 围栏 + 行内反引号）内的内容
- 不移动图片文件本身，只改 md 引用

用法：
    python3 tools/fix_image_paths.py            # 扫描 + 修复 + 报告
    python3 tools/fix_image_paths.py --dry-run  # 只扫描，不改文件
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}

# ---------- 正则 ----------
RE_WIKI_IMG = re.compile(r"!\[\[([^\]\|#]+?)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
RE_STD_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


# ---------- 工具 ----------
def iter_md_files(root: Path):
    for p in root.rglob("*.md"):
        parts = set(p.parts)
        if ".git" in parts or ".obsidian" in parts or ".trash" in parts:
            continue
        yield p


def build_image_index(root: Path):
    """构建 {文件名: [Path,...]} 索引。"""
    idx = defaultdict(list)
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMG_EXTS:
            continue
        parts = set(p.relative_to(root).parts)
        if ".git" in parts or ".obsidian" in parts:
            continue
        idx[p.name].append(p.resolve())
    return idx


def strip_code_spans(line: str) -> str:
    """把行内反引号内容替换成等长空格，避免误匹配代码里的示例。"""
    out = []
    in_backtick = False
    for ch in line:
        if ch == "`":
            in_backtick = not in_backtick
            out.append(" ")
        elif in_backtick:
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def in_fenced_block(lines, i):
    """判断第 i 行（0-based）是否在 ``` 围栏代码块内。"""
    # 简单状态机：从开头扫到 i
    inside = False
    fence_marker = None
    for j in range(i + 1):
        s = lines[j].lstrip()
        if not inside:
            if s.startswith("```") or s.startswith("~~~"):
                inside = True
                fence_marker = s[:3]
        else:
            if s.startswith(fence_marker):
                inside = False
                fence_marker = None
    return inside


def resolve_wiki_target(md_path: Path, img_name: str, img_index: dict):
    """根据 md 文件位置，为 wikilink 图片名挑最合适的实际文件。
    优先级：同目录 > 同子树深度最近 > 路径最短。
    返回绝对路径或 None。
    """
    candidates = img_index.get(img_name, [])
    if not candidates:
        return None
    md_abs = md_path.resolve()
    md_dir = md_abs.parent

    # 1) 同目录
    same_dir = [c for c in candidates if c.parent == md_dir]
    if same_dir:
        return same_dir[0]

    # 2) 距离最近（按相对路径的目录数）
    def dist(c: Path):
        try:
            rel = os_path_rel(md_dir, c.parent)
            return (rel.count("/"), len(rel))
        except ValueError:
            return (99, 999)

    candidates_sorted = sorted(candidates, key=dist)
    return candidates_sorted[0]


def os_path_rel(base: Path, target: Path) -> str:
    """跨盘符也不抛异常地算相对路径。"""
    import os
    return os.path.relpath(target, base)


def rel_from_md(md_path: Path, target_abs: Path) -> str:
    """计算从 md 文件所在目录到 target 的相对路径，用 / 分隔。"""
    rel = os_path_rel(md_path.parent.resolve(), target_abs)
    return rel.replace("\\", "/")


# ---------- 主流程 ----------
def main():
    dry_run = "--dry-run" in sys.argv

    img_index = build_image_index(ROOT)
    md_files = list(iter_md_files(ROOT))

    total_refs = 0
    wiki_fixed = 0          # wikilink → std 修复数
    path_corrected = 0      # std 引用路径修正数
    missing = []            # [(md_rel, ref_path, reason)]
    already_ok = 0
    remote_skipped = 0
    codeblock_skipped = 0

    changed_files = []

    for md in md_files:
        text = md.read_text(encoding="utf-8")
        lines = text.split("\n")
        new_lines = list(lines)
        file_changed = False

        # ---- wikilink 图片 ----
        for i, line in enumerate(lines):
            if in_fenced_block(lines, i):
                # 围栏内全部跳过
                continue
            cleaned = strip_code_spans(line)
            for m in RE_WIKI_IMG.finditer(cleaned):
                total_refs += 1
                img_name = m.group(1).strip()
                target = resolve_wiki_target(md, img_name, img_index)
                if target is None:
                    missing.append((str(md.relative_to(ROOT)), img_name, "wikilink 未找到文件"))
                    continue
                new_rel = rel_from_md(md, target)
                old = m.group(0)
                # 提取 alt：wikilink 默认无 alt
                alt = ""
                new = f"![{alt}]({new_rel})"
                if new != old:
                    new_lines[i] = new_lines[i].replace(old, new, 1)
                    wiki_fixed += 1
                    file_changed = True

        # ---- 标准 markdown 图片 ----
        # 重新读改写后的行
        text2 = "\n".join(new_lines)
        lines2 = text2.split("\n")
        for i, line in enumerate(lines2):
            if in_fenced_block(lines2, i):
                continue
            cleaned = strip_code_spans(line)
            for m in RE_STD_IMG.finditer(cleaned):
                total_refs += 1
                alt = m.group(1)
                ref = m.group(2).strip()
                # 远程 / data URI
                if re.match(r"^(https?:|data:|mailto:)", ref):
                    remote_skipped += 1
                    continue
                # 去掉锚点 / 查询
                ref_path = ref.split("#", 1)[0].split("?", 1)[0]
                target = (md.parent / ref_path).resolve()
                if target.exists():
                    already_ok += 1
                else:
                    # 尝试在 vault 里按 basename 找
                    base = Path(ref_path).name
                    cands = img_index.get(base, [])
                    # 排除自身目录不存在的情况
                    cands = [c for c in cands if c != target]
                    if cands:
                        # 挑最近
                        best = resolve_wiki_target(md, base, img_index)
                        new_rel = rel_from_md(md, best)
                        old = m.group(0)
                        new = f"![{alt}]({new_rel})"
                        new_lines[i] = new_lines[i].replace(old, new, 1)
                        path_corrected += 1
                        file_changed = True
                    else:
                        missing.append((str(md.relative_to(ROOT)), ref, "本地文件不存在"))

        if file_changed:
            changed_files.append(md)
            if not dry_run:
                md.write_text("\n".join(new_lines), encoding="utf-8")

    # ---------- 报告 ----------
    print("=" * 60)
    print(f"扫描 md 文件数      : {len(md_files)}")
    print(f"图片引用总数        : {total_refs}")
    print(f"  - wikilink 修复   : {wiki_fixed}")
    print(f"  - 路径修正        : {path_corrected}")
    print(f"  - 原本正常        : {already_ok}")
    print(f"  - 远程 URL 跳过   : {remote_skipped}")
    print(f"  - 代码块内跳过    : {codeblock_skipped}")
    print(f"  - 缺失图片        : {len(missing)}")
    print("=" * 60)

    if changed_files:
        print(f"\n修改的文件 ({len(changed_files)}):")
        for p in changed_files:
            print(f"  - {p.relative_to(ROOT)}")

    if missing:
        print(f"\n缺失图片清单:")
        for md_rel, ref, reason in missing:
            print(f"  - [{md_rel}] -> {ref}   ({reason})")

    if dry_run:
        print("\n[dry-run] 未写盘。去掉 --dry-run 实际执行。")


if __name__ == "__main__":
    main()
