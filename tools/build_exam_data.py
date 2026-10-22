#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库答题系统数据构建脚本
扫描 教材笔记/ 下的选择题集.md、考研真题集.md、模拟卷.md，输出 data.js
"""

import os
import re
import json
from pathlib import Path

# 知识库根目录（本脚本在 tools/ 下，上一级就是根目录）
ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = ROOT / "教材笔记"
OUTPUT = ROOT / "data.js"
EXPL_OUTPUT = ROOT / "data-expl.js"

# ---------- 工具函数 ----------

def clean_md(text: str) -> str:
    """清理 markdown 链接 [[xxx]]，保留纯文本；保留 $...$ 公式原文"""
    if not text:
        return ""
    # [[路径|显示]] -> 显示（第二组才是给人看的文字）
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    # [[链接]] -> 链接
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # 去掉行首尾多余空格
    lines = [ln.rstrip() for ln in text.split('\n')]
    return '\n'.join(lines).strip()


def parse_chapter_name(dirname: str) -> str:
    """从目录名 '00_导论' 提取章节名 '导论'"""
    m = re.match(r'^\d+[_\s]+(.+)$', dirname)
    return m.group(1) if m else dirname


# ---------- 选择题集解析 ----------

def split_kp_title(title: str, chapter_dir: Path):
    """从 KP 标题里分离：纯名字 / 知识点文件（仓库相对路径）。

    标题形态：
      KP01 资源稀缺性（[[知识点/KP01_资源稀缺性|回知识点]]）
      KP01 完全竞争市场的特征（[[KP01_完全竞争市场的特征|回知识点]]）
      KP99 曲线移动专项                     ← 没有 wikilink
    """
    name = clean_md(title).strip()
    file_rel = None

    m = re.search(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', title)
    if m:
        tgt = m.group(1).strip()
        if not tgt.endswith('.md'):
            tgt += '.md'
        cand = (chapter_dir / tgt)
        if cand.is_file():
            file_rel = cand.relative_to(ROOT).as_posix()
        else:
            cand2 = (chapter_dir / '知识点' / os.path.basename(tgt))
            if cand2.is_file():
                file_rel = cand2.relative_to(ROOT).as_posix()

    # 去掉标题末尾的（[[...]]）与（回知识点）这类括注
    name = re.sub(r'（\s*\[\[[^\]]*\]\]\s*）\s*$', '', name).strip()
    name = re.sub(r'（\s*回知识点\s*）\s*$', '', name).strip()
    return name, file_rel


def parse_choice_file(filepath: Path, subject: str, chapter_id: str, chapter_name: str):
    """
    解析选择题集.md
    返回 kps 列表: [{id, name, questions: [{id, stem, options, answer, explanation}]}]
    """
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')

    kps = []  # 当前章节下的知识点列表
    current_kp = None
    current_q = None  # 当前题目

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 检测知识点分组: ## KPxx 知识点名
        m_kp = re.match(r'^##\s+(KP\d+)\s+(.+)$', stripped)
        if m_kp:
            # 保存上一题
            if current_q and current_kp is not None:
                current_kp['questions'].append(current_q)
                current_q = None
            _name, _file = split_kp_title(m_kp.group(2), filepath.parent)
            current_kp = {
                'id': m_kp.group(1),
                'name': _name,
                'file': _file,
                'questions': []
            }
            kps.append(current_kp)
            i += 1
            continue

        # 检测题目: **N. 题干（　）。**
        m_q = re.match(r'^\*\*(\d+)\.\s+(.+?)\*\*\s*$', stripped)
        if m_q and current_kp is not None:
            # 保存上一题
            if current_q:
                current_kp['questions'].append(current_q)
            qnum = int(m_q.group(1))
            qid = f"{subject}_{chapter_id}_{current_kp['id']}_{qnum}"
            current_q = {
                'id': qid,
                'stem': clean_md(m_q.group(2)),
                'options': {},
                'answer': '',
                'explanation': ''
            }
            i += 1
            continue

        # 检测选项: A. xxx
        m_opt = re.match(r'^([A-D])\.\s+(.+)$', stripped)
        if m_opt and current_q is not None:
            opt_letter = m_opt.group(1)
            opt_text = m_opt.group(2).strip()
            # 可能跨行，直到下一个选项或空行
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if re.match(r'^[A-D]\.\s+', next_line) or next_line.startswith('>') or next_line == '':
                    break
                opt_text += '\n' + next_line
                j += 1
            current_q['options'][opt_letter] = clean_md(opt_text)
            i = j
            continue

        # 检测答案: > **✅ 答案：X**
        m_ans = re.match(r'^>\s*\*\*✅\s*答案[：:]\s*([A-D])\*\*\s*$', stripped)
        if m_ans and current_q is not None:
            current_q['answer'] = m_ans.group(1)
            i += 1
            continue

        # 检测解析: > **解析：** xxx
        m_exp = re.match(r'^>\s*\*\*解析[：:]\*\*\s*(.*)$', stripped)
        if m_exp and current_q is not None:
            exp_text = m_exp.group(1).strip()
            # 可能多行（都是 > 开头）
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line.startswith('>'):
                    # 去掉 > 前缀
                    content = re.sub(r'^>\s*', '', next_line)
                    exp_text += '\n' + content
                    j += 1
                else:
                    break
            current_q['explanation'] = clean_md(exp_text)
            i = j
            continue

        i += 1

    # 保存最后一题
    if current_q and current_kp is not None:
        current_kp['questions'].append(current_q)

    return kps


# ---------- 考研真题集解析 ----------

def parse_subjective_file(filepath: Path, subject: str, chapter_id: str, chapter_name: str):
    """
    解析考研真题集.md
    返回 {short_questions: [...], essay_questions: [...]}
    """
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')

    short_questions = []
    essay_questions = []

    current_section = None  # 'short' / 'essay'
    current_q = None
    current_field = None  # 当前正在解析的字段: 'framework' / 'answer' / 'scoring' / 'life'

    def save_q():
        nonlocal current_q
        if current_q is not None:
            if current_section == 'short':
                short_questions.append(current_q)
            elif current_section == 'essay':
                essay_questions.append(current_q)
        current_q = None
        current_field = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 检测大节: ## 一、简答题 / ## 二、论述题
        m_sec = re.match(r'^##\s+[一二三四五六七八九十]+[、．.]\s*(简答|论述)题', stripped)
        if m_sec:
            save_q()
            current_section = 'short' if m_sec.group(1) == '简答' else 'essay'
            i += 1
            continue

        # 检测题目: ### 简答 N：题干 {#sN} / ### 论述 N：题干 {#lN}
        m_q = re.match(r'^###\s+(简答|论述)\s+(\d+)[：:]\s*(.+?)\s*\{#([sl])\d+\}\s*$', stripped)
        if m_q and current_section is not None:
            save_q()
            q_type = m_q.group(1)
            qnum = int(m_q.group(2))
            anchor = m_q.group(4)  # 's' or 'l'
            qid = f"{subject}_{chapter_id}_{anchor}{qnum}"
            current_q = {
                'id': qid,
                'stem': clean_md(m_q.group(3)),
                'framework': [],
                'answer': '',
                'scoring': '',
                'life_example': ''
            }
            i += 1
            continue

        # 检测字段开始
        # **【答题框架】**
        if current_q is not None and re.match(r'^\*\*【答题框架】\*\*\s*$', stripped):
            current_field = 'framework'
            i += 1
            continue

        # **【参考答案】**
        if current_q is not None and re.match(r'^\*\*【参考答案】\*\*\s*$', stripped):
            current_field = 'answer'
            i += 1
            continue

        # **【解析·得分点】** xxx
        m_score = re.match(r'^\*\*【解析[·・]得分点】\*\*\s*(.*)$', stripped)
        if m_score and current_q is not None:
            current_q['scoring'] = clean_md(m_score.group(1))
            current_field = 'scoring'
            i += 1
            continue

        # **【生活实例】** xxx
        m_life = re.match(r'^\*\*【生活实例】\*\*\s*(.*)$', stripped)
        if m_life and current_q is not None:
            current_q['life_example'] = clean_md(m_life.group(1))
            current_field = 'life'
            i += 1
            continue

        # **【考什么】** xxx (不需要)
        if re.match(r'^\*\*【考什么】\*\*\s*', stripped):
            current_field = None
            i += 1
            continue

        # **【建议字数】** (不需要)
        if re.match(r'^\*\*【建议字数】\*\*\s*', stripped):
            current_field = None
            i += 1
            continue

        # **【双链接】** 🔗 [[知识点/KPxx|回知识点]] ｜ 📖 [[原书…]]
        m_dual = re.match(r'^\*\*【双链接】\*\*\s*(.*)$', stripped)
        if m_dual and current_q is not None:
            body = m_dual.group(1)
            # 优先取「知识点/KPxx」那条
            kp_file = None
            for wm in re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', body):
                tgt = wm.group(1).strip()
                if '知识点/KP' not in tgt:
                    continue
                if not tgt.endswith('.md'):
                    tgt += '.md'
                cand = filepath.parent / tgt
                if cand.is_file():
                    kp_file = cand.relative_to(ROOT).as_posix()
                    break
                cand2 = filepath.parent / '知识点' / os.path.basename(tgt)
                if cand2.is_file():
                    kp_file = cand2.relative_to(ROOT).as_posix()
                    break
            if kp_file:
                current_q['kp_file'] = kp_file
            current_field = None
            i += 1
            continue

        # 分割线 ---
        if stripped == '---':
            save_q()
            i += 1
            continue

        # 处理字段内容
        if current_q is not None and current_field == 'framework':
            # 无序列表项: - xxx
            m_item = re.match(r'^-\s+(.+)$', stripped)
            if m_item:
                current_q['framework'].append(clean_md(m_item.group(1)))
                i += 1
                continue
            else:
                # 非列表项，框架结束
                current_field = None

        if current_q is not None and current_field == 'answer':
            # 答案正文，直到遇到下一个 **【 字段 或 ---
            if re.match(r'^\*\*【', stripped) or stripped == '---':
                current_field = None
                # 不前进，让后续逻辑处理
            else:
                if current_q['answer']:
                    current_q['answer'] += '\n'
                current_q['answer'] += stripped
                i += 1
                continue

        if current_q is not None and current_field == 'scoring':
            # 得分点可能多行
            if re.match(r'^\*\*【', stripped) or stripped == '---':
                current_field = None
            else:
                if current_q['scoring']:
                    current_q['scoring'] += '\n'
                current_q['scoring'] += stripped
                i += 1
                continue

        if current_q is not None and current_field == 'life':
            if re.match(r'^\*\*【', stripped) or stripped == '---':
                current_field = None
            else:
                if current_q['life_example']:
                    current_q['life_example'] += '\n'
                current_q['life_example'] += stripped
                i += 1
                continue

        i += 1

    save_q()

    # 清理答案
    for q in short_questions + essay_questions:
        q['answer'] = clean_md(q['answer'])
        q['scoring'] = clean_md(q['scoring'])
        q['life_example'] = clean_md(q['life_example'])

    return {'short_questions': short_questions, 'essay_questions': essay_questions}


# ---------- 模拟卷解析 ----------

def extract_subject_from_stem(stem: str):
    """从题干末尾的括号提取学科: （政治经济学）/（西方经济学）"""
    if '政治经济学' in stem:
        return 'pol_econ', re.sub(r'[（(]\s*政治经济学\s*[)）]\s*', '', stem).strip()
    if '西方经济学' in stem:
        return 'west_econ', re.sub(r'[（(]\s*西方经济学\s*[)）]\s*', '', stem).strip()
    return None, stem


# 三块内容的块标题识别
_HDR = r'^\*\*【([^】]*)】\*\*\s*$'
_KEEP = ('核心推导', '为什么要答这几点', '如何分析题目')

def parse_mock_file(filepath: Path, mock_id: str):
    """
    解析模拟卷.md（兼容多种格式）
    返回 {id, title, difficulty, duration_min, questions: [...]}
    """
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')

    # 提取标题
    title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filepath.stem

    # 提取难度
    diff_match = re.search(r'\*\*难度[：:]\s*([^*]+)\*\*', text)
    difficulty = diff_match.group(1).strip() if diff_match else '未知'

    # 提取考试时间
    time_match = re.search(r'考试时间[：:]\s*(\d+)\s*分钟', text)
    duration_min = int(time_match.group(1)) if time_match else 180

    questions = []
    current_subject = None  # 'pol_econ' / 'west_econ'
    current_q = None
    current_field = None

    def save_q():
        nonlocal current_q
        if current_q is not None:
            questions.append(current_q)
        current_q = None
        current_field = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 检测部分标题，推断学科
        # 格式1: ## 第一部分　政治经济学（共 75 分）
        # 格式2: ## 第一部分　简答与计算题... / ## 一、简答与计算题...
        # 格式3: ## 第二部分　论述题... / ## 二、论述题...
        m_part = re.match(r'^##\s+(第[一二三四五六七八九十]+部分[　\s]+)?(.+)$', stripped)
        if m_part:
            part_name = m_part.group(2)
            if '政治经济学' in part_name:
                current_subject = 'pol_econ'
                save_q()
                i += 1
                continue
            elif '西方经济学' in part_name:
                current_subject = 'west_econ'
                save_q()
                i += 1
                continue
            elif '简答' in part_name or '论述' in part_name:
                # 简答/论述大节，不改变学科（学科从题目提取）
                save_q()
                i += 1
                continue
            elif '注意事项' in part_name or '考点' in part_name:
                save_q()
                i += 1
                continue

        # 检测题目（兼容多种格式）
        # 格式A: #### 简答 1（15 分）：题干 / #### 简答 4（15 分，含计算）：题干
        m_a = re.match(r'^####\s+(简答|论述)\s+(\d+)[（(](\d+)\s*分[^)）]*[)）][：:]\s*(.+)$', stripped)
        # 格式B: ### 简答 1：题干（15 分）
        m_b = re.match(r'^###\s+(简答|论述)\s+(\d+)[：:]\s*(.+?)[（(](\d+)\s*分[)）]\s*$', stripped)
        # 格式C: ### 简答 1：题干（政治经济学）
        m_c = re.match(r'^###\s+(简答|论述)\s+(\d+)[：:]\s*(.+?)[（(](政治经济学|西方经济学)[)）]\s*$', stripped)
        # 格式D: ### 简答 1（政治经济学，15 分）：题干
        m_d = re.match(r'^###\s+(简答|论述)\s+(\d+)[（(](政治经济学|西方经济学)[，,]\s*(\d+)\s*分[)）][：:]\s*(.+)$', stripped)

        m_q = None
        q_type = None
        qnum = None
        score = None
        stem = None
        q_subject = None

        if m_a:
            m_q = m_a
            q_type = m_a.group(1)
            qnum = int(m_a.group(2))
            score = int(m_a.group(3))
            stem = m_a.group(4).strip()
            q_subject = current_subject
        elif m_b:
            m_q = m_b
            q_type = m_b.group(1)
            qnum = int(m_b.group(2))
            stem = m_b.group(3).strip()
            score = int(m_b.group(4))
            # 从题干提取学科
            q_subject, stem = extract_subject_from_stem(stem)
            if not q_subject:
                q_subject = current_subject
        elif m_c:
            m_q = m_c
            q_type = m_c.group(1)
            qnum = int(m_c.group(2))
            stem = m_c.group(3).strip()
            q_subject = 'pol_econ' if m_c.group(4) == '政治经济学' else 'west_econ'
            score = 15 if q_type == '简答' else 30
        elif m_d:
            m_q = m_d
            q_type = m_d.group(1)
            qnum = int(m_d.group(2))
            q_subject = 'pol_econ' if m_d.group(3) == '政治经济学' else 'west_econ'
            score = int(m_d.group(4))
            stem = m_d.group(5).strip()

        if m_q:
            save_q()
            qid = f"{mock_id}_{'s' if q_type == '简答' else 'l'}{qnum}"
            current_q = {
                'id': qid,
                'type': 'short' if q_type == '简答' else 'essay',
                'subject': q_subject or 'unknown',
                'score': score,
                'stem': clean_md(stem),
                'framework': [],
                'answer': '',
                'scoring': '',
'life_example': '',
                'derivation': '',
                'why_points': '',
                'how_to_analyze': ''
            }
            i += 1
            continue

        # 检测字段
        _mm = re.match(_HDR, stripped) if current_q is not None else None
        if _mm is not None:
            _ttl = _mm.group(1)
            _nf = None
            if _ttl in _KEEP:
                _nf = ('derivation', 'why_points', 'how_to_analyze')[_KEEP.index(_ttl)]
            elif _ttl.startswith(_KEEP[0]):
                _nf = 'derivation'
            elif _ttl.startswith(_KEEP[1]):
                _nf = 'why_points'
            elif _ttl.startswith(_KEEP[2]):
                _nf = 'how_to_analyze'
            if _nf is not None:
                current_field = _nf
                i += 1
                continue
        if current_q is not None and re.match(r'^\*\*【答题框架】\*\*\s*$', stripped):
            current_field = 'framework'
            i += 1
            continue

        if current_q is not None and re.match(r'^\*\*【参考答案】\*\*\s*$', stripped):
            current_field = 'answer'
            i += 1
            continue

        m_score = re.match(r'^\*\*【解析[·・]得分点】\*\*\s*(.*)$', stripped)
        if m_score and current_q is not None:
            current_q['scoring'] = clean_md(m_score.group(1))
            current_field = 'scoring'
            i += 1
            continue

        m_life = re.match(r'^\*\*【生活实例】\*\*\s*(.*)$', stripped)
        if m_life and current_q is not None:
            current_q['life_example'] = clean_md(m_life.group(1))
            current_field = 'life'
            i += 1
            continue

        if re.match(r'^\*\*【考什么】\*\*\s*', stripped):
            current_field = None
            i += 1
            continue

        if re.match(r'^\*\*【双链接】\*\*\s*', stripped):
            current_field = None
            i += 1
            continue

        if stripped == '---':
            save_q()
            i += 1
            continue

        # 处理字段内容
        if current_q is not None and current_field in ('derivation', 'why_points', 'how_to_analyze'):
            _m3 = re.match(_HDR, stripped)
            _t3 = _m3.group(1) if _m3 is not None else ''
            _fx = chr(0x6ee1)+chr(0x5206)
            _sub = ('易失', '加分', '阅卷', '字数')
            _nof = _m3 is not None and _t3[:2] != _fx and _t3[:2] not in _sub
            if _nof or stripped == '---' or re.match(r'^#{3,4}\s+', stripped):
                current_field = None
            else:
                _cf = current_field
                if current_q[_cf]:
                    current_q[_cf] += chr(10)
                current_q[_cf] += stripped
        if current_q is not None and current_field == 'framework':
            m_item = re.match(r'^-\s+(.+)$', stripped)
            if m_item:
                current_q['framework'].append(clean_md(m_item.group(1)))
                i += 1
                continue
            elif stripped != '':
                current_field = None

        if current_q is not None and current_field == 'answer':
            if re.match(r'^\*\*【', stripped) or stripped == '---' or re.match(r'^#{3,4}\s+', stripped):
                current_field = None
            else:
                if current_q['answer']:
                    current_q['answer'] += '\n'
                current_q['answer'] += stripped
                i += 1
                continue

        if current_q is not None and current_field == 'scoring':
            if re.match(r'^\*\*【', stripped) or stripped == '---' or re.match(r'^#{3,4}\s+', stripped):
                current_field = None
            else:
                if current_q['scoring']:
                    current_q['scoring'] += '\n'
                current_q['scoring'] += stripped
                i += 1
                continue

        if current_q is not None and current_field == 'life':
            if re.match(r'^\*\*【', stripped) or stripped == '---' or re.match(r'^#{3,4}\s+', stripped):
                current_field = None
            else:
                if current_q['life_example']:
                    current_q['life_example'] += '\n'
                current_q['life_example'] += stripped
                i += 1
                continue

        i += 1

    save_q()

    # 清理
    for q in questions:
        for _k in ('derivation', 'why_points', 'how_to_analyze'):
            q[_k] = q[_k].strip()
        q['answer'] = clean_md(q['answer'])
        q['scoring'] = clean_md(q['scoring'])
        q['life_example'] = clean_md(q['life_example'])

    return {
        'id': mock_id,
        'title': clean_md(title),
        'difficulty': clean_md(difficulty),
        'duration_min': duration_min,
        'questions': questions
    }


# ---------- 主流程 ----------

def main():
    print(f"知识库根目录: {ROOT}")
    print(f"教材笔记目录: {NOTES_DIR}")

    data = {
        'choice': {'west_econ': {'chapters': []}, 'pol_econ': {'chapters': []}},
        'subjective': {'west_econ': {'chapters': []}, 'pol_econ': {'chapters': []}},
        'mock_papers': []
    }

    stats = {
        'choice_total': 0,
        'short_total': 0,
        'essay_total': 0,
        'mock_total': 0,
        'mock_details': [],
        'warnings': []
    }

    # 1. 扫描西方经济学
    west_dir = NOTES_DIR / "06_西方经济学"
    for chapter_dir in sorted(west_dir.iterdir()):
        if not chapter_dir.is_dir():
            continue
        chapter_id = chapter_dir.name
        chapter_name = parse_chapter_name(chapter_id)

        # 选择题
        choice_file = chapter_dir / "选择题集.md"
        if choice_file.exists():
            kps = parse_choice_file(choice_file, 'west_econ', chapter_id, chapter_name)
            data['choice']['west_econ']['chapters'].append({
                'id': chapter_id,
                'name': chapter_name,
                'kps': kps
            })
            qcount = sum(len(kp['questions']) for kp in kps)
            stats['choice_total'] += qcount
            print(f"  [选择] 西经 {chapter_name}: {len(kps)} 个知识点, {qcount} 题")
        else:
            stats['warnings'].append(f"缺少选择题集: {choice_file}")

        # 考研真题集
        subj_file = chapter_dir / "考研真题集.md"
        if subj_file.exists():
            subj = parse_subjective_file(subj_file, 'west_econ', chapter_id, chapter_name)
            data['subjective']['west_econ']['chapters'].append({
                'id': chapter_id,
                'name': chapter_name,
                'short_questions': subj['short_questions'],
                'essay_questions': subj['essay_questions']
            })
            stats['short_total'] += len(subj['short_questions'])
            stats['essay_total'] += len(subj['essay_questions'])
            print(f"  [主观] 西经 {chapter_name}: 简答 {len(subj['short_questions'])}, 论述 {len(subj['essay_questions'])}")
        else:
            stats['warnings'].append(f"缺少考研真题集: {subj_file}")

    # 2. 扫描政治经济学
    pol_dir = NOTES_DIR / "07_政治经济学"
    for chapter_dir in sorted(pol_dir.iterdir()):
        if not chapter_dir.is_dir():
            continue
        chapter_id = chapter_dir.name
        chapter_name = parse_chapter_name(chapter_id)

        choice_file = chapter_dir / "选择题集.md"
        if choice_file.exists():
            kps = parse_choice_file(choice_file, 'pol_econ', chapter_id, chapter_name)
            data['choice']['pol_econ']['chapters'].append({
                'id': chapter_id,
                'name': chapter_name,
                'kps': kps
            })
            qcount = sum(len(kp['questions']) for kp in kps)
            stats['choice_total'] += qcount
            print(f"  [选择] 政经 {chapter_name}: {len(kps)} 个知识点, {qcount} 题")
        else:
            stats['warnings'].append(f"缺少选择题集: {choice_file}")

        subj_file = chapter_dir / "考研真题集.md"
        if subj_file.exists():
            subj = parse_subjective_file(subj_file, 'pol_econ', chapter_id, chapter_name)
            data['subjective']['pol_econ']['chapters'].append({
                'id': chapter_id,
                'name': chapter_name,
                'short_questions': subj['short_questions'],
                'essay_questions': subj['essay_questions']
            })
            stats['short_total'] += len(subj['short_questions'])
            stats['essay_total'] += len(subj['essay_questions'])
            print(f"  [主观] 政经 {chapter_name}: 简答 {len(subj['short_questions'])}, 论述 {len(subj['essay_questions'])}")
        else:
            stats['warnings'].append(f"缺少考研真题集: {subj_file}")

    # 3. 扫描模拟卷
    mock_dir = NOTES_DIR / "模拟卷"
    mock_files = sorted([f for f in mock_dir.iterdir() if f.name.startswith('模拟卷') and f.suffix == '.md'])
    for idx, mock_file in enumerate(mock_files, 1):
        mock_id = f"mock{idx}"
        mock_data = parse_mock_file(mock_file, mock_id)
        data['mock_papers'].append(mock_data)
        stats['mock_total'] += len(mock_data['questions'])
        short_cnt = sum(1 for q in mock_data['questions'] if q['type'] == 'short')
        essay_cnt = sum(1 for q in mock_data['questions'] if q['type'] == 'essay')
        stats['mock_details'].append({
            'id': mock_id,
            'title': mock_data['title'],
            'short': short_cnt,
            'essay': essay_cnt,
            'total': len(mock_data['questions'])
        })
        print(f"  [模拟] {mock_data['title']}: 简答 {short_cnt}, 论述 {essay_cnt}, 共 {len(mock_data['questions'])} 题")

    # 拆出解析文本：解析占整个 data.js 的一半，但只有点了"查看解析"才需要
    # 拆走后首屏要下的 data.js 从 4.3MB 降到约 1.7MB
    explanations = {}
    for sub in ('west_econ', 'pol_econ'):
        for ch in data['choice'][sub]['chapters']:
            for kp in ch['kps']:
                for q in kp['questions']:
                    if 'explanation' in q:
                        explanations[q['id']] = q.pop('explanation')

    # 输出 data.js（题目主体）
    stamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    js_content = ("// 自动生成，请勿手动编辑\n// 生成时间: " + stamp + "\n")
    js_content += "window.EXAM_DATA = " + json.dumps(
        data, ensure_ascii=False, separators=(',', ':')) + ";\n"
    OUTPUT.write_text(js_content, encoding='utf-8')

    # 输出 data-expl.js（解析文本，按需加载）
    expl_content = ("// 自动生成，请勿手动编辑——选择题解析，按需加载\n// 生成时间: " + stamp + "\n")
    expl_content += "window.EXAM_EXPL = " + json.dumps(
        explanations, ensure_ascii=False, separators=(',', ':')) + ";\n"
    EXPL_OUTPUT.write_text(expl_content, encoding='utf-8')

    print(f"\n输出文件: {OUTPUT}")
    print(f"文件大小: {OUTPUT.stat().st_size / 1024:.1f} KB")
    print(f"解析文件: {EXPL_OUTPUT}")
    print(f"文件大小: {EXPL_OUTPUT.stat().st_size / 1024:.1f} KB（{len(explanations)} 条）")

    # 打印统计
    print("\n========== 统计 ==========")
    print(f"选择题总数: {stats['choice_total']}")
    print(f"简答题总数: {stats['short_total']}")
    print(f"论述题总数: {stats['essay_total']}")
    print(f"模拟卷总题数: {stats['mock_total']}")
    print("\n各模拟卷:")
    for m in stats['mock_details']:
        print(f"  {m['title']}: 简答{m['short']} + 论述{m['essay']} = {m['total']}题")

    if stats['warnings']:
        print(f"\n⚠️ 警告 ({len(stats['warnings'])}):")
        for w in stats['warnings']:
            print(f"  - {w}")
    else:
        print("\n✅ 无警告")


if __name__ == '__main__':
    main()
