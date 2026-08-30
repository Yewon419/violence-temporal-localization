export const meta = {
  name: 'xdv-content-review',
  description: 'Full-res subagent review of 5 violence categories: keep only bbox-meaningful action frames',
  phases: [{ title: 'Review', detail: '180 batches across Abuse/Explosion/Fighting/Riot/Shooting' }],
}

const REV = 'C:/Users/windg/Desktop/SCHOOL/3-1/데이터엔지니어링/project2/data/processed/vision_review/review_batches'

const CATS = [
  { cat: 'Abuse', dir: 'Abuse', nb: 2,
    keep: 'the frame visibly shows physical abuse/assault between people: someone hitting, punching, striking, choking, grabbing/dragging, or beating a victim; a clear aggressor physically attacking a victim',
    drop: 'people merely talking, standing, faces/portraits, calm scenes, empty rooms, or any frame with no visible physical assault' },
  { cat: 'Explosion', dir: 'Explosion', nb: 14,
    keep: 'the frame visibly shows an explosion: a fireball, blast, large flames, or a big smoke/debris plume from a blast',
    drop: 'dark aftermath with no visible fire, plain scenes, small irrelevant lights, faces, or any frame with no visible explosion/fire' },
  { cat: 'Fighting', dir: 'Fighting', nb: 45,
    keep: 'the frame visibly shows a physical fight: punching, kicking, grappling, brawling, a melee weapon strike, or people physically clashing in combat',
    drop: 'people standing/talking/posing, aftermath, crowds with no fighting, or any frame with no visible physical combat' },
  { cat: 'Riot', dir: 'Riot', nb: 106,
    keep: 'the frame visibly shows a riot / violent civil unrest: a mob or crowd clashing, charging, fighting police, throwing objects, or fires/smoke in streets during unrest',
    drop: 'calm or sparse crowds, empty streets, a single person, orderly scenes, or any frame with no visible unrest/mass violence' },
  { cat: 'Shooting', dir: 'Shooting', nb: 13,
    keep: 'a firearm is visibly being used or prominently present in a violent context: a person aiming or firing a gun, a muzzle flash, a gun pointed at someone, or someone being shot',
    drop: 'dark ambiguous frames, people with no visible gun, talking scenes, or any frame with no firearm clearly visible' },
]

const SCHEMA = {
  type: 'object',
  properties: {
    total: { type: 'integer' },
    positives: { type: 'array', items: { type: 'integer' } },
  },
  required: ['total', 'positives'],
}

function prompt(c, path) {
  return `You are doing strict visual classification of movie keyframes for a "${c.cat}" object-detection dataset. Keep ONLY frames that are meaningful to draw a bounding box on for this category; drop filler/ambiguous frames.

1. Read the batch list JSON at: ${path} — an array of {idx, path}.
2. For EVERY item, use the Read tool on its "path" to view the image at full resolution. Look at each one individually.
3. POSITIVE (keep) — ${c.keep}.
   NEGATIVE (drop) — ${c.drop}.
   Be STRICT. If uncertain and the defining action/object is not clearly visible, mark NEGATIVE.
4. Call StructuredOutput with: total = number of items reviewed, positives = the list of "idx" values (from the batch file) of POSITIVE frames.`
}

const thunks = []
for (const c of CATS) {
  for (let b = 0; b < c.nb; b++) {
    const bb = String(b).padStart(3, '0')
    const path = `${REV}/${c.dir}/batch_${bb}.json`
    thunks.push(() =>
      agent(prompt(c, path), { label: `${c.cat}:${bb}`, phase: 'Review', schema: SCHEMA })
        .then(r => ({ cat: c.cat, positives: r ? r.positives : [], total: r ? r.total : 0 }))
        .catch(() => ({ cat: c.cat, positives: [], total: 0 }))
    )
  }
}

log(`dispatching ${thunks.length} review batches`)
const results = await parallel(thunks)

const agg = {}
for (const c of CATS) agg[c.cat] = { positives: [], total: 0 }
for (const r of results.filter(Boolean)) {
  agg[r.cat].positives.push(...r.positives)
  agg[r.cat].total += r.total
}
for (const cat in agg) {
  agg[cat].positives = Array.from(new Set(agg[cat].positives)).sort((a, b) => a - b)
  agg[cat].pos = agg[cat].positives.length
}
return agg
