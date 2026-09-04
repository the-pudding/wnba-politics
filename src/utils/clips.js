// A Doc `clip:` line is a Fox headline clipping:
//   clip: tag | date | color | title   (color optional)
// ==word== inside the title is a tinted highlight.

export const PALETTE = {
	green: "#1f9d6e",
	pink: "#d55181",
	purple: "#b04ac2",
	teal: "#17a2b8",
	violet: "#7a6bcc",
	blue: "#2a78d6",
	orange: "#eda100"
};
export const CLIP_BLUE = "#003366";

// ((Caitlin Clark)) in Doc text -> her portrait (the same face the charts use)
// followed by her name; ((Caitlin Clark|face)) -> the portrait alone. A name
// that is not in people.json, or has no portrait, is left as plain text.
import roster from "$data/people.json";
const key = (name) => name.toLowerCase().replace(/[’‘]/g, "'").trim();
const byName = new Map(
	Object.entries(roster).map(([name, p]) => [key(name), p])
);
// Inline pop-ups in Doc text:
//   [[race | June 2026 | pink | Who is X? ... ==word== ...]]  -> a small FOX tag;
//       hovering (or tapping) it pops the headline card up
//   [[img: file.png | a caption]]  -> the same FOX tag, popping the picture
//       (from static/images) with its caption
const escapeAttr = (t) =>
	t.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
export const clipPops = (html, base = "") =>
	String(html ?? "").replace(/\[\[([^\[\]]+?)\]\]/g, (_, inner) => {
		const img = inner.match(/^\s*img:\s*([^|]+?)\s*(?:\|\s*([^]*?))?\s*$/i);
		if (img) {
			const [, file, caption = ""] = img;
			return (
				`<span class="clip-pop">` +
				`<button type="button" class="clip-tag" aria-label="Show the Fox News clip">FOX</button>` +
				`<span class="pop-card pop-image" role="tooltip">` +
				`<img src="${base}/images/${escapeAttr(file.trim())}" alt="${escapeAttr(caption)}" loading="lazy" />` +
				(caption ? `<span class="pop-caption">${caption}</span>` : "") +
				`</span></span>`
			);
		}
		const clip = parseClip(inner);
		const title = hl(clip.title ?? "", CLIP_BLUE);
		const date = clip.date
			? `<span class="pop-date">${escapeAttr(clip.date)}</span>`
			: "";
		return (
			`<span class="clip-pop">` +
			`<button type="button" class="clip-tag" aria-label="Show the Fox News headline">FOX</button>` +
			`<span class="pop-card" role="tooltip"><span class="pop-source">Fox News</span>${date}` +
			`<span class="pop-title">${title}</span></span></span>`
		);
	});

export const faces = (html, base = "") =>
	String(html ?? "").replace(
		/\(\(([^()|]+?)(?:\|\s*(face)\s*)?\)\)/g,
		(_, raw, only) => {
			const name = raw.trim();
			const person = byName.get(key(name));
			if (!person?.face) return name;
			const img = `<img class="face-inline" src="${base}/net/${person.face}" alt="${name}" loading="lazy" />`;
			return only ? img : `<span class="face-name">${img}${name}</span>`;
		}
	);

export const hl = (html, color = "#d55181") =>
	String(html ?? "").replace(
		/==(.+?)==/g,
		(_, w) =>
			`<mark style="background:${color}2e; box-shadow: inset 0 -2px 0 ${color}66">${w}</mark>`
	);

export function parseClip(v) {
	const p = String(v ?? "")
		.split("|")
		.map((s) => s.trim());
	if (p.length >= 4 && (PALETTE[p[2]] || /^#/.test(p[2])))
		return { tag: p[0], date: p[1], title: p.slice(3).join(" | ") };
	if (p.length >= 3)
		return { tag: p[0], date: p[1], title: p.slice(2).join(" | ") };
	if (p.length === 2) return { date: p[0], title: p[1] };
	return { title: v };
}
