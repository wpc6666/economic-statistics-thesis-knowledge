#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能断链修复脚本
遍历所有md文件中的wikilink，如果是相对路径且解析失败，
自动尝试增加../前缀层数，找到能正确解析的路径。
"""
import os
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/wangpengcheng/IT/03_知识库/综合评价")

# 收集所有md文件的完整路径（相对路径，无后缀）
all_md_relpaths = set()  # 如 "教材笔记/01_综合评价/README"
all_md_stems = defaultdict(list)  # stem -> [完整路径列表]

for p in ROOT.rglob("*.md"):
    if ".git" in p.parts:
        continue
    rel = p.relative_to(ROOT)
    rel_noext = str(rel.with_suffix(""))
    all_md_relpaths.add(rel_noext)
    all_md_stems[p.stem].append(rel_noext)

# 也收集svg
all_svg_relpaths = set()
for p in ROOT.rglob("*.svg"):
    if ".git" in p.parts:
        continue
    rel = p.relative_to(ROOT)
    all_svg_relpaths.add(str(rel.with_suffix("")))

WIKILINK_RE = re.compile(r'\[\[([^\[\]]+)\]\]')

def strip_code_blocks(text):
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]*`', '', text)
    return text

def try_resolve(src_file, target):
    """尝试从src_file解析target相对路径，返回正确的相对路径或None"""
    # 去掉.md后缀
    if target.endswith(".md"):
        target = target[:-3]
    if target.endswith(".svg"):
        target_noext = target[:-4]
    else:
        target_noext = target

    src_dir = src_file.parent

    # 尝试不同的上溯层数
    # 原target可能是 "教材笔记/xxx" 或 "../教材笔记/xxx"
    # 我们尝试从src_dir出发，加上0层、1层、2层...最多6层../
    parts = target.split("/")
    
    for ups in range(0, 8):
        # 构造候选路径：从src_dir上溯ups层，然后接target
        # 但要去掉target原有的../
        cleaned_parts = []
        for part in parts:
            if part == "..":
                ups += 1  # 原有的../也算上溯
            elif part == ".":
                continue
            else:
                cleaned_parts.append(part)
        
        # 从src_dir上溯ups层
        candidate_dir = src_dir
        valid = True
        for _ in range(ups):
            candidate_dir = candidate_dir.parent
        
        # 拼接候选路径
        candidate = candidate_dir.joinpath(*cleaned_parts)
        candidate_rel = candidate.resolve().relative_to(ROOT.resolve())
        
        # 检查是否存在
        candidate_str = str(candidate_rel)
        if candidate_str in all_md_relpaths:
            # 返回相对于src_file的路径
            result = os.path.relpath(candidate, src_dir)
            return result
        if candidate_str in all_svg_relpaths:
            result = os.path.relpath(candidate, src_dir)
            return result
        if (candidate.resolve().with_suffix(".md")).exists():
            result = os.path.relpath(candidate.resolve().with_suffix(".md"), src_dir)
            # 去掉.md后缀
            result = result[:-3]
            return result
        if (candidate.resolve().with_suffix(".svg")).exists():
            result = os.path.relpath(candidate.resolve().with_suffix(".svg"), src_dir)
            result = result[:-4]
            return result
        # 重置ups，不要累加
        break
    
    return None

# 上面的逻辑有问题，重写
def resolve_with_ups(src_file, target):
    """更简单的逻辑：尝试target本身，以及在前面加不同层数的../"""
    if target.endswith(".md"):
        target = target[:-3]
    if target.endswith(".svg"):
        target_noext = target[:-4]
    else:
        target_noext = target
    
    src_dir = src_file.parent
    
    # 去掉target开头的../，计算原有上溯层数
    original_ups = 0
    remaining = target
    while remaining.startswith("../"):
        original_ups += 1
        remaining = remaining[3:]
    while remaining.startswith("./"):
        remaining = remaining[2:]
    
    # 尝试从original_ups-2到original_ups+5的范围
    for ups in range(max(0, original_ups - 3), original_ups + 6):
        candidate_dir = src_dir
        valid = True
        for _ in range(ups):
            candidate_dir = candidate_dir.parent
            # 不能上溯超过ROOT
            if candidate_dir.resolve() == ROOT.resolve().parent:
                valid = False
                break
        if not valid:
            continue
        
        candidate = candidate_dir / remaining
        try:
            candidate_rel = str(candidate.resolve().relative_to(ROOT.resolve()))
        except ValueError:
            continue
        
        if candidate_rel in all_md_relpaths:
            result = os.path.relpath(candidate, src_dir)
            return result
        if candidate_rel in all_svg_relpaths:
            result = os.path.relpath(candidate, src_dir)
            return result
        if candidate.with_suffix(".md").exists():
            result = os.path.relpath(candidate.with_suffix(".md"), src_dir)
            result = result[:-3]
            return result
        if candidate.with_suffix(".svg").exists():
            result = os.path.relpath(candidate.with_suffix(".svg"), src_dir)
            result = result[:-4]
            return result
    
    return None

# 主流程
fixes = []  # (src_file, original_wikilink, old_target, new_target)
unresolved = []

for md_path in ROOT.rglob("*.md"):
    if ".git" in md_path.parts:
        continue
    
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    text_no_code = strip_code_blocks(text)
    
    # 找出所有相对路径的wikilink
    for m in WIKILINK_RE.finditer(text_no_code):
        raw = m.group(1).strip()
        raw_clean = raw.replace("\\|", "|")
        target = raw_clean.split("|")[0].split("#")[0].strip()
        
        if not target:
            continue
        if target.endswith(".md"):
            target = target[:-3]
        
        # 只处理相对路径链接
        if "/" not in target and not target.startswith("../") and not target.startswith("./"):
            # 全局文件名链接，跳过
            continue
        
        # 先检查原路径是否能解析
        original_candidate = (md_path.parent / target).resolve()
        try:
            original_rel = str(original_candidate.relative_to(ROOT.resolve()))
        except ValueError:
            original_rel = None
        
        original_ok = False
        if original_rel:
            if original_rel in all_md_relpaths or original_rel in all_svg_relpaths:
                original_ok = True
            elif original_candidate.with_suffix(".md").exists():
                original_ok = True
            elif original_candidate.with_suffix(".svg").exists():
                original_ok = True
        
        if original_ok:
            continue
        
        # 原路径断了，尝试修复
        new_target = resolve_with_ups(md_path, target)
        if new_target and new_target != target:
            fixes.append((str(md_path.relative_to(ROOT)), raw, target, new_target))
        elif not new_target:
            unresolved.append((str(md_path.relative_to(ROOT)), raw, target))

print(f"=== 断链修复报告 ===")
print(f"可自动修复: {len(fixes)}")
print(f"无法自动修复: {len(unresolved)}")
print()

# 按文件分组打印修复
by_file = defaultdict(list)
for src, raw, old_t, new_t in fixes:
    by_file[src].append((raw, old_t, new_t))

print("--- 修复明细（前50条）---")
count = 0
for src in sorted(by_file.keys()):
    for raw, old_t, new_t in by_file[src]:
        print(f"📄 {src}")
        print(f"   旧: [[{raw}]]  (target: {old_t})")
        # 构造新的显示文本
        if "|" in raw:
            display = raw.split("|", 1)[1]
            new_raw = f"{new_t}|{display}"
        else:
            new_raw = new_t
        print(f"   新: [[{new_raw}]]")
        print()
        count += 1
        if count >= 50:
            break
    if count >= 50:
        break

print()
print("--- 无法自动修复的断链（前30条）---")
for src, raw, target in unresolved[:30]:
    print(f"📄 {src}: [[{raw}]]  (target: {target})")

# 保存修复清单
import json
with open("/tmp/fixes.json", "w", encoding="utf-8") as f:
    json.dump({"fixes": fixes, "unresolved": unresolved}, f, ensure_ascii=False, indent=2)
print(f"\n修复清单已保存到 /tmp/fixes.json")
