// Converte o HTML em PDF com o Chromium do Playwright. Uso: node scripts/pdf.js saida/semana-ar.html saida/semana-ar.pdf
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + require('path').resolve(process.argv[2])); await p.waitForTimeout(800);
  await p.emulateMedia({ media: 'print' });
  await p.pdf({ path: process.argv[3], format: 'A4', printBackground: true, margin: { top: '11mm', bottom: '11mm', left: '10mm', right: '10mm' } });
  await b.close();
})();
