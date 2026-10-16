// People's names in a headline, underlined in their group's colour: the
// network map's groups (league, politics, commentators, anti-trans,
// celebrities). Names match by people.json's patterns, which know Ryan Clark
// isn't Caitlin, else by the full name or the surname, capitalized.
import people from "$data/people.json";
import net from "$data/network_map.json";

// the network map's group colours (NetworkMap reads them from here too)
export const GROUP_COLOR = {
	league: "#FA4D00",
	politics: "#166534",
	media: "#191919",
	antitrans: "#6B1D91",
	celebs: "#7C7060"
};
// people.json's groups, for anyone the network map doesn't have
const FROM_PEOPLE = {
	players: "league",
	league: "league",
	media: "media",
	politics: "politics"
};

const groupOf = new Map(net.nodes.map((n) => [n.name, n.group]));
const escRx = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const MATCHERS = [...new Set([...Object.keys(people), ...groupOf.keys()])]
	.map((name) => {
		const group = groupOf.get(name) ?? FROM_PEOPLE[people[name]?.group];
		const last = name.split(" ").slice(-1)[0];
		// the full name always counts, then their own pattern or the surname
		const pattern =
			escRx(name) + "|" + (people[name]?.rx ?? `\\b${escRx(last)}\\b`);
		try {
			return { name, color: GROUP_COLOR[group], rx: new RegExp(pattern, "gi") };
		} catch {
			return null;
		}
	})
	.filter((m) => m?.color);

// wrap each name in a headline's HTML (text only, never inside a tag); `only`
// limits it to the people known to be in the headline
export function markNames(html, only = null) {
	const list = only ? MATCHERS.filter((m) => only.includes(m.name)) : MATCHERS;
	return html
		.split(/(<[^>]+>)/)
		.map((part) => {
			if (part.startsWith("<")) return part;
			const hits = [];
			for (const m of list) {
				m.rx.lastIndex = 0;
				for (const hit of part.matchAll(m.rx)) {
					// names are capitalized: "bird" is not Sue Bird
					if (hit[0] && /[A-Z]/.test(hit[0][0]))
						hits.push({
							at: hit.index,
							end: hit.index + hit[0].length,
							color: m.color
						});
				}
			}
			// the earliest first, the longest where two start together; no overlaps
			hits.sort((a, b) => a.at - b.at || b.end - a.end);
			let out = "",
				from = 0;
			for (const h of hits) {
				if (h.at < from) continue;
				out +=
					part.slice(from, h.at) +
					`<span class="name-line">${part.slice(h.at, h.end)}</span>`;
				from = h.end;
			}
			return out + part.slice(from);
		})
		.join("");
}
