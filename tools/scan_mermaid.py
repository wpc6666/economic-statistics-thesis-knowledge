#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描知识库下所有 md 文件中的 mermaid 代码块，统计数量、分布并探测常见语法问题。"""
import os
import re
import json
from collections import Counter, defaultdict

ROOT = "/Users/wangpengcheng/IT/02_知识库/综合评价"

# 匹配 ```mermaid ... ``` 代码块（支持可选空格）
FENCE_RE = re.compile(r"```[ \t]*mermaid[ \t]*\r?\n(.*?)```", re.DOTALL | re.IGNORECASE)

# 常见问题探测正则
PROBES = {
    "arrow_single": re.compile(r"(?<![-])-(?![>-])>?\s*[A-Za-z一-鿿]"),  # -> 单箭头
    "arrow_dash_space": re.compile(r"-\s+->"),  # - ->
    "no_direction": None,  # 单独处理
    "chinese_id_line": None,  # 单独处理
}


def extract_mermaid_blocks(md_text):
    """返回 [(start_match, code_str), ...]"""
    out = []
    for m in FENCE_RE.finditer(md_text):
        out.append(m.group(1))
    return out


def detect_issues(code):
    """对单个 mermaid 代码块做问题探测，返回问题类型列表。"""
    issues = []
    lines = code.splitlines()

    # 1. 方向声明缺失：第一行非空、非注释，且不是 flowchart/graph/Timeline/sequenceDiagram 等
    first_nonempty = ""
    for ln in lines:
        s = ln.strip()
        if s and not s.startswith("%%"):
            first_nonempty = s
            break
    if first_nonempty:
        if not re.match(
            r"^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|stateDiagram-v2|"
            r"erDiagram|journey|gantt|pie|requirementDiagram|gitGraph|C4Context|"
            r"mindmap|timeline|sankey-beta|xychart-beta|block-beta|packet-beta|architecture|quadrantChart)",
            first_nonempty,
            re.IGNORECASE,
        ):
            issues.append("no_direction_decl")

    # 2. 箭头：-> 或 - ->（但排除 --> 和 --- 和 -.-> 和 ==> 等合法箭头）
    # 合法箭头形态：-->  ---  -.->  ==>  --  o--  x--  <-->  --o  --x
    # 非法：单独 -> 或 - ->
    if re.search(r"(?<![-=:|])->(?![->])", code):
        # 排除 --> 里的 ->（前面有 -）
        if re.search(r"(?<![-\w])->(?![->])", code):
            issues.append("arrow_single_hyphen")
    if re.search(r"-\s+->", code):
        issues.append("arrow_dash_space")

    # 3. 节点 ID 用中文：行首/箭头后紧跟中文然后跟 ( [ { 等
    # 形如：中文(标签)  中文[标签]  中文{标签}
    for m in re.finditer(r"(^|\s|-->|---|-\.->|==>|<-->)", code):
        rest = code[m.end():]
        cm = re.match(r"([一-鿿]+)\s*[\(\[\{\|]", rest)
        if cm:
            issues.append("chinese_node_id")
            break

    # 4. 标签里特殊字符未加引号：节点定义形如 A(中文:内容,xxx) 或 A[中文:内容,xxx]
    # 检测 节点ID( 标签 ) 中标签含 , : （ ） 但没有被 " " 包裹
    # 简化：找 ID(...) 或 ID[...] 或 ID{...} 里标签内容含 , : 且开头不是 "
    for m in re.finditer(r"([A-Za-z][A-Za-z0-9_]*)\s*([\(\[\{])((?:[^)\]\}]|\\.)*?)([\)\]\}])", code):
        nid, op, inner, cl = m.group(1), m.group(2), m.group(3), m.group(4)
        if not inner:
            continue
        # 已经被引号包裹则跳过
        if inner.startswith('"') or inner.startswith("'"):
            continue
        # 标签里含特殊字符 , : ; （括号配对外的） 中文括号
        if re.search(r"[,;:：，。（）()【】\[\]]", inner):
            issues.append("label_needs_quote")
            break

    # 5. 双引号嵌套：标签里出现 "xxx"yyy" 这种未转义
    # 形如 A["xx"yy"zz"]
    for m in re.finditer(r'"([^"\n]*)"([^"\n\]\)]*)"', code):
        # 粗略检测：引号内还有引号
        pass
    # 更直接：找 ["...]  里内容的引号数
    for m in re.finditer(r'\[\s*"((?:[^"\\]|\\.)*)"\s*\]', code):
        inner = m.group(1)
        # 内部不能再有未转义 "
        if inner.count('"') > 0:
            issues.append("quote_nesting")
            break

    return list(dict.fromkeys(issues))  # 去重保序


def main():
    total_files = 0
    files_with_mermaid = 0
    total_blocks = 0
    issue_counter = Counter()
    issue_files = defaultdict(list)  # issue_type -> [file paths]
    block_details = []  # (file, idx, issues, preview)

    for dirpath, dirnames, filenames in os.walk(ROOT):
        # 跳过 .git .obsidian node_modules
        dirnames[:] = [d for d in dirnames if d not in (".git", ".obsidian", "node_modules", ".venv", "__pycache__")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            total_files += 1
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                print(f"[WARN] 读取失败 {fp}: {e}")
                continue
            blocks = extract_mermaid_blocks(text)
            if not blocks:
                continue
            files_with_mermaid += 1
            rel = os.path.relpath(fp, ROOT)
            for i, code in enumerate(blocks):
                total_blocks += 1
                issues = detect_issues(code)
                for it in issues:
                    issue_counter[it] += 1
                    issue_files[it].append(rel)
                if issues:
                    preview = code.strip().splitlines()[0][:60] if code.strip() else ""
                    block_details.append((rel, i, issues, preview))

    print("=" * 60)
    print(f"扫描 md 文件总数: {total_files}")
    print(f"含 mermaid 的文件数: {files_with_mermaid}")
    print(f"mermaid 代码块总数: {total_blocks}")
    print("=" * 60)
    print("问题类型统计:")
    for it, cnt in issue_counter.most_common():
        print(f"  {it}: {cnt} 块")
    print("=" * 60)
    print(f"有问题的块总数: {len(block_details)}")

    # 输出到 json 供修复脚本使用
    report = {
        "total_files": total_files,
        "files_with_mermaid": files_with_mermaid,
        "total_blocks": total_blocks,
        "issue_counter": dict(issue_counter),
        "block_details": [
            {"file": b[0], "idx": b[1], "issues": b[2], "preview": b[3]} for b in block_details
        ],
    }
    out = os.path.join(ROOT, "tools", "scan_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已写入: {out}")


if __name__ == "__main__":
    main()
