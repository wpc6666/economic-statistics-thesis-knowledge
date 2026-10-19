// 逐个测试问题块的修复方案
import { JSDOM } from 'jsdom';
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost/', pretendToBeVisual: true,
});
global.window = dom.window;
global.document = dom.window.document;
const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose', flowchart: { htmlLabels: true } });

async function tryParse(label, code) {
  try {
    await mermaid.parse(code);
    console.log(`✅ ${label}`);
    return true;
  } catch (e) {
    console.log(`❌ ${label}: ${String(e.message).split('\n')[0].slice(0,150)}`);
    return false;
  }
}

// #0: 方括号标签含括号逗号
await tryParse('#0 原', `graph TD
    A[标准正态 Z~N(0,1)] -->|平方| B[χ²(1)]`);
await tryParse('#0 修', `graph TD
    A["标准正态 Z~N(0,1)"] -->|平方| B["χ²(1)"]`);

// #1: E(Y|x)=E(Y)
await tryParse('#1 原', `graph TD
    D -->|中等| E[E(Y|x)=E(Y)]
    G -->|最弱| H[Cov(X,Y)=0]`);
await tryParse('#1 修', `graph TD
    D -->|中等| E["E(Y|x)=E(Y)"]
    G -->|最弱| H["Cov(X,Y)=0"]`);

// #2: E(θ̂)=θ
await tryParse('#2 原', `graph TD
    B --> B1[E(θ̂)=θ<br>不系统偏差]`);
await tryParse('#2 修', `graph TD
    B --> B1["E(θ̂)=θ<br>不系统偏差"]`);

// #3: E(y|x) = α + βx
await tryParse('#3 原', `graph TD
    B --> B1[E(y|x) = α + βx<br>真实关系·未知常数]`);
await tryParse('#3 修', `graph TD
    B --> B1["E(y|x) = α + βx<br>真实关系·未知常数"]`);

// #4: 花括号标签含括号
await tryParse('#4 原', `graph TD
    C -->|q阶截尾| E{MA(q)模型}`);
await tryParse('#4 修', `graph TD
    C -->|q阶截尾| E{"MA(q)模型"}`);

// #5: 边标签含 < 和括号
await tryParse('#5 原', `graph TD
    D -->|少(<10)| E[雷达图叠加]
    D -->|多(几十)| F[脸谱图或星图]`);
await tryParse('#5 修a', `graph TD
    D -->|"少(&lt;10)"| E[雷达图叠加]
    D -->|"多(几十)"| F[脸谱图或星图]`);
await tryParse('#5 修b', `graph TD
    D -->|"少于10"| E[雷达图叠加]
    D -->|"多(几十)"| F[脸谱图或星图]`);

// #6: 末尾注释
await tryParse('#6 原', `graph TD
    A["商品(二因素)"] --> B["使用价值?"]   ← 引号、括号、问号都炸`);
await tryParse('#6 修', `graph TD
    A["商品(二因素)"] --> B["使用价值?"]
    %% 引号、括号、问号都炸`);

// #7: 边标签含 [0,1]
await tryParse('#7 原', `graph TD
    CHOICE -->|「要在[0,1]直接加权求和」| USE1["极差归一化"]`);
await tryParse('#7 修', `graph TD
    CHOICE -->|"「要在[0,1]直接加权求和」"| USE1["极差归一化"]`);

// #8: 花括号标签含 I(1)
await tryParse('#8 原', `graph TD
    C -->|「平稳 I(0)」| D["ARMA(p,q)"]
    E --> J{"两个I(1)序列协整？"}`);
await tryParse('#8 修', `graph TD
    C -->|"「平稳 I(0)」"| D["ARMA(p,q)"]
    E --> J{"两个I(1)序列协整？"}`);

// #9: gantt图用了graph TD
await tryParse('#9 原', `graph TD
    title 毕业论文 12 周甘特图
    section 第1阶段：开题
    选题+导师沟通           :a1, 2026-03-02, 7d`);
await tryParse('#9 修', `gantt
    title 毕业论文 12 周甘特图
    section 第1阶段：开题
    选题+导师沟通           :a1, 2026-03-02, 7d`);
