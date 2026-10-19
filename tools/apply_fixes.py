#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""应用断链修复到文件"""
import json
import re
from pathlib import Path

ROOT = Path("/Users/wangpengcheng/IT/03_知识库/综合评价")

with open("/tmp/fixes.json", "r", encoding="utf-8") as f:
    data = json.load(f)

fixes = data["fixes"]

# 按文件分组
from collections import defaultdict
by_file = defaultdict(list)
for src, raw, old_t, new_t in fixes:
    by_file[src].append((raw, old_t, new_t))

total_fixed = 0
for src_rel, items in by_file.items():
    fpath = ROOT / src_rel
    text = fpath.read_text(encoding="utf-8", errors="ignore")
    original_text = text
    
    for raw, old_t, new_t in items:
        # 构造旧wikilink和新wikilink
        # raw 格式可能是 "old_target|display"
        if "|" in raw:
            parts = raw.split("|", 1)
            display = parts[1]
            old_wikilink = f"[[{raw}]]"
            new_wikilink = f"[[{new_t}|{display}]]"
        else:
            old_wikilink = f"[[{raw}]]"
            new_wikilink = f"[[{new_t}]]"
        
        if old_wikilink in text:
            text = text.replace(old_wikilink, new_wikilink)
            total_fixed += 1
        else:
            # 可能有转义字符，尝试模糊匹配
            pass
    
    if text != original_text:
        fpath.write_text(text, encoding="utf-8")

print(f"=== 修复完成 ===")
print(f"修改文件数: {len(by_file)}")
print(f"实际替换链接数: {total_fixed}")
