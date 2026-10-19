// 用 mermaid.render() 实际渲染修复过的块，确认能生成SVG
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = '/Users/wangpengcheng/IT/03_知识库/综合评价';

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost/', pretendToBeVisual: true,
});
global.window = dom.window;
global.document = dom.window.document;
const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose', flowchart: { htmlLabels: true } });

// 抽样修复过的文件
const samples = [
  ['教材笔记/02_计量经济学/02_数学回顾/00_章节总结.md', [0,1]],
  ['教材笔记/03_时间序列/03_ARMA模型/00_章节总结.md', [1]],
  ['经济统计学论文从0基础到精通/09_时间序列/00_章节总结.md', [0]],
  ['经济统计学论文从0基础到精通/10_论文写作全流程/00_章节总结.md', [0]],
  ['教材笔记/04_多元统计/10_多变量图表示法/00_章节总结.md', [1]],
];

const FENCE_RE = /```[ \t]*mermaid[ \t]*\r?\n([\s\S]*?)```/gi;

let pass = 0, fail = 0;
for (const [relPath, idxs] of samples) {
  const fp = path.join(ROOT, relPath);
  const text = fs.readFileSync(fp, 'utf-8');
  FENCE_RE.lastIndex = 0;
  const blocks = [];
  let m;
  while ((m = FENCE_RE.exec(text)) !== null) blocks.push(m[1]);

  for (const idx of idxs) {
    if (idx >= blocks.length) continue;
    const code = blocks[idx];
    const tmpId = 'test_' + Math.random().toString(36).slice(2);
    try {
      const { svg } = await mermaid.render(tmpId, code);
      const hasSvg = svg.includes('<svg') && svg.length > 100;
      if (hasSvg) {
        console.log(`✅ ${relPath}#${idx} → SVG ${svg.length} bytes`);
        pass++;
      } else {
        console.log(`⚠️ ${relPath}#${idx} → SVG 异常 (${svg.length} bytes)`);
        fail++;
      }
    } catch (e) {
      console.log(`❌ ${relPath}#${idx} → ${String(e.message).split('\n')[0].slice(0,150)}`);
      fail++;
    }
  }
}
console.log(`\n渲染验证: ${pass} 通过, ${fail} 失败`);
