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
		const str = JSON.stringify(parsed);
		return str;
	} catch (err) {
		throw new Error(err);
	}
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
