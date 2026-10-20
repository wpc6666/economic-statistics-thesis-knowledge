#!/usr/bin/env python3
"""扫描知识库所有 wiki 链接，输出断链列表。支持 Obsidian 短链接。"""
import os
import re
from pathlib import Path

ROOT = Path("/Users/wangpengcheng/IT/02_知识库/综合评价")

WIKI_LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')

# 预建文件名索引：{文件名(不含.md): [完整路径列表]}
filename_index = {}
for md in ROOT.rglob("*.md"):
    if '_tools' in md.parts:
        continue
    name = md.stem  # 不含 .md
    filename_index.setdefault(name, []).append(md)

def resolve_link(source_file: Path, raw_target: str) -> Path | None:
    """根据源文件位置解析目标路径。返回 None 表示跳过。"""
    target = raw_target.strip().rstrip('\\').strip()
    # 去掉显示文本（\| 是转义管道符）
    if '\\|' in target:
        target = target.split('\\|')[0].strip()
    elif '|' in target:
        target = target.split('|')[0].strip()
    # 去掉锚点
    if '#' in target:
        target = target.split('#')[0].strip()
    if not target:
        return None
    if target.startswith(('http://', 'https://', 'mailto:')):
        return None
    target = target.lstrip('./')

    # 判断是根路径、相对路径还是纯文件名
    top_dirs = ('教材笔记/', '经济统计学论文从0基础到精通/', '原文件/', 'assets/')

    # 情况1：带路径分隔符 → 按相对/绝对路径解析
    if '/' in target:
        if target.startswith(top_dirs):
            resolved = (ROOT / target).resolve()
        else:
            resolved = (source_file.parent / target).resolve()
        # 尝试补 .md
        if not resolved.exists():
            with_md = resolved.with_suffix('.md')
            if with_md.exists():
                return with_md
            if resolved.is_dir():
                readme = resolved / 'README.md'
                if readme.exists():
                    return readme
        return resolved

    # 情况2：纯文件名（Obsidian 短链接）→ 全局搜索
    else:
        name = target
        if name in filename_index:
            candidates = filename_index[name]
            # 优先选和源文件同目录或同子树的
            for c in candidates:
                if source_file.parent in c.parents or c.parent == source_file.parent:
                    return c
            return candidates[0]
        return (source_file.parent / target).resolve()  # 返回不存在路径

def main():
    broken = []
    checked = 0

    for md_file in ROOT.rglob("*.md"):
        if '_tools' in md_file.parts:
            continue
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception:
            continue

        for match in WIKI_LINK_RE.finditer(content):
            raw = match.group(1)
            resolved = resolve_link(md_file, raw)
            if resolved is None:
                continue
            checked += 1
            if not resolved.exists():
                rel_source = md_file.relative_to(ROOT)
                clean_target = raw.split('\\|')[0].strip().rstrip('\\').strip()
                if '|' in clean_target:
                    clean_target = clean_target.split('|')[0].strip()
                broken.append((str(rel_source), clean_target))

    print(f"共检查 {checked} 个内部链接")
    print(f"发现 {len(broken)} 个断链\n")
    for src, target in broken[:30]:
        print(f"  {src}: [[{target}]]")
    if len(broken) > 30:
        print(f"... 还有 {len(broken)-30} 个")

if __name__ == '__main__':
    main()
