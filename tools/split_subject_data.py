#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按科目拆分生成题库：每科一个 data-<key>.js，前端切到哪科才加载哪科。

与 build_exam_data.py 的区别：
- build_exam_data.py 生成单一 data.js（西经+政经全量，1.7MB）
- 本脚本生成 data-west_econ.js / data-pol_econ.js / data-zonghe.js ... 分科文件

5 个新科目的题库格式与西经/政经不同：
- 选择题集.md 按 "## 第一章 绪论" 分章（不是 ## KPxx），需要先按章切片再逐片喂给 parse_choice_file
- 主观题文件叫 简答题集.md，格式是 "**N. 题干**" + "**答：**" + 分点正文，需专用解析器

用法：
  python3 tools/split_subject_data.py            # 生成全部科目
  python3 tools/split_subject_data.py zonghe     # 只生成某一科
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = ROOT / "教材笔记"

# 科目注册表：key -> (目录名, 显示名, 主观题文件名, 主观题格式)
SUBJECTS = {
    "west_econ": ("06_西方经济学", "西方经济学", "考研真题集.md", "kaoyan"),
    "pol_econ": ("07_政治经济学", "政治经济学", "考研真题集.md", "kaoyan"),
    "zonghe": ("01_综合评价", "综合评价", "简答题集.md", "simple"),
    "jiliang": ("02_计量经济学", "计量经济学", "简答题集.md", "simple"),
    "shixu": ("03_时间序列", "时间序列分析", "简答题集.md", "simple"),
    "duoyuan": ("04_多元统计", "多元统计分析", "简答题集.md", "simple"),
    "tongyuan": ("05_统计学原理", "统计学原理", "简答题集.md", "simple"),
}


def resolve_kp_file(text, md_path):
    """从 md 正文里找 [[知识点/KPxx|...]] 引用，解析成相对 ROOT 的真实路径。

    西经/政经的题目块里带 **【双链接】** \u9879\uff0c\u5f15\u7528\u76ee\u6807\u662f\u76f8\u5bf9\u4e8e\u672c md \u7684
    \u77e5\u8bc6\u70b9\u6587\u4ef6\uff08\u5982 01_\u9700\u6c42\u4f9b\u7ed9\u4e0e\u5747\u8861\u4ef7\u683c/\u77e5\u8bc6\u70b9/KP01_xxx.md\uff09\u3002
    \u4e0d\u80fd\u76f4\u63a5\u62ff\u6587\u4ef6\u540d\uff1a\u4e0d\u540c\u79d1\u76ee\u4e0b\u53ef\u80fd\u6709\u540c\u540d KPxx\uff0c
    \u5fc5\u987b\u6309\u672c md \u6240\u5728\u76ee\u5f55\u5b9e\u9645\u5b58\u5728\u7684\u8def\u5f84\u53d6\u3002\u627e\u4e0d\u5230\u5c31\u8fd4\u56de\u7a7a\u4e32\uff0c\u4e0d\u731c\u3002
    """
    if not md_path:
        return ""
    base = Path(md_path).parent
    for wm in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", text or ""):
        tgt = wm.group(1).strip()
        if "\u77e5\u8bc6\u70b9/KP" not in tgt:
            continue
        if not tgt.endswith(".md"):
            tgt += ".md"
        for cand in (base / tgt, base / "\u77e5\u8bc6\u70b9" / Path(tgt).name):
            try:
                if cand.is_file():
                    return cand.relative_to(ROOT).as_posix()
            except ValueError:
                continue
    return ""


def clean_md(s):
    """去掉 markdown 强调符号，压缩空白"""
    if not s:
        return ""
    s = s.replace("**", "").replace("__", "")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def parse_chapter_name(dirname):
    """01_综合评价的一般问题 -> 综合评价的一般问题"""
    return re.sub(r"^\d+_", "", dirname)


def strip_quan(s):
    """第一章 绪论 -> 绪论；第0章 导论 -> 导论；第一章 -> None"""
    m = re.match(r"^第[0-9一二三四五六七八九十百]+章\s*(.*)$", s.strip())
    if m:
        return m.group(1).strip() or None
    return s.strip() or None


