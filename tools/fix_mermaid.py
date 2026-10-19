#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 mermaid 代码块中的语法错误。
基于 mermaid 10.9.8 真实解析验证，只修复确认会报错的块。
修复规则：
  1. 节点标签 ID[...] / ID(...) / ID{...} 里含特殊字符 ()[] 但未加双引号 → 加双引号
  2. 边标签 -->|...| 里含 []() 但未加双引号 → 加双引号
  3. gantt 图误用 graph TD 开头 → 改成 gantt
  4. 行尾非法注释（中文说明跟在代码后）→ 改成 %% 注释
"""
import os
import re
import json
import subprocess
from collections import defaultdict

ROOT = "/Users/wangpengcheng/IT/03_知识库/综合评价"
CHECK_DIR = os.path.join(ROOT, "tools", "mermaid_check")

FENCE_RE = re.compile(r"(```[ \t]*mermaid[ \t]*\r?\n)(.*?)(```)", re.DOTALL | re.IGNORECASE)

# 节点形状字符对
SHAPE_PAIRS = {
    "[": "]",
    "(": ")",
    "{": "}",
}

# 标签里出现这些字符时，必须用双引号包裹（否则 mermaid 解析器会混淆）
LABEL_SPECIAL_CHARS = set('()[]{}<>,;:')


def label_needs_quotes(text: str) -> bool:
    """判断标签内容是否需要用双引号包裹。"""
    if not text:
        return False
    if text.startswith('"') or text.startswith("'"):
        return False
    # 含特殊字符就需要引号
    for ch in text:
        if ch in LABEL_SPECIAL_CHARS:
            return True
    return False


def fix_node_labels_in_line(line: str) -> tuple:
    """修复一行中的节点标签。返回 (新行, 是否修改)。"""
    original = line
    # 匹配 ID 后跟形状标签：ID[内容] / ID(内容) / ID{内容}
    # 注意：要排除已经引号包裹的 ["..."] / ("...") / {"..."}
    # 也排除边标签 -->|...|（单独处理）

    # 我们用一个逐字符扫描的状态机来处理，避免嵌套括号问题
    # 简化：用正则找 ID[ ... ] 形式，内容不含 ] 和引号
    # 模式：节点ID + 开括号 + 标签内容 + 闭括号

    def replace_node(m):
        nid = m.group(1)
        op = m.group(2)
        inner = m.group(3)
        cl = m.group(4)
        if not inner:
            return m.group(0)
        if inner.startswith('"') or inner.startswith("'"):
            return m.group(0)
        # 检查是否需要引号
        if not label_needs_quotes(inner):
            return m.group(0)
        # 加双引号（注意转义内部双引号）
        escaped = inner.replace('"', '\\"')
        return f'{nid}{op}"{escaped}"{cl}'

    # 匹配 ID[内容] — 内容不含 ] " （已引号的会被跳过）
    # 分组: (nid)([)(inner)(])
    line = re.sub(
        r'([A-Za-z][A-Za-z0-9_]*)(\[)([^"\]\n]*)(\])',
        replace_node, line
    )
    # 匹配 ID{内容} — 内容不含 } "
    # 分组: (nid)({)(inner)(})
    line = re.sub(
        r'([A-Za-z][A-Za-z0-9_]*)(\{)([^"}\n]*)(\})',
        replace_node, line
    )
    # 匹配 ID(内容) — 内容不含 ) " （但要排除函数调用如 style ID ... 等）
    # 注意：ID(内容) 是圆角矩形节点定义，只在行首或箭头后出现
    # 为安全起见，我们只匹配行首/箭头后紧跟的 ID(...)
    def replace_paren_node(m):
        prefix = m.group(1)
        nid = m.group(2)
        inner = m.group(3)
        if not inner:
            return m.group(0)
        if inner.startswith('"') or inner.startswith("'"):
            return m.group(0)
        if not label_needs_quotes(inner):
            return m.group(0)
        escaped = inner.replace('"', '\\"')
        return f'{prefix}{nid}("{escaped}")'

    line = re.sub(
        r'(^|\s|-->|---|-\.->|==>|<-->)'
        r'([A-Za-z][A-Za-z0-9_]*)\(([^")\n]*)\)',
        replace_paren_node, line
    )

    return line, line != original


def fix_edge_labels_in_line(line: str) -> tuple:
    """修复边标签 -->|...| 里的特殊字符。"""
    original = line

    def replace_edge(m):
        arrow = m.group(1)  # --> / -.-> / ==> 等
        inner = m.group(2)
        if not inner:
            return m.group(0)
        if inner.startswith('"') or inner.startswith("'"):
            return m.group(0)
        # 边标签里含 []() 或 < > 时需要引号
        needs = False
        for ch in inner:
            if ch in '[]()<>':
                needs = True
                break
        if not needs:
            return m.group(0)
        escaped = inner.replace('"', '\\"')
        return f'{arrow}|"{escaped}"|'

    # 匹配 -->|...| 或 -.->|...| 或 ==>|...| 等
    line = re.sub(
        r'(-->|-\.->|==>|-->|---|<-->|o--|x--|--o|--x)\|([^|\n]*)\|',
        replace_edge, line
    )
    return line, line != original


def fix_trailing_comment(line: str) -> tuple:
    """修复行尾非法注释：代码行后跟  ← 中文说明  → 改成 %% 注释。
    注意：只匹配 ← （左箭头），不匹配 → （右箭头，它在 mermaid 标签里是合法内容）。"""
    m = re.match(r'^(.*?[^\s])[ \t]+←[ \t]*(.+)$', line)
    if m:
        code_part = m.group(1).rstrip()
        comment_part = m.group(2).strip()
        return f'{code_part}\n    %% {comment_part}', True
    return line, False


def fix_gantt_misuse(code: str) -> tuple:
    """如果开头是 graph TD/LR 但内容是 gantt 语法，改成 gantt。"""
    lines = code.split('\n')
    if not lines:
        return code, False
    first = lines[0].strip()
    if re.match(r'^graph\s+(TD|LR|BT|RL|TB)$', first, re.IGNORECASE):
        # 检查后续是否有 gantt 特征：title xxx / section xxx / :a1, date, dur
        has_gantt_feature = False
        for ln in lines[1:10]:
            s = ln.strip()
            if s.startswith('section ') or re.search(r':\w+,\s*\d{4}-\d{2}-\d{2}', s):
                has_gantt_feature = True
                break
        if has_gantt_feature:
            lines[0] = 'gantt'
            return '\n'.join(lines), True
    return code, False


def fix_mermaid_block(code: str) -> tuple:
    """修复一个 mermaid 代码块。返回 (新代码, 是否修改, 修改类型列表)。"""
    changes = []
    original = code

    # 1. gantt 误用
    code, changed = fix_gantt_misuse(code)
    if changed:
        changes.append('gantt_direction')

    # 2. 逐行修复
    new_lines = []
    for line in code.split('\n'):
        # 跳过注释行
        stripped = line.strip()
        if stripped.startswith('%%'):
            new_lines.append(line)
            continue

        # 行尾非法注释
        line, c = fix_trailing_comment(line)
        if c:
            changes.append('trailing_comment')

        # 边标签
        line, c = fix_edge_labels_in_line(line)
        if c:
            changes.append('edge_label_quotes')

        # 节点标签
        line, c = fix_node_labels_in_line(line)
        if c:
            changes.append('node_label_quotes')

        new_lines.append(line)

    code = '\n'.join(new_lines)

    return code, code != original, list(dict.fromkeys(changes))


def main():
    # 读取真实错误列表
    with open(os.path.join(CHECK_DIR, 'real_errors.json')) as f:
        real_errors = json.load(f)

    print(f"共 {len(real_errors['errors'])} 个报错块需要修复\n")

    # 收集需要修复的文件和块索引
    file_blocks = defaultdict(list)
    for e in real_errors['errors']:
        file_blocks[e['file']].append(e['idx'])

    fixed_files = []
    total_fixes = 0
    fix_details = []

    for rel_path, block_indices in sorted(file_blocks.items()):
        fp = os.path.join(ROOT, rel_path)
        with open(fp, 'r', encoding='utf-8') as f:
            text = f.read()

        # 提取所有 mermaid 块
        blocks = list(FENCE_RE.finditer(text))
        # 逆序处理，避免位置偏移
        new_text = text
        file_changes = []

        for idx in sorted(block_indices, reverse=True):
            if idx >= len(blocks):
                continue
            m = blocks[idx]
            full_match = m.group(0)
            fence_start = m.group(1)
            code = m.group(2)
            fence_end = m.group(3)

            new_code, changed, change_types = fix_mermaid_block(code)
            if changed:
                new_full = fence_start + new_code + fence_end
                new_text = new_text[:m.start()] + new_full + new_text[m.end():]
                file_changes.append((idx, change_types, code, new_code))
                total_fixes += 1

        if file_changes:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(new_text)
            fixed_files.append(rel_path)
            for idx, ctypes, old_code, new_code in file_changes:
                fix_details.append({
                    'file': rel_path,
                    'block_idx': idx,
                    'changes': ctypes,
                })
            print(f"✅ 修复 {rel_path}:")
            for idx, ctypes, old_code, new_code in file_changes:
                print(f"   块#{idx}: {ctypes}")
                # 打印 diff 摘要
                old_lines = old_code.strip().split('\n')
                new_lines = new_code.strip().split('\n')
                for ol, nl in zip(old_lines, new_lines):
                    if ol != nl:
                        print(f"     - {ol.strip()}")
                        print(f"     + {nl.strip()}")

    print(f"\n{'='*60}")
    print(f"修复完成：{len(fixed_files)} 个文件，{total_fixes} 个块")
    print(f"{'='*60}")

    # 写修复报告
    report = {
        'fixed_files': fixed_files,
        'total_fixed_blocks': total_fixes,
        'details': fix_details,
    }
    with open(os.path.join(ROOT, 'tools', 'fix_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
