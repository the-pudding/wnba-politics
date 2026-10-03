<script>
	// Who Fox News names in WNBA headlines, compared with other outlets: a face
	// per player on a log scale centred on "Same", walked through by the Doc's
	// steps, then explored with an outlet switch.
	//
	//   {.OutletGapScrolly}
	//   heading: How often Fox News names each player in WNBA headlines
	//   comparedWith: compared with    allOutlets: six other outlets combined
	//   [.steps]
	//   names: Caitlin Clark          (lit; "all" for everyone)
	//   place: Caitlin Clark          (placed so far, added up step by step; "all" places everyone)
	//   center: Caitlin Clark         (named at the centre line before she's placed)
	//   text: …                       ((Name| face)) puts a face in the text
	//   explore: true                 (the last step: everyone placed)
	//   []
	//   {}
	// Data: src/data/outlet_gap.json (notebook 02), people.json for the faces.
	import { onMount } from "svelte";
	import { base } from "$app/paths";
	import gap from "$data/outlet_gap.json";
	import roster from "$data/people.json";
	import registry from "$data/outlets.json";
	import { faces, clipPops } from "$utils/clips.js";
	import { LOGO } from "$utils/outlets.js";
	import LogoSelect from "$components/helpers/LogoSelect.svelte";
	import { or } from "$utils/fill.js";

	let {
		steps = [],
		heading = "",
		comparedWith = "",
		allOutlets = "",
		...unused
	} = $props();

	// ---------------------------------------------------------------------
	// Settings
	// ---------------------------------------------------------------------

	// left out, to keep the rows to the players the piece discusses
	const HIDDEN = new Set([
		"Sue Bird",
		"Diana Taurasi",
		"Sabrina Ionescu",
		"Chennedy Carter",
		"Nneka Ogwumike",
		"Candace Parker",
		"Cameron Brink",
		"Kelsey Plum"
	]);
	const HEADING = "How often Fox News names each player in WNBA headlines";
	const EVEN = 1.1; // within 10% either way reads as level: the pale ring
	const REACH = 4; // log2 units either way (16×), past every value in the data
	const SHORT = { "New York Times": "NYT", "Washington Post": "Post" };
	const WIDE = 960; // wider than this: the text beside the chart, not over it
	const TICK_HALF = 10; // half an "8×" label: the heading's edges meet the labels' outer edges

	// ---------------------------------------------------------------------
	// Data
	// ---------------------------------------------------------------------

	const key = (s) => String(s).toLowerCase().replace(/[’‘]/g, "'").trim();
	const list = (v) =>
		String(v ?? "")
			.split(",")
			.map((s) => s.trim())
			.filter(Boolean);
	const fmtN = (n) => n.toLocaleString("en-US");
	const pct = (s) => `${(s * 100).toFixed(s >= 0.1 ? 0 : 1)}%`;
	const times = (k) => `${k.toFixed(k < 10 ? 1 : 0)}×`;
	const surname = (n) => n.split(" ").slice(-1)[0];
	const curly = (n) => n.replace(/'/g, "’");
	const faceOf = (name) =>
		(
			roster[name] ??
			roster[name.replace(/'/g, "’")] ??
			Object.values(roster).find((r) => r.name === name)
		)?.face;

	const OUTLETS = registry.outlets
		.filter((o) => o.group !== "fox")
		.map((o) => o.label);
	const people = gap.people
		.filter((p) => !HIDDEN.has(p.name))
		.map((p) => {
			const face = faceOf(p.name);
			return {
				name: p.name,
				k: key(p.name),
				face: face ? `${base}/net/${face}` : null,
				fox: p.fox,
				foxN: p.foxN,
				by: Object.fromEntries(
					Object.entries(p.byOutlet).map(([o, v]) => [
						o,
						{ share: v.share, n: v.n }
					])
				)
			};
		});

	// the steps: placements add up step by step; `all` or the explore step places everyone
	const raw = (steps ?? [])
		.filter(
			(s) =>
				String(s.text ?? "").trim() ||
				s.explore === true ||
				s.explore === "true"
		)
		.map((s) => ({
			names: list(s.names ?? s.words),
			place: list(s.place),
			center: list(s.center),
			explore: s.explore === true || s.explore === "true",
			html: s.text ?? ""
		}));
	let acc = raw.some((s) => s.place.length) ? [] : null;
	const STEPS = raw.map((s) => {
		if (acc !== null) {
			if (s.explore || s.place.some((n) => key(n) === "all")) acc = null;
			else acc = [...acc, ...s.place];
		}
		return { ...s, placed: acc === null ? null : new Set(acc.map(key)) };
	});

	// what Fox is compared with: the six pooled, or one outlet
	const ALL = "all outlets";
	const withWhom = (o) => {
		const m = registry.members[o];
		if (!m) return o;
		return m.includes(o)
			? `${o} (with ${m.filter((x) => x !== o).join(", ")})`
			: `${o} (${m.join(" and ")})`;
	};
	const CMP = [
		{ id: ALL, short: "others", poss: "the other outlets’" },
		...OUTLETS.map((o) => ({
			id: o,
			label: withWhom(o),
			short: SHORT[o] ?? o,
			poss: `${o}’s`,
			name: o
		}))
	];

	// the outlet in the "compared with" menu; the chart redraws when it changes
	let against = $state(ALL);
	let redraw = () => {};
	const againstName = (id) =>
		id === ALL
			? or(allOutlets, "six other outlets combined")
			: CMP.find((c) => c.id === id).label;

	let root = $state(null);
	const q = (id) => root.querySelector(`[data-id="${id}"]`);

	onMount(() => {
		const NS = "http://www.w3.org/2000/svg";
		let cmp = CMP[0];
		const ratioOf = (p) => p.fox / Math.max(p.by[cmp.id]?.share ?? 0, 1e-9);
		const svg = q("svg"),
			chart = q("chart"),
			sticky = q("sticky"),
			tip = q("tip"),
			headEl = q("head");

		// ---- layout
		let L = {};
		function layout() {
			fit();
			// the heading spans the axis, outer tick label to outer tick label
			// (full width on a phone, where that span is too narrow to read)
			const tall = headEl.offsetHeight;
			headEl.style.paddingInline = L.narrow
				? ""
				: `${Math.max(0, L.x(2 ** -3) - TICK_HALF)}px`;
			if (headEl.offsetHeight !== tall) fit();
		}
		function fit() {
			const W = chart.clientWidth;
			const narrow = W < 560;
			const wide = innerWidth >= WIDE;
			const vh = innerHeight;
			const head = narrow ? 44 : 50;
			const room =
				(wide ? vh - 80 : vh * (narrow ? 0.6 : 0.64)) -
				headEl.offsetHeight -
				head;
			const row = Math.max(
				narrow ? 28 : 32,
				Math.min(narrow ? 36 : 50, room / people.length)
			);
			const R = Math.round(row * 0.42);
			const x0 = W / 2;
			const half = W / 2 - R * 1.2 - 2;
			L = {
				W,
				narrow,
				wide,
				head,
				row,
				R,
				x0,
				H: head + people.length * row + 6,
				x: (k) =>
					x0 + (Math.max(-REACH, Math.min(REACH, Math.log2(k))) / REACH) * half
			};
			sticky.style.top = wide
				? `${Math.max(10, (vh - L.H - headEl.offsetHeight) / 2)}px`
				: "";
		}

		// ---- drawing: built once, then moved
		const make = (tag, attrs = {}, parent) => {
			const n = document.createElementNS(NS, tag);
			for (const [a, v] of Object.entries(attrs)) n.setAttribute(a, v);
			if (parent) parent.appendChild(n);
			return n;
		};
		svg.replaceChildren();
		const defs = make("defs", {}, svg);
		const clipId = "gap-face-" + Math.random().toString(36).slice(2, 7);
		const clipCircle = make(
			"circle",
			{ cx: 0, cy: 0 },
			make("clipPath", { id: clipId, clipPathUnits: "userSpaceOnUse" }, defs)
		);
		const gAxis = make("g", {}, svg);
		const gRows = make("g", {}, svg);
		const rows = new Map();
		for (const p of people) {
			const g = make("g", { class: "row" }, gRows);
			const hit = make("rect", { class: "hit" }, g);
			const stem = make("g", { class: "stem" }, g);
			const line = make("line", { x1: 0, y1: 0, y2: 0 }, stem);
			const label = make("g", { class: "label" }, g);
			const name = make("text", { class: "name", dy: "0.35em" }, label);
			const tName = make("tspan", {}, name);
			make("tspan", {}, name).textContent = " ";
			const tRatio = make("tspan", { class: "ratio" }, name);
			const sub = make("text", { class: "sub" }, label);
			const face = make("g", { class: "face" }, g);
			const grow = make("g", { class: "grow" }, face);
			const bg = make("circle", { fill: "#f7f2e6" }, grow);
			const img = p.face
				? make(
						"image",
						{
							href: p.face,
							preserveAspectRatio: "xMidYMid slice",
							"clip-path": `url(#${clipId})`
						},
						grow
					)
				: null;
			const ring = make("circle", { class: "ring" }, grow);
			rows.set(p.k, {
				p,
				g,
				hit,
				stem,
				line,
				label,
				name,
				tName,
				tRatio,
				sub,
				face,
				grow,
				bg,
				img,
				ring
			});
			g.addEventListener("pointerenter", () => showTip(p));
			g.addEventListener(
				"pointerleave",
				(e) => e.pointerType === "mouse" && hideTip()
			);
			g.addEventListener("click", (e) => {
				e.stopPropagation();
				showTip(p);
			});
		}
		const away = () => hideTip();
		document.addEventListener("click", away);

		function drawAxis() {
			gAxis.replaceChildren();
			const { W, x0, head, H, narrow } = L;
			for (let e = -3; e <= 3; e++) {
				const x = L.x(2 ** e);
				make(
					"line",
					{
						class: `grid${e === 0 ? " mid" : ""}`,
						x1: x,
						x2: x,
						y1: head - 8,
						y2: H - 2
					},
					gAxis
				);
				make(
					"text",
					{
						class: `tick${e === 0 ? " mid" : ""}`,
						x,
						y: head - 14,
						"text-anchor": "middle"
					},
					gAxis
				).textContent = e === 0 ? "Same" : `${2 ** Math.abs(e)}×`;
			}
			make(
				"text",
				{
					class: "dir",
					x: x0 - 12,
					y: 12,
					"text-anchor": "end",
					fill: "var(--others)"
				},
				gAxis
			).textContent = narrow
				? `← ${cmp.short}`
				: `← Bigger share at ${cmp.id === ALL ? "other outlets" : cmp.name}`;
			make(
				"text",
				{ class: "dir", x: x0 + 12, y: 12, fill: "var(--fox)" },
				gAxis
			).textContent = narrow ? "Fox News →" : "Bigger share at Fox News →";
			svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
			svg.setAttribute("height", H);
		}

		// ---- what a step shows
		let step = 0;
		function state() {
			const s = STEPS[step];
			if (!s || s.explore)
				return {
					placed: null,
					centered: new Set(),
					lit: new Set(),
					explore: true
				};
			const all = s.names.some((n) => key(n) === "all");
			return {
				placed: s.placed,
				centered: new Set(s.center.map(key)),
				lit: all ? new Set() : new Set(s.names.map(key)),
				explore: false
			};
		}
		function render() {
			const S = state();
			const { x0, row, R, head, W, narrow } = L;
			clipCircle.setAttribute("r", Math.max(0, R - 1));
			const order = people
				.map((p) => ({ p, k: ratioOf(p) }))
				.sort((a, b) => b.k - a.k);
			// the two shares behind a ratio: for a step's one player, and for Clark
			// in explore, as the key to reading the rest
			const single =
				S.lit.size === 1 ? [...S.lit][0] : S.explore ? "caitlin clark" : null;
			order.forEach(({ p, k }, i) => {
				const r = rows.get(p.k);
				const on = S.placed === null || S.placed.has(p.k);
				const lit = S.lit.has(p.k);
				const named = (S.lit.size ? lit : on) || S.centered.has(p.k);
				const dir = k >= 1 ? 1 : -1;
				const big = Math.max(k, 1 / k);
				const colour =
					big < EVEN ? "var(--even)" : dir > 0 ? "var(--fox)" : "var(--others)";
				const grow = on && lit && S.lit.size > 0 ? 1.2 : 1;
				const fx = on ? L.x(k) : x0;
				const off = Math.abs(fx - x0);
				r.g.style.transform = `translate(0px, ${head + i * row + row / 2}px)`;
				r.g.classList.toggle("dim", on && S.lit.size > 0 && !lit);
				r.g.classList.toggle("waiting", !on && !named);
				r.g.classList.toggle("lit", lit);
				r.hit.setAttribute("x", 0);
				r.hit.setAttribute("width", W);
				r.hit.setAttribute("y", -row / 2);
				r.hit.setAttribute("height", row);
				r.face.style.transform = `translate(${fx}px, 0px)`;
				r.grow.style.transform = `scale(${grow})`;
				r.bg.setAttribute("r", R);
				r.ring.setAttribute("r", R);
				r.ring.style.stroke = on ? colour : "rgba(0,0,0,0.25)";
				if (r.img) {
					r.img.setAttribute("x", -R * 1.2);
					r.img.setAttribute("y", -R * 1.05);
					r.img.setAttribute("width", R * 2.4);
					r.img.setAttribute("height", R * 2.4);
				}
				r.line.setAttribute("x2", dir);
				r.line.style.stroke = colour;
				r.stem.style.transform = `translate(${x0}px, 0px) scaleX(${on ? Math.max(0.001, off - R * grow) : 0.001})`;
				// the name sits in the half the face isn't in, clear of a face near the line
				const gapX = Math.max(10, R * grow - off + 7);
				r.label.style.transform = `translate(${x0 - dir * gapX}px, 0px)`;
				const anchor = dir > 0 ? "end" : "start";
				r.name.setAttribute("text-anchor", anchor);
				r.sub.setAttribute("text-anchor", anchor);
				r.tName.textContent = narrow ? surname(curly(p.name)) : curly(p.name);
				r.tRatio.textContent = on ? times(big) : "";
				r.tRatio.style.fill = colour;
				const showSub = on && single === p.k;
				const fox = pct(p.fox),
					them = pct(p.by[cmp.id].share);
				r.sub.textContent = !showSub
					? ""
					: narrow
						? `Fox ${fox}, ${cmp.short} ${them}`
						: `in ${fox} of Fox’s headlines vs. ${them} of ${cmp.poss}`;
				r.name.setAttribute("y", showSub ? -7 : 0);
				r.sub.setAttribute("y", 12);
			});
		}

		// ---- tooltip
		function showTip(p) {
			const S = state();
			if (!(S.placed === null || S.placed.has(p.k))) return;
			const k = ratioOf(p),
				big = Math.max(k, 1 / k),
				them = p.by[cmp.id];
			const side =
				big < EVEN
					? "About the same share at both."
					: k >= 1
						? `Named in ${times(big)} the share of Fox’s WNBA headlines.`
						: `Named in ${times(big)} the share of ${cmp.poss} WNBA headlines.`;
			tip.innerHTML =
				`<p class="t">${curly(p.name)}</p>` +
				`<p class="cap">Share of WNBA headlines naming her</p>` +
				`<div class="r"><span><i class="sw" style="background:var(--fox)"></i>Fox News</span><span>${pct(p.fox)} · ${fmtN(p.foxN)}</span></div>` +
				`<div class="r"><span><i class="sw" style="background:var(--others)"></i>${cmp.id === ALL ? "Six other outlets" : cmp.id}</span><span>${pct(them.share)} · ${fmtN(them.n)}</span></div>` +
				`<p class="k">${side}</p>`;
			tip.style.display = "block";
			const box = chart.getBoundingClientRect();
			const i = people
				.map((x) => ({ x, k: ratioOf(x) }))
				.sort((a, b) => b.k - a.k)
				.findIndex((o) => o.x === p);
			const y = L.head + i * L.row + L.row / 2;
			const w = tip.offsetWidth,
				h = tip.offsetHeight;
			const above = y - L.R - 8 - h;
			tip.style.left = `${Math.max(0, Math.min(box.width - w, L.x(k) - w / 2))}px`;
			tip.style.top = `${above > 0 ? above : y + L.R + 8}px`;
		}
		const hideTip = () => (tip.style.display = "none");

		// ---- the step text
		const stepsEl = q("steps");
		stepsEl.innerHTML = STEPS.map(
			(s) =>
				`<div class="step"><div class="card"><p>${clipPops(faces(s.html, base), base)}</p></div></div>`
		).join("");
		const stepEls = [...stepsEl.children];
		function onScroll() {
			const line = innerHeight * (L.wide ? 0.55 : 0.8);
			let next = 0;
			stepEls.forEach((d, i) => {
				if (d.querySelector(".card").getBoundingClientRect().top < line)
					next = i;
			});
			if (next !== step) {
				const wasExplore = STEPS[step]?.explore;
				step = next;
				if (wasExplore && !STEPS[step].explore) resetExplore();
				hideTip();
				render();
			}
			stepEls.forEach((d, i) => d.classList.toggle("on", i === step));
		}

		// ---- the outlet switch; leaving explore for the steps resets it
		redraw = (id) => {
			cmp = CMP.find((c) => c.id === id) ?? CMP[0];
			hideTip();
			drawAxis();
			render();
		};
		function resetExplore() {
			if (cmp === CMP[0]) return;
			cmp = CMP[0];
			against = ALL;
			drawAxis();
		}

		// ---- go
		function relayout(animate) {
			if (!animate) svg.classList.add("no-anim");
			layout();
			drawAxis();
			render();
			if (!animate)
				requestAnimationFrame(() =>
					requestAnimationFrame(() => svg.classList.remove("no-anim"))
				);
		}
		relayout(false);
		onScroll();
		let raf;
		const resized = () => {
			cancelAnimationFrame(raf);
			raf = requestAnimationFrame(() => (relayout(false), onScroll()));
		};
		addEventListener("scroll", onScroll, { passive: true });
		addEventListener("resize", resized);
		document.fonts?.ready.then(() => root && relayout(false));
		return () => {
			removeEventListener("scroll", onScroll);
			removeEventListener("resize", resized);
			document.removeEventListener("click", away);
		};
	});
</script>

<figure class="gapfaces" bind:this={root}>
	<div class="scrolly">
		<div class="sticky" data-id="sticky">
			<!-- the title, and who Fox is compared with, as on the words charts -->
			<div class="head" data-id="head">
				<p class="heading">{or(heading, HEADING)}</p>
				<!-- a div, not a p: the menu inside renders block elements -->
				<div class="subheading">
					<span>{or(comparedWith, "compared with")}</span>
					<LogoSelect
						options={CMP.map((c) => c.id)}
						bind:value={against}
						logoOf={(id) => (id === ALL ? null : (LOGO[id] ?? null))}
						nameOf={againstName}
						label="Compared with"
						onchange={(id) => redraw(id)}
					/>
				</div>
			</div>
			<div class="chart" data-id="chart">
				<svg
					data-id="svg"
					role="img"
					aria-label="Each player's share of Fox News WNBA headlines compared with other outlets, on a log scale"
				></svg>
				<div class="tip" data-id="tip"></div>
			</div>
		</div>
		<div class="steps" data-id="steps"></div>
	</div>
</figure>

<style>
	/* on the page, in the airplay style: one accent (Fox navy), the other
	   outlets' side in their site purple, faint brown gridlines. d3-style DOM is built
	   in the script, hence :global */
	.gapfaces {
		--ink: #2a1503;
		--ink-2: rgba(42, 21, 3, 0.82);
		--ink-3: rgba(42, 21, 3, 0.66);
		--rule: rgba(42, 21, 3, 0.18);
		--fox: #003366;
		--others: var(--color-outlets);
		--even: #c2a68c;
		--chart-w: 620px;
		max-width: 1060px;
		margin: 8px auto 0;
		padding: 0 16px;
		color: var(--ink);
		font-family: var(--font-sans);
	}
	/* the text beside the chart on a wide screen */
	.scrolly {
		position: relative;
		display: grid;
		grid-template-columns: 290px minmax(0, 1fr);
		column-gap: 40px;
	}
	.gapfaces :global(.steps) {
		grid-column: 1;
		grid-row: 1;
		padding: 30vh 0 55vh;
	}
	/* the chart and its heading are held to WIDTH, centred in their room */
	.sticky {
		grid-column: 2;
		grid-row: 1;
		position: sticky;
		top: 0;
		align-self: start;
		justify-self: center;
		width: 100%;
		max-width: var(--chart-w);
	}
	.gapfaces :global(.step) {
		min-height: 78vh;
		display: flex;
		align-items: center;
	}
	.gapfaces :global(.card) {
		padding: 16px 20px;
		background: #fff;
		border-radius: 4px;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
		font-family: var(--font-serif);
		font-size: 18px;
		line-height: 1.5;
		color: var(--ink);
		opacity: 0.5;
		transition: opacity 250ms ease;
	}
	.gapfaces :global(.step.on .card) {
		opacity: 1;
	}
	.gapfaces :global(.card p) {
		margin: 0;
	}
	.gapfaces :global(.card a) {
		color: inherit;
		text-underline-offset: 3px;
	}
	.gapfaces :global(.card .fox) {
		color: var(--fox);
		font-weight: 700;
	}
	.gapfaces :global(.card .others),
	.gapfaces :global(.card .other) {
		color: var(--others);
		font-weight: 700;
	}

	/* the title, and who Fox is compared with, as on the words charts */
	.head {
		margin: 0 0 12px;
	}
	.heading {
		margin: 0;
		font-family: var(--font-serif);
		font-size: 22px;
		font-weight: 700;
		line-height: 1.25;
		color: var(--ink);
	}
	.subheading {
		display: flex;
		align-items: center;
		gap: 6px;
		margin: 2px 0 0;
		font-family: var(--font-serif);
		font-size: 17px;
		color: rgba(42, 21, 3, 0.75);
	}
	.subheading > span {
		flex: 0 0 auto;
		white-space: nowrap;
	}
	.subheading :global(.logo-select) {
		flex: 0 1 auto;
		width: auto;
		min-width: 0;
	}
	/* the menu sits in the line as a quiet underlined word */
	.subheading :global(.logo-select .current) {
		height: auto;
		padding: 0 18px 0 0;
		border: 0;
		border-bottom: 1.5px solid currentColor;
		border-radius: 0;
		background: transparent;
		font-family: var(--font-serif);
		font-size: 17px;
		color: var(--ink);
	}
	.subheading :global(.logo-select .current::after) {
		right: 0;
	}

	.chart {
		position: relative;
	}
	.chart svg {
		display: block;
		width: 100%;
		overflow: visible;
	}
	.gapfaces :global(svg text) {
		font-family: var(--font-sans);
	}
	.gapfaces :global(.dir) {
		font-size: 13px;
		font-weight: 700;
	}
	.gapfaces :global(.tick) {
		font-size: 12px;
		fill: var(--ink-3);
		font-variant-numeric: tabular-nums;
	}
	.gapfaces :global(.tick.mid) {
		fill: var(--ink);
		font-weight: 700;
	}
	.gapfaces :global(.grid) {
		stroke: var(--rule);
		stroke-width: 1;
	}
	.gapfaces :global(.grid.mid) {
		stroke: rgba(42, 21, 3, 0.7);
	}
	.gapfaces :global(.row) {
		transition:
			transform 700ms cubic-bezier(0.22, 0.8, 0.3, 1),
			opacity 300ms ease;
	}
	.gapfaces :global(.row.dim) {
		opacity: 0.2;
	}
	.gapfaces :global(.hit) {
		fill: transparent;
	}
	.gapfaces :global(.face),
	.gapfaces :global(.stem),
	.gapfaces :global(.label) {
		transition:
			transform 1000ms cubic-bezier(0.22, 0.8, 0.3, 1),
			opacity 300ms ease;
	}
	.gapfaces :global(.grow) {
		transition: transform 450ms cubic-bezier(0.22, 0.8, 0.3, 1);
	}
	.gapfaces :global(.stem line) {
		stroke-width: 2;
		vector-effect: non-scaling-stroke;
	}
	.gapfaces :global(.ring) {
		fill: none;
		stroke-width: 2;
	}
	.gapfaces :global(.row.waiting .face) {
		opacity: 0.28;
	}
	.gapfaces :global(.row.waiting .label),
	.gapfaces :global(.row.waiting .stem) {
		opacity: 0;
	}
	.gapfaces :global(.name) {
		font-size: 14px;
		fill: var(--ink);
	}
	.gapfaces :global(.row.lit .name) {
		font-weight: 700;
	}
	.gapfaces :global(.ratio) {
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
	.gapfaces :global(.sub) {
		font-size: 12px;
		fill: var(--ink-3);
	}
	.gapfaces :global(.no-anim .row),
	.gapfaces :global(.no-anim .face),
	.gapfaces :global(.no-anim .stem),
	.gapfaces :global(.no-anim .label),
	.gapfaces :global(.no-anim .grow) {
		transition: none !important;
	}

	/* tooltip */
	.gapfaces :global(.tip) {
		position: absolute;
		z-index: 5;
		display: none;
		width: 240px;
		padding: 10px 12px 11px;
		background: #fff;
		border: 1px solid rgba(28, 25, 23, 0.14);
		border-radius: 4px;
		box-shadow:
			0 6px 24px rgba(28, 25, 23, 0.14),
			0 1px 2px rgba(28, 25, 23, 0.06);
		font-size: 12.5px;
		line-height: 1.45;
		color: #4a4a4a;
		pointer-events: none;
	}
	.gapfaces :global(.tip .t) {
		margin: 0 0 3px;
		font: 700 16px/1.25 var(--font-serif);
		color: #1a1a1a;
	}
	.gapfaces :global(.tip .cap) {
		margin: 0 0 4px;
		font-size: 11.5px;
		color: #727272;
	}
	.gapfaces :global(.tip .r) {
		display: flex;
		justify-content: space-between;
		gap: 12px;
	}
	.gapfaces :global(.tip .r span:last-child) {
		font-variant-numeric: tabular-nums;
		color: #1a1a1a;
	}
	.gapfaces :global(.tip .sw) {
		display: inline-block;
		width: 9px;
		height: 9px;
		margin-right: 6px;
		border-radius: 50%;
	}
	.gapfaces :global(.tip .k) {
		margin: 6px 0 0;
		padding-top: 6px;
		border-top: 1px solid #e2e2e2;
		color: #1a1a1a;
	}

	/* narrower screens: the chart sticks at the top and the text cards pass
	   over its foot */
	@media (max-width: 959px) {
		.scrolly {
			display: block;
		}
		.sticky {
			margin: 0 auto;
			height: 100vh;
			height: 100svh;
			padding-top: 10px;
		}
		.gapfaces :global(.steps) {
			position: relative;
			z-index: 2;
			margin-top: -100vh;
			margin-top: -100svh;
			padding: 0 0 115vh;
			pointer-events: none;
		}
		/* the last card scrolls fully off before the chart lets go */
		.gapfaces :global(.step) {
			min-height: 100vh;
			min-height: 100svh;
			align-items: flex-end;
			justify-content: center;
			padding-bottom: 7vh;
		}
		.gapfaces :global(.step:first-child) {
			min-height: 115vh;
		}
		.gapfaces :global(.card) {
			max-width: 460px;
			padding: 12px 14px;
			font-size: 16px;
			opacity: 1;
			background: rgba(255, 255, 255, 0.96);
		}
		.gapfaces :global(.card a) {
			pointer-events: auto;
		}
	}
	@media (max-width: 600px) {
		.gapfaces {
			padding: 0 2px;
		}
		.heading {
			font-size: 18px;
		}
		.subheading,
		.subheading :global(.logo-select .current) {
			font-size: 15px;
		}
		.gapfaces :global(.name) {
			font-size: 12.5px;
		}
		.gapfaces :global(.sub) {
			font-size: 11px;
		}
		.gapfaces :global(.dir) {
			font-size: 12px;
		}
		.gapfaces :global(.tick) {
			font-size: 11px;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.gapfaces :global(.row),
		.gapfaces :global(.face),
		.gapfaces :global(.stem),
		.gapfaces :global(.label),
		.gapfaces :global(.grow) {
			transition: none !important;
		}
	}
</style>