def split_by_heading(text, pattern):
    """按 ## 标题切段，返回 [(标题行, 正文), ...]"""
    lines = text.split("\n")
    blocks = []
    cur_title = None
    cur_lines = []
    for line in lines:
        if re.match(pattern, line.strip()):
            if cur_title is not None:
                blocks.append((cur_title, "\n".join(cur_lines)))
            cur_title = line.strip()
            cur_lines = []
        elif cur_title is not None:
            cur_lines.append(line)
    if cur_title is not None:
        blocks.append((cur_title, "\n".join(cur_lines)))
    return blocks


# ---------- 选择题解析（自建，适配 "## 第N章 名字" 分章格式） ----------

def parse_choice_md(text, subject, chapter_id, chapter_name):
    """
    解析单科选择题集.md，按 ## 第N章 分章，返回 kps 列表。
    每个章节作为一个"伪知识点"kp，id 用 CH01 形式，保证与西经的 KPxx 结构兼容。
    """
    kps = []
    blocks = split_by_heading(text, r"^##\s+第[0-9一二三四五六七八九十百]+章")
    if not blocks:
        # 没有 ## 章节标题：整篇当一个块
        blocks = [(None, text)]

    for idx, (title, body) in enumerate(blocks, 1):
        # 章节内的 ## KP01 xxx 是真知识点编号，沿用它可以保住历史题 id（错题本、云端进度都按它索引）
        m_kp = re.match(r"^##\s+(KP\d+)\s+(.+)$", (title or "").strip())
        kp_id = m_kp.group(1) if m_kp else ("CH%02d" % idx)
        kp_name = strip_quan(re.sub(r"^#+\s*", "", title.strip())) if title else chapter_name
        if not kp_name:
            kp_name = chapter_name
        kp_name = clean_md(kp_name)

        # 如果章节标题带了 "第N章 Xxxx"，Xxxx 就是知识点名
        questions = parse_choice_questions(body, subject, chapter_id, kp_id)
        if questions:
            kps.append({
                "id": kp_id,
                "name": kp_name,
                "file": "",
                "questions": questions,
            })
    return kps


def parse_choice_questions(body, subject, chapter_id, kp_id):
    lines = body.split("\n")
    questions = []
    cur = None
    i = 0

    def save():
        nonlocal cur
        if cur is not None and cur["options"]:
            questions.append(cur)
        cur = None

    while i < len(lines):
        stripped = lines[i].strip()

        # **1.** 题干（　）。  或  **1. 题干**  或  **1. 题干**
        m_q = re.match(r"^\*\*(\d+(?:[\.．]\d+)?)[\.．]?\*\*\s+(.+)$", stripped) \
              or re.match(r"^\*\*(\d+(?:[\.．]\d+)?)[\.．]\s+(.+?)\*\*\s*$", stripped)
        if m_q:
            save()
            qnum_text = m_q.group(1).replace("．", ".")
            qnum = len(questions) + 1
            cur = {
                "id": "%s_%s_%s_%d" % (subject, chapter_id, kp_id, qnum),
                "num": qnum_text,
                "stem": clean_md(m_q.group(2)),
                "options": {},
                "answer": "",
                "explanation": "",
            }
            i += 1
            continue

        # A. xxx
        m_opt = re.match(r"^([A-D])[\.．、]\s*(.+)$", stripped)
        if m_opt and cur is not None:
            letter = m_opt.group(1)
            opt = m_opt.group(2).strip()
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt or re.match(r"^[A-D][\.．、]\s+", nxt) or nxt.startswith(">") or re.match(r"^\*\*\d+\.", nxt):
                    break
                if re.match(r"^[A-D][\.．、]", nxt):
                    break
                opt += " " + nxt
                j += 1
            cur["options"][letter] = clean_md(opt)
            i = j
            continue

        # > **✅ 答案：B**
        m_ans = re.match(r"^>\s*\*\*[✅✔]?\s*答案[：:]\s*([A-D])\*\*", stripped)
        if m_ans and cur is not None:
            cur["answer"] = m_ans.group(1)
            i += 1
            continue

        # > **解析：** xxx
        m_exp = re.match(r"^>\s*\*\*解析[：:]\*\*\s*(.*)$", stripped)
        if m_exp and cur is not None:
            parts = [m_exp.group(1).strip()]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith(">"):
                parts.append(re.sub(r"^>\s?", "", lines[j].strip()))
                j += 1
            cur["explanation"] = clean_md("\n".join(parts))
            i = j
            continue

        i += 1

    save()
    return questions


