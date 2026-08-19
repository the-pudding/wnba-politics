// Tidy Third Eye OCR chyron text for display. The raw feed carries frame
// junk ("| ", ":l", "["), stray lowercase letters dropped mid-line
// ("GRINER. h TO RUSSIAN"), truncated tails, and whole duplicated segments.
export default function cleanChyron(raw, term = "") {
	if (!raw) return "";

	const cleanSeg = (seg) => {
		let toks = seg
			.split(/\s+/)
			// pure punctuation, or punctuation glued to a lone I/l (":I", "| ", "[")
			.filter((tok) => /[A-Za-z0-9]/.test(tok) && !/^[|\[\]:;.,'"]+[Il]?$/.test(tok))
			// stray lowercase single letters are OCR noise in all-caps text
			.filter((tok) => !/^[^A-Za-z0-9]*[a-z][^A-Za-z0-9]*$/.test(tok))
			.map((tok) => tok.replace(/^[|\[\]:;]+/, "").replace(/[|\[\]]+$/, ""));
		// a trailing single letter is almost always a truncation artifact
		while (toks.length && /^[A-Za-z]$/.test(toks[toks.length - 1]) && toks[toks.length - 1] !== "A") {
			toks.pop();
		}
		return toks.join(" ").replace(/\s+/g, " ").trim();
	};

	const segs = raw
		.split(/\s*\/\s*/)
		.map(cleanSeg)
		.filter((s) => s.length > 8);

	// OCR frequently repeats the same line back-to-back, sometimes with a junk
	// tail (a speaker attribution, a truncation) — dedup on letters only,
	// treating prefix-matches as duplicates and keeping the shorter segment
	const uniq = [];
	const key = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "");
	for (const s of segs) {
		const k = key(s);
		const i = uniq.findIndex((u) => {
			const uk = key(u);
			return uk.startsWith(k) || k.startsWith(uk);
		});
		if (i === -1) uniq.push(s);
		else if (s.length < uniq[i].length) uniq[i] = s;
	}

	// when the tooltip is about a specific word, prefer the segment containing it
	const t = term.toLowerCase();
	const hits = t ? uniq.filter((s) => s.toLowerCase().includes(t)) : [];
	let out = (hits.length ? hits : uniq).slice(0, 2).join("  /  ");
	// source strings were clipped at ~150 chars at harvest time — mark the cut
	if (raw.length >= 145 && out.endsWith(uniq[uniq.length - 1] ?? "")) out += "…";
	return out;
}
