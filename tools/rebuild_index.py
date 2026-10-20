#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建 file-tree.json（目录树）和 00_索引.md（AI检索用结构化索引）"""
import json
import os
from pathlib import Path

ROOT = Path("/Users/wangpengcheng/IT/03_知识库/综合评价")

EXCLUDE_DIRS = {".git", ".obsidian", ".github", ".DS_Store", "__pycache__", "tools", "_tools", "node_modules"}
EXCLUDE_FILES = {".DS_Store", ".gitignore", "00_学习导航.md", "00_总索引与学习规划.md", "00_质量检测报告.md", "exam.html.bak"}

# ========== 1. 重建 file-tree.json ==========
def build_tree(dir_path: Path):
    tree = {}
    entries = sorted(os.listdir(dir_path), key=lambda x: (not (dir_path / x).is_dir(), x))
    for name in entries:
        if name in EXCLUDE_DIRS or name in EXCLUDE_FILES or name.startswith("."):
            continue
        p = dir_path / name
        if p.is_dir():
            subtree = build_tree(p)
            if subtree:
                tree[name] = subtree
        else:
            tree[name] = None
    return tree

tree = build_tree(ROOT)
(ROOT / "file-tree.json").write_text(
    json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✓ file-tree.json 已重建，顶层 {len(tree)} 项")

# ========== 2. 生成 00_索引.md ==========
lines = []
A = lines.append
A("# 00 索引 · AI 快速检索用")
A("")
A("> 本文件由 tools/rebuild_index.py 自动生成，勿手工编辑。")
A("> 用途：AI 快速定位知识库内任意课程、章节、KP 文件、真题集、模拟卷。")
A(f"> 生成时间基准：实际文件系统扫描。")
A("")
A("## 一、根目录入口文件")
A("")
for f in ["README.md", "00_总导航.md", "00_互链映射规范.md", "00_索引.md"]:
    if (ROOT / f).exists():
        A(f"- `{f}`")
A("- 已过时（勿作入口）：00_学习导航.md / 00_总索引与学习规划.md / 00_质量检测报告.md")
A("")

# 课程列表（教材笔记/*/ 与 经济统计学论文从0基础到精通/*/）
def list_chapters(course_dir: Path):
    return sorted([d.name for d in course_dir.iterdir()
                   if d.is_dir() and d.name not in EXCLUDE_DIRS and not d.name.startswith(".")
                   and d.name != "assets" and d.name != "_tools"])

COURSES = [
    ("教材笔记/01_综合评价", "01 综合评价"),
    ("教材笔记/02_计量经济学", "02 计量经济学"),
    ("教材笔记/03_时间序列", "03 时间序列"),
    ("教材笔记/04_多元统计", "04 多元统计"),
    ("教材笔记/05_统计学原理", "05 统计学原理"),
    ("教材笔记/06_西方经济学", "06 西方经济学"),
    ("教材笔记/07_政治经济学", "07 政治经济学"),
]

A("## 二、教材笔记 · 七门课程及章节入口")
A("")
for rel_dir, title in COURSES:
    cd = ROOT / rel_dir
    readme = f"{rel_dir}/README.md" if (cd / "README.md").exists() else None
    A(f"### {title}（`{rel_dir}/`）")
    if readme:
        A(f"- 课程入口：`{readme}`")
    A("")
    for ch in list_chapters(cd):
        chd = cd / ch
        # 找章节入口
        entry = None
        for cand in ["README.md", "00_章节总结.md"]:
            if (chd / cand).exists():
                entry = f"{rel_dir}/{ch}/{cand}"
                break
        kp_dir = chd / "知识点"
        kp_count = len(list(kp_dir.glob("KP*.md"))) if kp_dir.is_dir() else 0
        zhenti = "考研真题集.md" if (chd / "考研真题集.md").exists() else None
        bits = [f"- `{ch}/`"]
        if entry:
            bits.append(f"入口 `{entry}`")
        if kp_count:
            bits.append(f"{kp_count} 个KP")
        if zhenti:
            bits.append(f"真题集 `{rel_dir}/{ch}/考研真题集.md`")
        A("　".join(bits))
    A("")

A("## 三、经济统计学论文从0基础到精通（教程）")
A("")
tut = ROOT / "经济统计学论文从0基础到精通"
A(f"- 教程入口：`经济统计学论文从0基础到精通/README.md`")
for ch in list_chapters(tut):
    chd = tut / ch
    entry = None
    for cand in ["README.md", "00_章节总结.md"]:
        if (chd / cand).exists():
            entry = f"经济统计学论文从0基础到精通/{ch}/{cand}"
            break
    bits = [f"- `{ch}/`"]
    if entry:
        bits.append(f"入口 `{entry}`")
    A("　".join(bits))
A("")

A("## 四、KP 文件完整路径清单（按课程/章节分组）")
A("")
for rel_dir, title in COURSES:
    cd = ROOT / rel_dir
    A(f"### {title}")
    for ch in list_chapters(cd):
        kp_dir = cd / ch / "知识点"
        if not kp_dir.is_dir():
            continue
        kps = sorted(kp_dir.glob("*.md"))
        if not kps:
            continue
        A(f"- **{ch}/知识点/**：")
        for kp in kps:
            A(f"  - `{rel_dir}/{ch}/知识点/{kp.name}`")
    A("")

A("## 五、真题集与模拟卷位置")
A("")
A("### 模拟卷（首经贸801）")
A("")
A("- 目录：`教材笔记/模拟卷/`")
for f in sorted((ROOT / "教材笔记/模拟卷").glob("*.md")):
    A(f"  - `教材笔记/模拟卷/{f.name}`")
A("- 大纲与答题技巧：`教材笔记/首经贸801大纲解读与答题技巧.md`")
A("- 出题模板：`教材笔记/出题模板规范_首经贸801.md`")
A("")
A("### 各章考研真题集（教材笔记/06 西方经济学、07 政治经济学为主）")
A("")
for zt in sorted((ROOT / "教材笔记").rglob("考研真题集.md")):
    A(f"- `{zt.relative_to(ROOT)}`")
A("")

A("## 六、其他资源")
A("")
A("- `原文件/`：原始 PDF 转写与补充资料（含贝塞尔修正 PDF 等）")
A("- `assets/`：根目录共享图片/导图")
A("- `tools/`：维护脚本（check_links.py / fix_links.py / fix_remaining_links.py / fix_remaining_links2.py / rebuild_index.py / build_exam_data.py）")
A("")

(ROOT / "00_索引.md").write_text("\n".join(lines), encoding="utf-8")
print(f"✓ 00_索引.md 已生成，{len(lines)} 行")
