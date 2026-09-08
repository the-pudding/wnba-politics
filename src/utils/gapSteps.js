// The scrolly steps for the outlet-gap charts, read from the Doc.
//
// Fields per step:
//   names:   who to highlight
//   place:   who moves from the starting position to her spot. Placements
//            accumulate down the steps; `all` places everyone; the explore
//            step implies all.
//   center:  who sits on the equal line for this step while still unplaced
//            (dot plot only) — "here is where she'd be if coverage were equal"
//   clip:    a Fox headline clipping shown under the step's text, in the
//            running text's format: tag | date | color | title
//   explore: true — hand over the outlet picker
//
// If no step uses `place`, nobody is staged and every face starts in place.

import { parseClip } from "./clips.js";

const list = (value) =>
	String(value ?? "")
		.split(",")
		.map((n) => n.trim())
		.filter(Boolean);

export function stageSteps(steps) {
	const raw = (steps ?? [])
		// a step needs text to show a card — except the closing explore step,
		// which may be wordless: it just hands the chart over
		.filter(
			(step) =>
				(step.text ?? "").trim() ||
				step.explore === true ||
				step.explore === "true"
		)
		.map((step) => ({
			names: list(step.names ?? step.words),
			place: list(step.place),
			center: list(step.center),
			clip: step.clip ? parseClip(step.clip) : null,
			explore: step.explore === true || step.explore === "true",
			html: step.text ?? ""
		}));
	const staged = raw.some((step) => step.place.length);
	let placed = staged ? [] : null;
	return raw.map((step) => {
		if (placed !== null) {
			if (step.explore || step.place.some((n) => n.toLowerCase() === "all"))
				placed = null;
			else placed = [...placed, ...step.place];
		}
		return { ...step, placed };
	});
}
