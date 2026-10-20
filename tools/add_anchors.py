#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量给 KP 文件的"原书原文"链接加精确锚点，并在原书对应位置加反向链接。
"""
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/wangpengcheng/IT/03_知识库/综合评价")

# ── 工具：中文数字转阿拉伯 ──
CN_NUM = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,
          '十':10,'两':2}
def cn2int(s):
    """支持 '一' '四' '十三' '二十' 等"""
    if not s: return None
    if s.isdigit(): return int(s)
    if s == '十': return 10
    if '十' in s:
        parts = s.split('十')
        tens = CN_NUM.get(parts[0], 1) if parts[0] else 1
        ones = CN_NUM.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
        return tens * 10 + ones
    if s in CN_NUM: return CN_NUM[s]
    return None

# ── 解析原书标题索引 ──
def index_book(book_path):
    """返回 [(行号, 级别, 标题文本, 完整标题), ...]"""
    if not book_path.exists():
        print(f"  ⚠️ 原书不存在: {book_path}")
        return []
    lines = book_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    headings = []
    for i, line in enumerate(lines):
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headings.append((i, level, text))
    return headings

def find_chapter_section(headings, chapter_cn, section_cn=None, book_key=None):
    """在标题列表里找章和节。
    支持:
    - 西经/政经: '## 第X章 ...' / '## 导论' / '## 第X节 ...'
    - 计量: '## 4. 一元线性回归' / '## 4.1 ...'
    - 多元: '## 4.1 ...' / '## 4.1.1 ...'
    """
    ch_num = cn2int(chapter_cn) if chapter_cn else None

    # 中文数字映射
    cn_chapter_map = {1:'一',2:'二',3:'三',4:'四',5:'五',6:'六',7:'七',8:'八',9:'九',10:'十',
                      11:'十一',12:'十二',13:'十三',14:'十四',15:'十五',16:'十六',17:'十七',18:'十八'}

    ch_idx = None
    for i, (ln, lv, txt) in enumerate(headings):
        if lv > 2:
            continue
        # 西经: 第X章
        if chapter_cn and f"第{chapter_cn}章" in txt:
            ch_idx = i
            break
        # 导论/绪论
        if chapter_cn in ('导论', '绪论') and chapter_cn in txt:
            ch_idx = i
            break
        # 统计原书: "## 第九章"（数字转中文）
        if ch_num is not None and ch_num in cn_chapter_map:
            cn_ch = cn_chapter_map[ch_num]
            if f"第{cn_ch}章" in txt:
                ch_idx = i
                break
        # 计量: '## 4. XXX' 或 '## 4．XXX'
        if ch_num is not None:
            m = re.match(rf'^{ch_num}[\.．、]\s*\S', txt)
            if m and lv == 2:
                ch_idx = i
                break

    if ch_idx is None:
        return None, None

    if section_cn is None:
        ln, lv, txt = headings[ch_idx]
        return txt, ch_idx

    # 在章之后找节
    sec_num = cn2int(section_cn) if section_cn else None
    cn_sec_map = {1:'一',2:'二',3:'三',4:'四',5:'五',6:'六',7:'七',8:'八',9:'九',10:'十'}
    sec_cn = cn_sec_map.get(sec_num, section_cn) if sec_num else section_cn

    for j in range(ch_idx + 1, len(headings)):
        ln, lv, txt = headings[j]
        # 到下一章就停
        if lv <= 2:
            if chapter_cn and f"第{chapter_cn}章" not in txt and '章' in txt:
                break
            if ch_num is not None:
                m_next = re.match(rf'^(\d+)[\.．、]\s*\S', txt)
                if m_next and lv == 2:
                    next_num = int(m_next.group(1))
                    if next_num != ch_num:
                        break
        # 西经节: 第X节（支持中文数字和阿拉伯数字转换）
        if sec_cn and f"第{sec_cn}节" in txt:
            return txt, j
        # 计量节: '## 4.1 XXX'
        if ch_num is not None and sec_num is not None:
            m = re.match(rf'^{ch_num}\.{sec_num}[\.．\s]', txt)
            if m:
                return txt, j

    # 没找到节，返回章
    ln, lv, txt = headings[ch_idx]
    return txt, ch_idx

# ── 主流程 ──
def main():
    # 1) 建立所有 KP 文件索引
    kp_files = list(ROOT.rglob("KP*.md"))
    print(f"KP 文件总数: {len(kp_files)}")

    # 2) 原书文件
    books = {
        "upper": ROOT / "原文件/经济学/西方经济学上册_微观_全书.md",
        "lower": ROOT / "原文件/经济学/西方经济学下册_宏观_全书.md",
        "zz":    ROOT / "原文件/经济学/马克思主义政治经济学概论_全书.md",
        "jl":    ROOT / "原文件/计量经济学/陈强_计量经济学及Stata应用_全书.md",
        "dy":    ROOT / "原文件/多元统计分析/何晓群_多元统计分析_全书.md",
        "tj":    ROOT / "原文件/统计学原理/韩兆洲_统计学原理第7版_全书.md",
        "zh":    ROOT / "原文件/综合评价/陈正伟_综合评价技术及应用_全书.md",
    }
    book_index = {k: index_book(v) for k, v in books.items()}

    # 3) 扫描每个 KP 文件，找"原书原文"链接
    wiki_re = re.compile(r'\[\[([^\]]+)\]\]')
    fixed = 0
    skipped = 0
    reverse_links = defaultdict(list)  # book_rel -> [(line_idx, anchor, kp_path, label)]

    for kp in kp_files:
        text = kp.read_text(encoding="utf-8", errors="ignore")
        new_text = text
        modified = False

        for m in wiki_re.finditer(text):
            raw = m.group(1)
            parts = raw.split('|')
            target = parts[0].strip()
            label = parts[1].strip() if len(parts) > 1 else target

            # 只处理"原书原文"链接（target 含"原文件/"）
            if "原文件/" not in target:
                continue

            # 已经有锚点的跳过
            if '#' in target:
                skipped += 1
                continue

            # 从 label 提取 章/节
            # 模式1: "原书·导论第四节" / "原书·第四章第三节"
            # 模式2: "《西方经济学》下册 第十四章"
            # 模式3: "《概论》第四章"
            # 模式4: "陈强《计量经济学》第5章" / "第4-5章"

            # 导论/绪论特殊处理
            if ('导论' in label or '绪论' in label) and '第' not in label:
                chapter_cn = '导论' if '导论' in label else '绪论'
                section_cn = None
            elif ('导论' in label or '绪论' in label) and '第' in label:
                chapter_cn = '导论' if '导论' in label else '绪论'
                sec_m = re.search(r'第([一二三四五六七八九十百\d]+)节', label)
                section_cn = sec_m.group(1) if sec_m else None
            else:
                # 处理 "第4-5章" → 取4
                ch_m = re.search(r'第([一二三四五六七八九十百\d]+)(?:-[一二三四五六七八九十百\d]+)?章', label)
                sec_m = re.search(r'第([一二三四五六七八九十百\d]+)节', label)
                chapter_cn = ch_m.group(1) if ch_m else None
                section_cn = sec_m.group(1) if sec_m else None

                # 韩兆洲教材·9.2节 / 9.1节 格式
                if not chapter_cn:
                    m2 = re.search(r'(\d+)\.(\d+)\s*节', label)
                    if m2:
                        chapter_cn = m2.group(1)
                        section_cn = m2.group(2)

            if not chapter_cn:
                continue

            # 判断用哪本书
            book_key = None
            if "上册" in label or "原书·" in label:
                # 上册微观
                book_key = "upper"
            elif "下册" in label:
                book_key = "lower"
            elif "概论" in label or "政治经济学" in label:
                book_key = "zz"
            elif "计量" in label:
                book_key = "jl"
            elif "多元" in label or "何晓群" in label:
                book_key = "dy"
            elif "统计" in label or "韩兆洲" in label:
                book_key = "tj"
            elif "综合评价" in label or "陈正伟" in label:
                book_key = "zh"
            else:
                # 从 target 路径判断
                if "上册" in target: book_key = "upper"
                elif "下册" in target: book_key = "lower"
                elif "政治经济学" in target: book_key = "zz"
                elif "计量" in target: book_key = "jl"
                elif "多元" in target: book_key = "dy"
                elif "统计" in target: book_key = "tj"
                elif "综合评价" in target: book_key = "zh"

            if not book_key:
                continue

            headings = book_index.get(book_key, [])
            if not headings:
                continue

            anchor_text, hidx = find_chapter_section(headings, chapter_cn, section_cn)
            if not anchor_text:
                continue

            # 锚点文本（Obsidian 用标题原文）
            # 新链接: [[target#anchor|label]]
            new_target = f"{target}#{anchor_text}"
            old_link = f"[[{raw}]]"
            new_link = f"[[{new_target}|{label}]]"

            new_text = new_text.replace(old_link, new_link, 1)
            modified = True
            fixed += 1

            # 记录反向链接信息
            book_path = books[book_key]
            book_rel = str(book_path.relative_to(ROOT))
            kp_rel = str(kp.relative_to(ROOT))
            reverse_links[book_rel].append((hidx, anchor_text, kp_rel, kp.stem))

        if modified:
            kp.write_text(new_text, encoding="utf-8")

    print(f"\n✅ 已加锚点: {fixed} 个链接")
    print(f"⏭️  已有锚点跳过: {skipped} 个")

    # 4) 在原书对应标题后加反向链接
    print(f"\n=== 给原书加反向链接 ===")
    for book_rel, entries in reverse_links.items():
        book_path = ROOT / book_rel
        lines = book_path.read_text(encoding="utf-8").splitlines()

        # 按行号降序插入（避免行号偏移）
        entries_sorted = sorted(entries, key=lambda x: -x[0])
        inserted = 0
        for hidx, anchor, kp_rel, kp_stem in entries_sorted:
            # 在标题行下一行插入反向链接
            insert_at = hidx + 1
            # 检查是否已经加过
            existing = ''.join(lines[max(0, insert_at-2):insert_at+1])
            if "↩️" in existing and kp_stem in existing:
                continue
            back_link = f"\n> ↩️ 配套KP：[[{kp_rel}|{kp_stem}]]"
            lines.insert(insert_at, back_link)
            inserted += 1

        book_path.write_text('\n'.join(lines), encoding="utf-8")
        print(f"  {book_rel}: 插入 {inserted} 个反向链接")

if __name__ == "__main__":
    main()