def parse_choice_kp(text, subject, chapter_id, chapter_name):
    """章节子目录里的选择题集.md：按 ## KPxx 知识点切分，题 id 保持 history 兼容。"""
    kps = []
    blocks = split_by_heading(text, r"^##\s+KP\d+\s+")
    for title, body in blocks:
        m_kp = re.match(r"^##\s+(KP\d+)\s+(.+?)\s*$", title.strip())
        if not m_kp:
            continue
        kp_id = m_kp.group(1)
        kp_name = clean_md(strip_quan(re.sub(r"^\[\[.*?\|(.*?)\]\].*$", r"\1", m_kp.group(2))))
        questions = parse_choice_questions(body, subject, chapter_id, kp_id)
        if questions:
            kps.append({"id": kp_id, "name": kp_name, "file": "", "questions": questions})
    return kps


# ---------- 主观题解析 ----------

def parse_subjective_kaoyan(text, subject, chapter_id, chapter_name, md_path=None):
    """考研真题集.md 格式（西经/政经）：## 一、简答题 + ### 简答 N：题干"""
    return parse_subjective_common(text, subject, chapter_id, chapter_name, "kaoyan", md_path)


def parse_subjective_simple(text, subject, chapter_id, chapter_name, md_path=None):
    """简答题集.md 格式（5 新科）：## 第N章 + **N. 题干** + **答：**"""
    return parse_subjective_common(text, subject, chapter_id, chapter_name, "simple", md_path)


