import { describe, it, expect } from "vitest";
import { buildTimeline } from "../timeline";

describe("buildTimeline", () => {
  it("marks only steps present in history; no fake progress", () => {
    const t = buildTimeline([{ new_status: "submitted", created_at: "x" }, { new_status: "assigned", created_at: "y" }]);
    expect(t.map((s) => s.reached)).toEqual([true, true, false, false]);
    expect(t[1].current).toBe(true);
  });
  it("empty history reaches nothing", () => {
    expect(buildTimeline([]).some((s) => s.reached)).toBe(false);
  });
  it("adds rejected step", () => {
    expect(buildTimeline([{ new_status: "Rejected" }]).at(-1).status).toBe("rejected");
  });
});
