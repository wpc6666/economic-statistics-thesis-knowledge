#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量给教材笔记/ 和 经济统计学论文从0基础到精通/ 下的 .md 文件
在第一个 # 标题后插入"📝 开始做题"按钮（链接到 exam.html）。
相对路径按文件位置自动计算。
幂等：已插入过的文件自动跳过。
"""
import os
import re

ROOT = '/Users/wangpengcheng/IT/02_知识库/综合评价'
SCAN_DIRS = ['教材笔记', '经济统计学论文从0基础到精通']
EXCLUDE_NAMES = {'README.md', '00_章节总结.md'}
BUTTON_MARKER = '开始做题'  # 幂等标记

def make_button(href):
    """生成按钮 HTML 片段"""
    return (
        '<div style="text-align:right;margin:10px 0;">'
        f'<a href="{href}" target="_blank" '
        'style="display:inline-block;padding:6px 16px;background:#2563eb;'
        'color:#fff;border-radius:6px;text-decoration:none;font-size:14px;">'
        '📝 开始做题</a></div>'
    )

def process_file(filepath):
    """处理单个 md 文件，返回 (是否修改, 原因)"""
    rel = os.path.relpath(filepath, ROOT)
    filename = os.path.basename(filepath)

    if filename in EXCLUDE_NAMES:
        return False, '排除名单'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 幂等：已插入过就跳过
    if BUTTON_MARKER in content:
        return False, '已存在按钮'

    lines = content.split('\n')

    # 找第一个 # 一级标题行（注意排除 ## 和 # 后面不是空格的情况）
    title_idx = -1
    for i, line in enumerate(lines):
        # 严格匹配一级标题：行首 # 后跟空格
        if re.match(r'^#\s+\S', line):
            title_idx = i
            break

    if title_idx == -1:
        return False, '无一级标题'

    # 计算相对路径：从文件所在目录到根目录的 exam.html
    file_dir = os.path.dirname(filepath)
    rel_href = os.path.relpath(os.path.join(ROOT, 'exam.html'), start=file_dir)
    # 规范化为 unix 风格
    rel_href = rel_href.replace(os.sep, '/')

    button_html = make_button(rel_href)

    # 在一级标题行后插入：空行 + 按钮 + 空行
    new_lines = lines[:title_idx + 1] + ['', button_html, ''] + lines[title_idx + 1:]
    new_content = '\n'.join(new_lines)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True, f'已插入（href={rel_href}）'

def main():
    modified = 0
    skipped = 0
    errors = 0

    for scan_dir in SCAN_DIRS:
        base = os.path.join(ROOT, scan_dir)
        if not os.path.isdir(base):
            print(f'⚠️ 目录不存在: {base}')
            continue

        for dirpath, dirnames, filenames in os.walk(base):
            for fn in filenames:
                if not fn.endswith('.md'):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    changed, msg = process_file(fp)
                    rel = os.path.relpath(fp, ROOT)
                    if changed:
                        modified += 1
                        print(f'✓ {rel}: {msg}')
                    else:
                        skipped += 1
                except Exception as e:
                    errors += 1
                    print(f'✗ {fp}: {e}')

    print(f'\n=== 完成 ===')
    print(f'修改: {modified} 个文件')
    print(f'跳过: {skipped} 个文件')
    print(f'错误: {errors} 个文件')

if __name__ == '__main__':
    main()