def parse_subjective_common(text, subject, chapter_id, chapter_name, mode, md_path=None):
    short_qs, essay_qs = [], []
    lines = text.split("\n")

    section = None      # 'short' / 'essay'
    cur = None
    field = None

    def save():
        nonlocal cur, field
        if cur is not None:
            if section == "essay":
                essay_qs.append(cur)
            else:
                short_qs.append(cur)
        cur = None
        field = None

    if mode == "simple":
        # 每道题：**N. 题干** ... **答：** ... 正文
        for raw in lines:
            s = raw.strip()
            m_q = re.match(r"^\*\*(\d+)\.\s*(.+?)\*\*\s*$", s)
            if m_q and not s.startswith("**答"):
                save()
                cur = {
                    "id": "%s_%s_s%d" % (subject, chapter_id, int(m_q.group(1))),
                    "stem": clean_md(m_q.group(2)),
                    "framework": [],
                    "answer": "",
                    "scoring": "",
                    "life_example": "",
                    "kp_file": "",
                }
                field = None
                continue
            if cur is None:
                continue
            if re.match(r"^\*\*答[：:]\*\*\s*$", s) or re.match(r"^\*\*答[：:]\*\*", s):
                field = "answer"
                rest = re.sub(r"^\*\*答[：:]\*\*\s*", "", s)
                if rest:
                    cur["answer"] += rest + "\n"
                continue
            if field == "answer":
                cur["answer"] += raw.rstrip() + "\n"
        save()
        for q in short_qs:
            q["answer"] = q["answer"].strip()
        return {"short_questions": short_qs, "essay_questions": []}

    # kaoyan 模式
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()

        m_sec = re.match(r"^##\s+[一二三四五六七八九十]+[、．.]\s*(简答|论述)题", s)
        if m_sec:
            save()
            section = "short" if m_sec.group(1) == "简答" else "essay"
            i += 1
            continue

        m_q = re.match(r"^###\s+(?:<a id=\"[^\"]*\"></a>)?\s*(简答|论述)\s+(\d+)[：:]\s*(.+?)\s*$", s)
        if m_q and section is not None:
            save()
            num = int(m_q.group(2))
            cur = {
                "id": "%s_%s_%s%d" % (subject, chapter_id, "s" if m_q.group(1) == "简答" else "l", num),
                "stem": clean_md(m_q.group(3)),
                "framework": [],
                "answer": "",
                "scoring": "",
                "life_example": "",
                "derivation": "",
                "why_points": "",
                "how_to_analyze": "",
                "kp_file": "",
            }
            field = None
            i += 1
            continue

        if cur is not None:
            if s.startswith("**【核心推导】"):
                field = "derivation"
                cur["derivation"] = re.sub(r"^\*\*【[^】]*】\*\*\s*", "", s)
                i += 1
                continue
            if s.startswith("**【为什么要答这几点】"):
                field = "why"
                cur["why_points"] = re.sub(r"^\*\*【[^】]*】\*\*\s*", "", s)
                i += 1
                continue
            if s.startswith("**【如何分析题目】"):
                field = "analyze"
                cur["how_to_analyze"] = re.sub(r"^\*\*【[^】]*】\*\*\s*", "", s)
                i += 1
                continue
            if s.startswith("**【答题框架】"):
                field = "framework"
                i += 1
                continue
            if s.startswith("**【参考答案】"):
                field = "answer"
                i += 1
                continue
            if s.startswith("**【解析·得分点】") or s.startswith("**【得分点】"):
                field = "scoring"
                cur["scoring"] = re.sub(r"^\*\*【[^】]*】\*\*\s*", "", s)
                i += 1
                continue
            if s.startswith("**【生活实例】"):
                field = "life"
                cur["life_example"] = re.sub(r"^\*\*【[^】]*】\*\*\s*", "", s)
                i += 1
                continue
            # 【双链接】行里带着 [[知识点/KPxx|回知识点]]，把它解析成真实文件路径；
            # 不先拦下来的话会被下面那个 "【" 分支当成废字段跳掉，
            # 前端“回知识点”就只能拼出一个空链接。
            if s.startswith("**【双链接】"):
                if not cur.get("kp_file"):
                    kf = resolve_kp_file(s, md_path)
                    if kf:
                        cur["kp_file"] = kf
                i += 1
                continue
            if s.startswith("**【") or s.startswith("---"):
                field = None
                i += 1
                continue

            if field == "framework":
                m_b = re.match(r"^[-*]\s+(.+)$", s)
                if m_b:
                    cur["framework"].append(clean_md(m_b.group(1)))
            elif field == "answer":
                cur["answer"] += line.rstrip() + "\n"
            elif field == "scoring":
                cur["scoring"] += " " + s if s else ""
            elif field == "life":
                cur["life_example"] += " " + s if s else ""
            elif field == "derivation":
                cur["derivation"] += "\n" + line.rstrip()
            elif field == "why":
                cur["why_points"] += "\n" + line.rstrip()
            elif field == "analyze":
                cur["how_to_analyze"] += "\n" + line.rstrip()
        i += 1

    save()
    for q in short_qs + essay_qs:
        q["answer"] = q["answer"].strip()
        q["scoring"] = q["scoring"].strip()
        q["life_example"] = q["life_example"].strip()
        for k in ("derivation", "why_points", "how_to_analyze"):
            if k in q:
                q[k] = q[k].strip()
    return {"short_questions": short_qs, "essay_questions": essay_qs}


