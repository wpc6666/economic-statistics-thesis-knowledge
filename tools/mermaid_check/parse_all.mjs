// 用 mermaid 10.9.8 真实解析每个代码块，输出报错的块
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = '/Users/wangpengcheng/IT/03_知识库/综合评价';

// 设置 jsdom 环境
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost/',
  pretendToBeVisual: true,
});
global.window = dom.window;
global.document = dom.window.document;
if (!global.navigator) global.navigator = dom.window.navigator;
global.DOMPurify = undefined;

const mermaid = (await import('mermaid')).default;

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  flowchart: { htmlLabels: true, useMaxWidth: true },
});

// 递归找所有 md 文件
function walk(dir, exts) {
  let out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.')) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (['node_modules', '__pycache__', '.git'].includes(e.name)) continue;
      out = out.concat(walk(p, exts));
    } else if (exts.some(ext => e.name.endsWith(ext))) {
      out.push(p);
    }
  }
  return out;
}

const FENCE_RE = /```[ \t]*mermaid[ \t]*\r?\n([\s\S]*?)```/gi;

const mdFiles = walk(ROOT, ['.md']);
console.error(`扫描到 ${mdFiles.length} 个 md 文件`);

const errors = [];
let totalBlocks = 0;

for (const fp of mdFiles) {
  const text = fs.readFileSync(fp, 'utf-8');
  let m;
  FENCE_RE.lastIndex = 0;
  let idx = 0;
  while ((m = FENCE_RE.exec(text)) !== null) {
    totalBlocks++;
    const code = m[1];
    try {
      // mermaid.parse 返回 promise
      await mermaid.parse(code);
    } catch (e) {
      const rel = path.relative(ROOT, fp);
      const msg = String(e.message || e).split('\n')[0].slice(0, 200);
      errors.push({ file: rel, idx, error: msg, code: code.trim().slice(0, 300) });
    }
    idx++;
  }
}

console.error(`总 mermaid 块: ${totalBlocks}, 报错块: ${errors.length}`);
fs.writeFileSync(
  path.join(__dirname, 'real_errors.json'),
  JSON.stringify({ totalBlocks, errors }, null, 2),
  'utf-8'
);
console.log(JSON.stringify({ totalBlocks, errorCount: errors.length }));
