#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成答题页用的轻量索引与按章选择题切片。"""
import hashlib
import json
from pathlib import Path

from split_subject_data import ROOT, SUBJECTS, build_subject


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write_slice(path, expression, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "window.%s = window.%s || {};\n" % (expression, expression)
    subject, chapter_id = value["subject"], value["chapter"]["id"]
    body += "window.%s[%s] = window.%s[%s] || {};\n" % (
        expression, compact_json(subject), expression, compact_json(subject))
    body += "window.%s[%s][%s] = %s;\n" % (
        expression, compact_json(subject), compact_json(chapter_id), compact_json(value["chapter"]))
    path.write_text(body, encoding="utf-8")


def write_explanations(path, subject, chapter_id, explanations):
    body = "window.EXAM_EXPL_SLICES = window.EXAM_EXPL_SLICES || {};\n"
    body += "window.EXAM_EXPL_SLICES[%s] = window.EXAM_EXPL_SLICES[%s] || {};\n" % (
        compact_json(subject), compact_json(subject))
    body += "window.EXAM_EXPL_SLICES[%s][%s] = %s;\n" % (
        compact_json(subject), compact_json(chapter_id), compact_json(explanations))
    path.write_text(body, encoding="utf-8")


def build():
    index = {"subjects": {}}
    fingerprints = []
    for key, (_, display, _, _) in SUBJECTS.items():
        data, explanations = build_subject(key)
        choice_rows = []
        for idx, chapter in enumerate(data["choice"]["chapters"]):
            chapter = dict(chapter)
            count = sum(len(kp["questions"]) for kp in chapter["kps"])
            digest = hashlib.sha256(compact_json(chapter).encode("utf-8")).hexdigest()[:10]
            filename = "data-slices/%s-choice-%03d-%s.js" % (key, idx, digest)
            write_slice(ROOT / filename, "EXAM_CHAPTER_DATA", {"subject": key, "chapter": chapter})
            fingerprints.append(digest)
            qids = [q["id"] for kp in chapter["kps"] for q in kp["questions"]]
            chapter_explanations = {qid: explanations.get(qid, "") for qid in qids}
            expl_digest = hashlib.sha256(compact_json(chapter_explanations).encode("utf-8")).hexdigest()[:10]
            expl_filename = "data-slices/%s-expl-%03d-%s.js" % (key, idx, expl_digest)
            write_explanations(ROOT / expl_filename, key, chapter["id"], chapter_explanations)
            fingerprints.append(expl_digest)
            choice_rows.append({
                "id": chapter["id"], "name": chapter["name"], "file": filename,
                "explFile": expl_filename, "count": count,
                "kps": [{"id": kp["id"], "name": kp["name"], "file": kp.get("file", "")}
                        for kp in chapter["kps"]],
            })
        subjective_rows = [
            {"id": ch["id"], "name": ch["name"],
             "shortCount": len(ch["short_questions"]), "essayCount": len(ch["essay_questions"]),
             "file": "data-slices/%s-subjective-%03d-%s.js" % (
                 key, idx, hashlib.sha256(compact_json(ch).encode("utf-8")).hexdigest()[:10])}
            for idx, ch in enumerate(data["subjective"]["chapters"])
        ]
        for idx, chapter in enumerate(data["subjective"]["chapters"]):
            digest = hashlib.sha256(compact_json(chapter).encode("utf-8")).hexdigest()[:10]
            write_slice(ROOT / subjective_rows[idx]["file"], "EXAM_SUBJECTIVE_DATA",
                        {"subject": key, "chapter": chapter})
            fingerprints.append(digest)
        index["subjects"][key] = {
            "name": display, "choice": choice_rows, "subjective": subjective_rows,
            "shortCount": sum(row["shortCount"] for row in subjective_rows),
            "essayCount": sum(row["essayCount"] for row in subjective_rows),
        }
    index["version"] = hashlib.sha256("".join(fingerprints).encode("ascii")).hexdigest()[:16]
    out = ROOT / "data-index.js"
    out.write_text("window.EXAM_DATA_INDEX = %s;\n" % compact_json(index), encoding="utf-8")
    return out


if __name__ == "__main__":
    output = build()
    print("生成章节索引与选择题切片：%s" % output)