def parse_subjective_heading(text, subject, chapter_id, chapter_name, md_path=None):
    """简答题集.md 的另一种写法：### 子标题 + **答题要点：** 正文（时间序列/多元统计）。"""
    qs = []
    cur = None
    field = None
    for raw in text.split("\n"):
        s = raw.strip()
        m_h = re.match(r"^###\s+(.+?)\s*$", s)
        if m_h and not s.startswith("####"):
            if cur is not None:
                qs.append(cur)
            cur = {
                "id": "%s_%s_s%d" % (subject, chapter_id, len(qs) + 1),
                "stem": clean_md(m_h.group(1)),
                "framework": [],
                "answer": "",
                "scoring": "",
                "life_example": "",
                "kp_file": "",
                "derivation": "",
                "why_points": "",
                "how_to_analyze": "",
            }
            field = None
            continue
        if cur is None:
            continue
        if s.startswith("**答题要点") or s.startswith("**答："):
            field = "answer"
            rest = re.sub(r"^\*\*[^*]*\*\*\s*", "", s)
            if rest:
                cur["answer"] += rest + "\n"
            continue
        if s in ("---", "") and field == "answer":
            cur["answer"] += ""
            continue
        if s.startswith("**【"):
            m_t = re.match(r"^\*\*【([^】]*)】\*\*", s)
            title = m_t.group(1) if m_t else ""
            nf = None
            if title.startswith("核心推导"):
                nf = "derivation"
            elif title.startswith("为什么要答"):
                nf = "why_points"
            elif title.startswith("如何分析"):
                nf = "how_to_analyze"
            if nf:
                field = nf
                rest = re.sub(r"^\*\*[^*]*\*\*\s*", "", s)
                if rest:
                    cur[nf] += rest + "\n"
                continue
        if field is not None:
            cur[field] += raw.rstrip() + "\n"
    if cur is not None:
        qs.append(cur)
    for q in qs:
        q["answer"] = q["answer"].strip()
        for k in ("derivation", "why_points", "how_to_analyze"):
            q[k] = q[k].strip()
    return {"short_questions": qs, "essay_questions": []}


# ---------- 主流程 ----------

