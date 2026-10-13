"""Exercise the SHIPPED web engine (web/app.js) against the new assets.

Runs the real `precomputeSections` / `sectionContent` / `isMetaIntro` /
`buildExamPlan` functions extracted from web/app.js, so both clients are held to
the same guarantee: every day resolves to its own item, every exam has a pool.
"""
import json
import subprocess
import sys

NODE = r"C:\Users\welcome\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe"

JS = r"""
const fs = require('fs');
const appJs = fs.readFileSync('web/app.js', 'utf8');

function slice(from, to) {
  const a = appJs.indexOf(from);
  const b = appJs.indexOf(to);
  if (a < 0 || b < 0 || b <= a) { console.error('cannot slice', from, '->', to); process.exit(1); }
  return appJs.slice(a, b);
}

const engine = slice('const META_INTRO_SECTIONS', 'function planForDay')
  + "\n" + slice('function seededShuffle', 'function buildActivity');

const state = {
  content: JSON.parse(fs.readFileSync('app/src/main/assets/content.json', 'utf8')),
  course: JSON.parse(fs.readFileSync('app/src/main/assets/course.json', 'utf8')),
  sectionCache: new Map(),
};
const api = new Function('state', engine + '; return { precomputeSections, sectionContent, sectionIntros, isMetaIntro, buildExamPlan, META_INTRO_SECTIONS };')(state);
api.precomputeSections();

const problems = [];
const days = state.course.days;
const lessons = days.filter(d => !d.is_exam);

// 1. every lesson resolves
for (const d of lessons) {
  const items = api.sectionContent(d.section_id);
  if (!items.length) { problems.push(`day ${d.day}: no content for ${d.section_id}`); continue; }
  const prior = days.filter(x => x.section_id === d.section_id && !x.is_exam && x.day < d.day).length;
  const item = items[prior] || items[items.length - 1];
  if (!item || !item.text || !item.text.trim()) problems.push(`day ${d.day}: empty item text`);
}

// 2. no two lessons in a chapter teach the same item
const bySid = {};
for (const d of lessons) (bySid[d.section_id] ||= []).push(d);
for (const [sid, ds] of Object.entries(bySid)) {
  const items = api.sectionContent(sid);
  if (ds.length > items.length) problems.push(`${sid}: ${ds.length} days > ${items.length} items`);
  const seen = new Set();
  ds.sort((a, b) => a.day - b.day).forEach((d, i) => {
    const it = items[i] || items[items.length - 1];
    if (seen.has(it.content_id)) problems.push(`${sid}: day ${d.day} repeats ${it.content_id}`);
    seen.add(it.content_id);
  });
}

// 3. exam pools
const exams = days.filter(d => d.is_exam);
const examSizes = [];
for (const e of exams) {
  const p = api.buildExamPlan(e);
  if (p && p.error) { problems.push(`exam day ${e.day}: ${p.error}`); examSizes.push([e.day, 0]); }
  else examSizes.push([e.day, (p.activities || []).length]);
}

// 4. intros still surface
const introSections = [...api.META_INTRO_SECTIONS].filter(s => api.sectionIntros(s).length);
console.log('lessons:', lessons.length, '| exams:', exams.length,
            '| chapters with day-cycles:', Object.keys(bySid).length);
console.log('chapters that render an intro card:', introSections.join(', '));
console.log('exam question counts:', examSizes.map(([d, n]) => `day${d}=${n}`).join(' '));
if (problems.length) {
  console.log('PROBLEMS:'); problems.forEach(p => console.log('  x', p)); process.exit(1);
}
console.log('web engine: OK');
"""

proc = subprocess.run([NODE, "-e", JS], capture_output=True, text=True, encoding="utf-8")
print(proc.stdout)
if proc.stderr:
    print(proc.stderr, file=sys.stderr)
sys.exit(proc.returncode)
