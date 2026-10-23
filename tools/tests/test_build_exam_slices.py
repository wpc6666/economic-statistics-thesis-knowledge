import json
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from build_exam_slices import SUBJECTS, build_subject  # noqa: E402


def read_assignment(path):
    line = path.read_text(encoding="utf-8").splitlines()[-1]
    payload = line.split(" = ", 1)[1].rstrip(";")
    return json.loads(payload)


class ExamSliceBuildTests(unittest.TestCase):
    def test_manifest_slices_preserve_questions_and_explanations(self):
        index_text = (ROOT / "data-index.js").read_text(encoding="utf-8")
        index = json.loads(index_text.split(" = ", 1)[1].rstrip(";\n"))
        self.assertEqual(set(index["subjects"]), set(SUBJECTS))

        for subject in SUBJECTS:
            expected, explanations = build_subject(subject)
            info = index["subjects"][subject]
            choice_qids = set()
            for chapter_ref in info["choice"]:
                chapter = read_assignment(ROOT / chapter_ref["file"])
                self.assertEqual(chapter["id"], chapter_ref["id"])
                self.assertEqual(chapter["name"], chapter_ref["name"])
                qids = {q["id"] for kp in chapter["kps"] for q in kp["questions"]}
                self.assertEqual(len(qids), chapter_ref["count"])
                self.assertTrue(all(qid.startswith(subject + "_" + chapter["id"] + "_") for qid in qids))
                self.assertFalse(choice_qids.intersection(qids))
                choice_qids.update(qids)

                expl_path = ROOT / chapter_ref["explFile"]
                expl = read_assignment(expl_path)
                self.assertEqual(set(expl), qids)
                self.assertEqual(expl, {qid: explanations.get(qid, "") for qid in qids})

            expected_qids = {q["id"] for ch in expected["choice"]["chapters"]
                             for kp in ch["kps"] for q in kp["questions"]}
            self.assertEqual(choice_qids, expected_qids)

            self.assertEqual(len(info["subjective"]), len(expected["subjective"]["chapters"]))
            for ref, chapter in zip(info["subjective"], expected["subjective"]["chapters"]):
                slice_data = read_assignment(ROOT / ref["file"])
                self.assertEqual(slice_data["id"], ref["id"])
                self.assertEqual(slice_data, chapter)
                self.assertEqual(ref["shortCount"], len(chapter["short_questions"]))
                self.assertEqual(ref["essayCount"], len(chapter["essay_questions"]))


if __name__ == "__main__":
    unittest.main()