def build_subject(key):
    dirname, display, subj_file, subj_mode = SUBJECTS[key]
    base = NOTES_DIR / dirname

    data = {
        "name": display,
        "choice": {"chapters": []},
        "subjective": {"chapters": []},
    }
    explanations = {}

    # 章节顺序以选择题集.md 的 ## 标题为准；没有则退回扫描子目录
    choice_file = base / "选择题集.md"
    chapter_dirs = []
    if base.exists():
        for p in sorted(base.iterdir()):
            if p.is_dir() and p.name != "assets" and re.match(r"^\d+_", p.name):
                chapter_dirs.append(p)

    if choice_file.exists():
        text = choice_file.read_text(encoding="utf-8")
        blocks = split_by_heading(text, r"^##\s+第[0-9一二三四五六七八九十百]+章")
        for idx, (title, body) in enumerate(blocks, 1):
            kp_id = "CH%02d" % idx
            name = clean_md(strip_quan(re.sub(r"^#+\s*", "", title.strip())) or ("第%d章" % idx))
            questions = parse_choice_questions(body, key, kp_id, kp_id)
            qs = []
            for q in questions:
                explanations[q["id"]] = q.pop("explanation") or ""
                qs.append(q)
            if not qs:
                continue
            data["choice"]["chapters"].append({
                "id": kp_id,
                "name": name,
                "kps": [{"id": kp_id, "name": name, "file": "", "questions": qs}],
            })

    # 西经/政经：章节子目录各有一个选择题集.md，按 ## KPxx 分组，题 id 沿用 data-expl.js 的命名
    else:
        for cd in chapter_dirs:
            cf = cd / "选择题集.md"
            if not cf.exists():
                continue
            cid = cd.name
            cname = parse_chapter_name(cid)
            kps = parse_choice_kp(cf.read_text(encoding="utf-8"), key, cid, cname)
            qs_all = []
            for kp in kps:
                kept = []
                for q in kp["questions"]:
                    explanations[q["id"]] = q.pop("explanation") or ""
                    kept.append(q)
                kp["questions"] = kept
                qs_all.extend(kept)
            if not qs_all:
                continue
            data["choice"]["chapters"].append({
                "id": cid,
                "name": cname,
                "kps": kps,
            })

    # 主观题：优先读科目根目录下的单文件（5 个新科），否则按章节子目录逐个读（西经/政经）
    subj_cfg = (subj_file, subj_mode)
    root_subj = base / subj_cfg[0]
    if root_subj.exists():
        txt = root_subj.read_text(encoding="utf-8")
        # 按 ## 第N章 切分，每章一段，题目编号在全文内连续
        blocks = split_by_heading(txt, r"^##\s+第[0-9一二三四五六七八九十百]+章")
        _CHCN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
        _seen = {}
        for bidx, (btitle, bbody) in enumerate(blocks, 1):
            cname = clean_md(strip_quan(re.sub(r"^#+\s*", "", btitle.strip()))) or ("第%d章" % bidx)
            # 章号改用标题里的数字（"第3章" -> 3），使简答题 id 的章段与选择题 id 对齐；
            # 同一章号重复出现时依次加偏移，杜绝 id 撞车。
            m_no = re.search(r"第\s*([0-9]+|[一二三四五六七八九十]+)\s*章", btitle)
            cno = bidx
            if m_no:
                t = m_no.group(1)
                cno = int(t) if t.isdigit() else _CHCN.get(t, bidx)
            _seen[cno] = _seen.get(cno, 0) + 1
            cno_eff = cno + 100 * (_seen[cno] - 1)
            # 两种写法都支持：**N. 题干** + **答：**（综合评价/计量/统计原理），
            # 以及 ### 子标题 + **答题要点：**（时间序列/多元统计）。
            subj = parse_subjective_simple(bbody, key, "C%02d" % cno_eff, cname, root_subj)
            if not subj["short_questions"]:
                subj = parse_subjective_heading(bbody, key, "C%02d" % cno_eff, cname, root_subj)
            if not subj["short_questions"] and not subj["essay_questions"]:
                continue
            data["subjective"]["chapters"].append({
                "id": "C%02d" % bidx,
                "name": cname,
                "short_questions": subj["short_questions"],
                "essay_questions": subj["essay_questions"],
            })
        chapter_dirs = []

    for cd in chapter_dirs:
        f = cd / subj_cfg[0]
        if not f.exists():
            continue
        cid = cd.name
        cname = parse_chapter_name(cid)
        txt = f.read_text(encoding="utf-8")
        if subj_cfg[1] == "simple":
            subj = parse_subjective_simple(txt, key, cid, cname, f)
        else:
            subj = parse_subjective_kaoyan(txt, key, cid, cname, f)
        if not subj["short_questions"] and not subj["essay_questions"]:
            continue
        data["subjective"]["chapters"].append({
            "id": cid,
            "name": cname,
            "short_questions": subj["short_questions"],
            "essay_questions": subj["essay_questions"],
        })

    return data, explanations


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    keys = [only] if only else list(SUBJECTS.keys())
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_c = total_s = total_e = 0

    for key in keys:
        if key not in SUBJECTS:
            print("未知科目: %s（可选: %s）" % (key, ", ".join(SUBJECTS)))
            return 1
        data, expl = build_subject(key)
        n_c = sum(len(kp["questions"])
                  for ch in data["choice"]["chapters"] for kp in ch["kps"])
        n_s = sum(len(ch["short_questions"]) for ch in data["subjective"]["chapters"])
        n_e = sum(len(ch["essay_questions"]) for ch in data["subjective"]["chapters"])
        total_c += n_c
        total_s += n_s
        total_e += n_e

        out = ROOT / ("data-%s.js" % key)
        body = ("// 自动生成，请勿手动编辑——科目：%s\n// 生成时间: %s\n" % (data["name"], stamp))
        body += "window.EXAM_SUBJECT_DATA = window.EXAM_SUBJECT_DATA || {};\n"
        body += "window.EXAM_SUBJECT_DATA[%s] = %s;\n" % (
            json.dumps(key), json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        out.write_text(body, encoding="utf-8")

        eout = ROOT / ("data-expl-%s.js" % key)
        ebody = ("// 自动生成，请勿手动编辑——科目 %s 的选择题解析，按需加载\n// 生成时间: %s\n" % (data["name"], stamp))
        ebody += "window.EXAM_SUBJECT_EXPL = window.EXAM_SUBJECT_EXPL || {};\n"
        ebody += "window.EXAM_SUBJECT_EXPL[%s] = %s;\n" % (
            json.dumps(key), json.dumps(expl, ensure_ascii=False, separators=(",", ":")))
        eout.write_text(ebody, encoding="utf-8")

        print("[%s] %s  章 %d / 选择 %d / 简答 %d / 论述 %d  → %s (%.1f KB) + %s (%.1f KB)" % (
            key, data["name"],
            len(data["choice"]["chapters"]), n_c, n_s, n_e,
            out.name, out.stat().st_size / 1024,
            eout.name, eout.stat().st_size / 1024))

    print("\n合计：选择 %d / 简答 %d / 论述 %d" % (total_c, total_s, total_e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
