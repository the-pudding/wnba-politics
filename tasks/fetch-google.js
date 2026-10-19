import fs from "fs";
import archieml from "archieml";
import docs from "../google.config.js";

const CWD = process.cwd();

// `tab`: a Doc with several tabs exports only its first one unless the tab's
// id (the "tab=t.…" part of the Doc's URL when that tab is open) is given
const fetchGoogle = async ({ id, gid, sheet, tab }) => {
	console.log(`fetching...${id}${tab ? ` (tab ${tab})` : ""}`);

	const base = "https://docs.google.com";
	const post = sheet
		? `spreadsheets/d/${id}/export?format=csv${gid ? `&gid=${gid}` : ""}`
		: gid
			? `spreadsheets/u/1/d/${id}/export?format=csv&id=${id}&gid=${gid}`
			: `document/d/${id}/export?format=txt${tab ? `&tab=${tab}` : ""}`;
	const url = `${base}/${post}`;

	try {
		const response = await fetch(url);
		let text = await response.text();

		if (gid || sheet) return text;

		// a mistyped link in the Doc ("<href =”url” target=_blank>") opens an
		// unknown element the browser parses differently from the server, and
		// hydration fails: repair the common form and say so
		const repaired = text.replace(/<href\s*=\s*[”"“]([^”"“]+)[”"“]\s*target=_blank>/g, '<a href="$1" target="_blank" rel="noopener">');
		if (repaired !== text) console.warn("⚠️  repaired a mistyped <href> link in the Doc; fix it there too");
		text = repaired;
		const parsed = archieml.load(text);
		warnUnbalancedTags(text);
		const str = JSON.stringify(parsed);
		return str;
	} catch (err) {
		throw new Error(err);
	}
};

// An unclosed inline tag in the Doc (a typo like "<i>word</>i") leaves the
// tag open for the rest of the page, which breaks hydration and renders the
// whole page twice. Say so at import time, with the offending line.
const warnUnbalancedTags = (text) => {
	const tags = ["i", "em", "b", "strong", "a", "span", "mark", "u", "sup", "sub"];
	const lines = text.split("\n");
	for (const tag of tags) {
		const opens = (text.match(new RegExp(`<${tag}(\\s|>)`, "g")) || []).length;
		const closes = (text.match(new RegExp(`</${tag}>`, "g")) || []).length;
		if (opens === closes) continue;
		console.warn(`⚠️  <${tag}> opened ${opens} times but closed ${closes} in the Doc`);
		// point at lines where this tag opens without closing, or closes oddly
		for (const [i, line] of lines.entries()) {
			const o = (line.match(new RegExp(`<${tag}(\\s|>)`, "g")) || []).length;
			const c = (line.match(new RegExp(`</${tag}>`, "g")) || []).length;
			if (o !== c || /<\/>/.test(line))
				console.warn(`    line ${i + 1}: ${line.trim().slice(0, 120)}`);
		}
	}
	if (/<\/>/.test(text)) console.warn('⚠️  a stray "</>" in the Doc — a mistyped closing tag');
};

(async () => {
	for (let d of docs) {
		try {
			let str = await fetchGoogle(d);
			// a sheet row whose cells were cleared instead of deleted comes down as
			// ",,": an empty term matches every sentence (it made every player
			// 100% political), so blank rows are dropped here
			if (d.sheet) {
				const lines = str.split(/\r?\n/);
				const kept = lines.filter((line) => line.replace(/[",\s]/g, "") !== "");
				if (kept.length < lines.length)
					console.log(`    dropped ${lines.length - kept.length} blank row(s) from ${d.filepath}`);
				str = kept.join("\n") + "\n";
			}
			const file = `${CWD}/${d.filepath}`;
			fs.writeFileSync(file, str);
		} catch (err) {
			console.log(err);
		}
	}
})();
