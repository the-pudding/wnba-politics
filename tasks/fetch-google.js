import fs from "fs";
import archieml from "archieml";
import docs from "../google.config.js";

const CWD = process.cwd();

const fetchGoogle = async ({ id, gid, sheet }) => {
	console.log(`fetching...${id}`);

	const base = "https://docs.google.com";
	const post = sheet
		? `spreadsheets/d/${id}/export?format=csv${gid ? `&gid=${gid}` : ""}`
		: gid
			? `spreadsheets/u/1/d/${id}/export?format=csv&id=${id}&gid=${gid}`
			: `document/d/${id}/export?format=txt`;
	const url = `${base}/${post}`;

	try {
		const response = await fetch(url);
		const text = await response.text();

		if (gid || sheet) return text;

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
			const str = await fetchGoogle(d);
			const file = `${CWD}/${d.filepath}`;
			fs.writeFileSync(file, str);
		} catch (err) {
			console.log(err);
		}
	}
})();
