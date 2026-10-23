import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

from split_subject_data import ROOT, parse_choice_kp  # noqa: E402


class ChoiceKnowledgePointLinkTests(unittest.TestCase):
    def test_embedded_wikilink_sets_real_file_and_clean_title(self):
        source = ROOT / "教材笔记/06_西方经济学/00_导论/选择题集.md"
        content = source.read_text(encoding="utf-8")

        knowledge_points = parse_choice_kp(
            content,
            "west_econ",
            "00_导论",
            "导论",
            source,
        )
        kp03 = next(item for item in knowledge_points if item["id"] == "KP03")

        self.assertEqual(kp03["name"], "实证分析与规范分析")
        self.assertEqual(
            kp03["file"],
            "教材笔记/06_西方经济学/00_导论/知识点/KP03_实证分析与规范分析.md",
        )


if __name__ == "__main__":
    unittest.main()
