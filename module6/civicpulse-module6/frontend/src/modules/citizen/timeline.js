export const STEPS = ["submitted", "assigned", "in_progress", "resolved"];
const norm = (s) => (s || "").toLowerCase().replace(/[\s-]+/g, "_");

/** Build timeline strictly from status_history. A step is "reached" only if a history row exists for it. */
export function buildTimeline(history = []) {
  const byStatus = {};
  history.forEach((h) => { byStatus[norm(h.new_status)] = h; }); // latest row per status wins
  const steps = STEPS.map((s) => ({ status: s, reached: !!byStatus[s], entry: byStatus[s] || null }));
  if (byStatus.rejected) steps.push({ status: "rejected", reached: true, entry: byStatus.rejected });
  const lastReached = steps.map((s) => s.reached).lastIndexOf(true);
  return steps.map((s, i) => ({ ...s, current: i === lastReached }));
}
