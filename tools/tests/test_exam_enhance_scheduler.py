import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class EnhanceSchedulerRegressionTest(unittest.TestCase):
    def test_lazy_mermaid_does_not_requeue_resolved_base_promise(self):
        source = (ROOT / "exam-app.js").read_text(encoding="utf-8")
        match = re.search(
            r"// 公式库未到时只等待 KaTeX 链一次.*?\n(.*?)// mermaid：把",
            source,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match, "未找到 Markdown 增强库调度逻辑")
        scheduler = match.group(1)

        self.assertIn("!window.renderMathInElement", scheduler)
        self.assertIn("data-math-enhance-requested", scheduler)
        self.assertIn("window.__EXAM_MATH_READY.then", scheduler)
        self.assertNotIn("window.__EXAM_LIBS_READY.then", scheduler)
        self.assertNotIn("!window.mermaid", scheduler)
        self.assertNotIn("removeAttribute('data-math-enhance-requested')", scheduler)


if __name__ == "__main__":
    unittest.main()
