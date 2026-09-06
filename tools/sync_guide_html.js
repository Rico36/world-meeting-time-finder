const fs = require('fs');
const path = require('path');
const REPO = path.resolve(__dirname, '..');

const src = fs.readFileSync(path.join(REPO, 'guides.js'), 'utf8');
const dataOnly = src.slice(0, src.indexOf('function renderGuide'));

const sandbox = {};
new Function('exports', dataOnly + '\nexports.guides=guides;exports.guideUi=guideUi;' +
  'exports.guideExpansions=typeof guideExpansions!=="undefined"?guideExpansions:{};' +
  'exports.guideDeepening=typeof guideDeepening!=="undefined"?guideDeepening:{};' +
  'exports.guideReference=typeof guideReference!=="undefined"?guideReference:{};' +
  'exports.holidayGuidePositioning=typeof holidayGuidePositioning!=="undefined"?holidayGuidePositioning:{};' +
  'exports.guideLinks=guideLinks;')(sandbox);

const { guides, guideUi, guideExpansions, guideDeepening, guideReference,
        holidayGuidePositioning, guideLinks } = sandbox;

const FILES = { converter: 'meeting-time-zone-converter.html',
                planner: 'international-meeting-planner.html',
                dst: 'daylight-saving-holidays.html' };

const lang = 'en';
let report = [];

for (const [key, file] of Object.entries(FILES)) {
  const base = Object.assign({}, guides[key][lang],
                key === 'dst' ? (holidayGuidePositioning[lang] || {}) : {});
  const sections = [].concat(base.sections,
    (guideExpansions[key] && guideExpansions[key][lang]) || [],
    (guideDeepening[key] && guideDeepening[key][lang]) || [],
    (guideReference[key] && guideReference[key][lang]) || []);
  const ui = guideUi[lang];

  const body =
    `<p class="eyebrow">${base.eyebrow}</p><h1>${base.heading}</h1>` +
    `<p class="lede">${base.intro}</p>` +
    `<a class="primary-button" href="./">${ui.planner}</a>\n    ` +
    sections.map(([h, c]) =>
      `<section><h2>${h}</h2>` +
      (Array.isArray(c) ? `<ul class="guide-points">${c.map(i => `<li>${i}</li>`).join('')}</ul>`
                        : `<p>${c}</p>`) + `</section>`).join('\n    ') +
    `\n    <aside class="guide-note"><p>${base.note}</p></aside>` +
    `\n    <nav class="guide-nav" aria-label="${ui.more}"><h2>${ui.more}</h2><ul>` +
    Object.entries(guideLinks).filter(([id]) => id !== key)
      .map(([id, url]) => `<li><a href="${url}">${guides[id][lang].heading}</a></li>`).join('') +
    `</ul></nav>`;

  const p = path.join(REPO, file);
  let html = fs.readFileSync(p, 'utf8');
  const open = html.indexOf('<main class="content-page" id="guide-content">');
  const close = html.indexOf('</main>', open);
  if (open === -1 || close === -1) { console.log('SKIP (markers not found):', file); continue; }
  const before = html.slice(0, open + '<main class="content-page" id="guide-content">'.length);
  const after = html.slice(close);
  const out = before + '\n    ' + body + '\n  ' + after;

  // keep <title> and meta description in step with the data
  let final = out
    .replace(/<title>[\s\S]*?<\/title>/, `<title>${base.title}</title>`)
    .replace(/(<meta name="description" content=")[^"]*(")/, `$1${base.description}$2`);

  fs.writeFileSync(p, final, 'utf8');
  const words = body.replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;
  report.push(`  ${file.padEnd(36)} ${sections.length} sections, ${words} words`);
}
console.log(report.join('\n'));
