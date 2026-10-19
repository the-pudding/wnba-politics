// A Doc `clip:` line is a Fox headline clipping:
//   clip: tag | date | color | title   (color optional)
// ==word== inside the title is a tinted highlight.

export const PALETTE = {
	green: "var(--color-politics)",
	pink: "var(--color-race)",
	purple: "var(--color-lgbtq)",
	teal: "var(--color-trans)",
	violet: "var(--color-chip)",
	blue: "var(--color-clark)",
	orange: "var(--color-gold)"
};
export const CLIP_BLUE = "var(--color-fox-navy)";

// ((Caitlin Clark)) in Doc text -> her portrait (the same face the charts use)
// followed by her name; ((Caitlin Clark|face)) -> the portrait alone. A name
// that is not in people.json, or has no portrait, is left as plain text.
import roster from "$data/people.json";
const key = (name) => name.toLowerCase().replace(/[’‘]/g, "'").trim();
const byName = new Map(
	Object.entries(roster).map(([name, p]) => [key(name), p])
);
// Inline pop-ups in Doc text:
//   [[race | June 2026 | pink | Who is X? ... ==word== ...]]  -> a small newspaper badge;
//       hovering (or tapping) it pops the headline card up
//   [[img: file.png | a caption]]  -> a lower-third badge, popping the picture
//       (from static/images) with its caption
//   [[icon]]  -> the newspaper badge on its own (no pop-up), to introduce it earlier
const escapeAttr = (t) =>
	t.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
// the badge glyphs: a folded newspaper (headline pops) and a lower-third bar (image pops)
const NEWSPAPER =
	'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h14v2h2v13a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V4h1zm2 2v13a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V8h-2V6H6zm2 2h5v5H8V8zm7 0h2v2h-2V8zm0 3h2v2h-2v-2zM8 14h9v2H8v-2z"/></svg>';
const CHYRON =
	'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 5h20v14H2V5zm2 2v10h16V7H4zm2 7h12v2H6v-2zm0-3h7v1.5H6V11z"/></svg>';
export const clipPops = (html, base = "") =>
	String(html ?? "").replace(/\[\[([^\[\]]+?)\]\]/g, (_, inner) => {
		// [[icon]] on its own: the badge with no pop-up, for introducing it in the text
		if (/^\s*(icon|ref)\s*$/i.test(inner))
			return `<span class="clip-tag static" aria-hidden="true">${NEWSPAPER}</span>`;
		const img = inner.match(/^\s*img:\s*([^|]+?)\s*(?:\|\s*([^]*?))?\s*$/i);
		if (img) {
			const [, file, caption = ""] = img;
			return (
				`<span class="clip-pop">` +
				`<button type="button" class="clip-tag" aria-label="Show the Fox News clip">${CHYRON}</button>` +
				`<span class="pop-card pop-image" role="tooltip">` +
				`<img src="${base}/images/${escapeAttr(file.trim())}" alt="${escapeAttr(caption)}" loading="lazy" />` +
				(caption ? `<span class="pop-caption">${caption}</span>` : "") +
				`</span></span>`
			);
		}
		const clip = parseClip(inner);
		const title = hl(faces(clip.title ?? "", base), CLIP_BLUE);
		const date = clip.date
			? `<span class="pop-date">${escapeAttr(clip.date)}</span>`
			: "";
		return (
			`<span class="clip-pop">` +
			`<button type="button" class="clip-tag" aria-label="Show the Fox News headline">${NEWSPAPER}</button>` +
			`<span class="pop-card" role="tooltip"><span class="pop-source">Fox News</span>${date}` +
			`<span class="pop-title">${title}</span></span></span>`
		);
	});

// Google Docs smart-quotes the `"` around an href (<a href="…”>), which
// leaves the attribute open: the browser then swallows the rest of the
// paragraph into it, the server and client trees disagree, and hydration
// fails — blanking the whole story. Straighten the quotes inside tags.
export const tidy = (html) =>
	balance(
		String(html ?? "").replace(/<[^<>]*>/g, (tag) =>
			tag.replace(/[“”„‟]/g, '"').replace(/[‘’‚‛]/g, "'")
		)
	);

// A mistyped closing tag in the Doc (<span>…</a>) leaves an element open:
// the browser closes it somewhere else than the server did, and hydration
// fails. Drop closers that match nothing and close whatever is left open.
const VOID = /^(br|img|hr|wbr|input|source|meta|link|col|area|embed|track)$/i;
export const balance = (html) => {
	const open = [];
	const out = String(html ?? "").replace(
		/<(\/?)([a-zA-Z][\w-]*)\b[^<>]*?(\/?)>/g,
		(tag, closing, name, selfClosing) => {
			name = name.toLowerCase();
			if (VOID.test(name) || selfClosing) return tag;
			if (!closing) return open.push(name), tag;
			const at = open.lastIndexOf(name);
			if (at < 0) return "";
			// close anything opened inside it that was left open
			const inner = open.splice(at).slice(1).reverse();
			return inner.map((n) => `</${n}>`).join("") + tag;
		}
	);
	return out + open.reverse().map((n) => `</${n}>`).join("");
};

export const faces = (html, base = "") =>
	tidy(html).replace(
		/\(\(([^()|]+?)(?:\|\s*(face)\s*)?\)\)/g,
		(_, raw, only) => {
			const name = raw.trim();
			const person = byName.get(key(name));
			if (!person?.face) return name;
			const img = `<img class="face-inline" src="${base}/net/${person.face}" alt="${name}" loading="lazy" />`;
			return only ? img : `<span class="face-name">${img}${name}</span>`;
		}
	);

// ==word== anywhere (Doc text, clip titles, network headlines): the yellow
// marker pen the foul reel uses, one highlighter across the piece
// (styled by mark.pen in app.css). `color` is no longer used.
export const hl = (html, color = null) =>
	tidy(html).replace(/==(.+?)==/g, (_, w) => `<mark class="pen">${w}</mark>`);

export function parseClip(v) {
	// a ((Name|face)) token carries a pipe of its own: shield it from the split
	const shielded = String(v ?? "").replace(
		/\(\(([^()|]+)\|([^()]+)\)\)/g,
		(_, name, flag) => `((${name}\u00a6${flag}))`
	);
	const p = shielded.split("|").map((s) => s.trim().replace(/\u00a6/g, "|"));
	if (p.length >= 4 && (PALETTE[p[2]] || /^#/.test(p[2])))
		return { tag: p[0], date: p[1], title: p.slice(3).join(" | ") };
	// "June 2026 | pink | headline": a colour in the second slot, so no tag
	if (p.length >= 3 && (PALETTE[p[1]] || /^#/.test(p[1])))
		return { date: p[0], title: p.slice(2).join(" | ") };
	if (p.length >= 3)
		return { tag: p[0], date: p[1], title: p.slice(2).join(" | ") };
	if (p.length === 2) return { date: p[0], title: p[1] };
	return { title: v };
}
