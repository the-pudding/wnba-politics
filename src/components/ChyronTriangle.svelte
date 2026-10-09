<script>
	// The cable news triangle: each word in WNBA chyrons as a dot, placed by how
	// much of its use was on Fox News, CNN or MSNBC
	//
	import { onMount } from "svelte";
	import { base } from "$app/paths";
	import * as d3 from "d3";
	import roster from "$data/people.json";
	import {
		loadTriangle,
		Tern,
		COL,
		fmt,
		pct,
		esc,
		textW,
		leanColor,
		barHTML
	} from "$utils/triangle.js";

	let {
		steps = null,
		topic = "",
		firstWords = "",
		tryWords = "",
		...unused
	} = $props();

	// ---------------------------------------------------------------------
	// Settings
	// ---------------------------------------------------------------------

	// the first step's words: the ones in the chyron shown with it
	// ("CLARK HIT IN THROAT DURING LOOSE-BALL SCRAMBLE")
	const FIRST_WORDS = ["clark", "hit", "throat", "ball"];
	const TRY_WORDS = [
		"kanter",
		"engelbert",
		"shooting",
		"vote",
		"loeffler",
		"throat"
	];
	const TOPIC_LABELS = 7; // topic words labelled on a topic triangle (the most used)
	const WIDE = 860; // wider than this: the cards beside the triangle, not over it
	const CARD_COLUMN = 360; // room the cards take on the left, wide screens
	const EXPLORE_GAP = 14; // px between the triangle and the explore card, narrow screens

	// ---------------------------------------------------------------------

	const words = (s, fallback) =>
		String(s ?? "").trim()
			? String(s)
					.split(",")
					.map((w) => w.trim().toLowerCase())
					.filter(Boolean)
			: fallback;

	// people with a face, for "caitlin, clark" groups and ((Name| face)) in the text
	const FACES = new Map(
		Object.entries(roster)
			.filter(([, p]) => p.face)
			.map(([name, p]) => [
				name.toLowerCase(),
				{ name, face: `${base}/net/${p.face}` }
			])
	);
	const person = (group) => FACES.get(group.join(" ").toLowerCase()) ?? null;
	function facesIn(html) {
		return String(html ?? "").replace(
			/\(\(([^()|]+?)(?:\|\s*(face)\s*)?\)\)/g,
			(_, raw, only) => {
				const p = FACES.get(raw.trim().toLowerCase());
				if (!p) return raw.trim();
				const img = `<img class="face-inline" src="${p.face}" alt="${esc(p.name)}">`;
				return only ? img : `<span class="nowrap">${img}${esc(p.name)}</span>`;
			}
		);
	}
	const parseGroups = (step) =>
		String(step.groups ?? "").trim()
			? step.groups
					.split(/\/+/)
					.map((b) =>
						b
							.split(",")
							.map((w) => w.trim().toLowerCase())
							.filter(Boolean)
					)
					.filter((b) => b.length)
			: [];

	let root = $state(null);
	const el = (id) => root.querySelector(`[data-id="${id}"]`);

	onMount(() => {
		const cleanup = [];
		let alive = true;
		loadTriangle().then((D) => {
			if (!alive) return;
			if (steps) buildScrolly(D, cleanup);
			else buildTopic(D, cleanup);
			// labels are measured in Atlas: redraw once it has loaded
			document.fonts?.ready.then(
				() =>
					alive && cleanup.terns?.forEach((t) => (t.layout(), t.render(false)))
			);
		});
		return () => {
			alive = false;
			cleanup.forEach((f) => f());
		};
	});

	// one row per word or group: its name, a stacked bar (Fox | CNN | MSNBC), Fox's share
	function shareRows(rows, { removable = false, labelW = null } = {}) {
		if (!rows.length) return "";
		// the label column fits the longest label, so the bars line up
		const need =
			d3.max(
				rows,
				(r) =>
					textW(r.label, 13) +
					(r.face ? 28 : 0) +
					(r.uses != null ? textW(fmt(r.uses), 11.5, 400) + 6 : 0) +
					(removable ? 18 : 0)
			) + 4;
		labelW = Math.min(170, Math.max(labelW || 0, Math.ceil(need)));
		return (
			`<div class="shares" style="--lw:${labelW}px"><div class="shares-head"><span></span><span class="legend"><i style="color:${COL.fox}">Fox</i><i style="color:${COL.cnn}">CNN</i><i style="color:${COL.msnbcText}">MSNBC</i></span><span>Fox</span></div>` +
			rows
				.map(
					(r) =>
						`<div class="srow" data-k="${esc(r.key)}"><span class="who">${r.face ? `<img src="${r.face}" alt="">` : ""}<span>${esc(r.label)}</span>${r.uses != null ? `<small>${fmt(r.uses)}</small>` : ""}${removable ? `<button class="x" data-x="${esc(r.key)}" aria-label="Remove ${esc(r.label)}">×</button>` : ""}</span>${barHTML(r.s)}<span class="pct" style="color:${leanColor(r.s)}">${pct(r.s[0])}</span></div>`
				)
				.join("") +
			`</div>`
		);
	}

	// ---- the walk-through ----------------------------------------------------
	function buildScrolly(D, cleanup) {
		const { TERMS, BY, sharesOf } = D;
		const groupRow = (g) => {
			const pts = g.map((w) => BY.get(w)).filter(Boolean);
			const counts = [0, 1, 2].map((i) => d3.sum(pts, (p) => p.c[i]));
			const p = person(g);
			return {
				key: g.join(","),
				label: p ? p.name : g.join(", "),
				face: p?.face,
				s: sharesOf(counts),
				uses: null
			};
		};
		const STEPS = steps
			.filter(
				(s) => String(s.text ?? "").trim() || parseGroups(s).length || s.search
			)
			.map((s) => ({
				groups: parseGroups(s),
				img: String(s.img ?? "").trim(),
				search: s.search === true || s.search === "true",
				html: s.text ?? ""
			}));
		const wide = () => innerWidth > WIDE;
		const host = el("tern");
		const tern = new Tern(host, D, {
			maxSide: 640,
			maxHeight: () =>
				wide() ? innerHeight - 52 : Math.min(innerHeight * 0.55, 470)
		});
		cleanup.terns = [tern];
		cleanup.push(() => tern.destroy());
		// on wide screens the triangle sits right of the card column
		const fit = () => {
			host.style.marginLeft = wide() ? CARD_COLUMN + "px" : "0";
			host.style.width = wide() ? `calc(100% - ${CARD_COLUMN}px)` : "100%";
		};
		fit();

		const stepsEl = el("steps");
		const tryList = words(tryWords, TRY_WORDS);
		stepsEl.innerHTML = STEPS.map((s, i) => {
			if (s.search)
				return `<div class="step explore" data-i="${i}"><div class="step-card">
					<p class="step-text">${facesIn(s.html)}</p>
					<div class="find"><input data-id="find" type="search" placeholder="Find a word…" autocomplete="off" spellcheck="false" aria-label="Find a word"><ul class="sugg" data-id="sugg" role="listbox"></ul></div>
					<p class="hint" data-id="hint"></p>
					<p class="try" data-id="try">Try ${tryList.map((w) => `<button data-try="${esc(w)}">${esc(w)}</button>`).join(" · ")}</p>
					<div class="kept" data-id="kept"></div>
					<div class="floor" data-id="floor"><span>Show</span><button data-f="1">All words</button><button data-f="10" class="on">10+ uses</button><button data-f="100">100+ uses</button></div>
				</div></div>`;
			const img = s.img
				? `<img class="step-img" src="${base}/images/${esc(s.img)}" alt="">`
				: "";
			return `<div class="step" data-i="${i}"><div class="step-card"><p class="step-text">${facesIn(s.html)}</p>${img}${shareRows(s.groups.map(groupRow))}</div></div>`;
		}).join("");

		// a step card's share rows point at their dots in the triangle
		stepsEl.addEventListener("pointerover", (e) => {
			const row = e.target.closest(".srow");
			if (!row) return;
			tern.hover =
				row.dataset.k
					.split(",")
					.map((w) => tern.by.get(w))
					.filter(Boolean)
					.sort((a, b) => b.total - a.total)[0] || null;
			tern.drawTip();
		});
		stepsEl.addEventListener("pointerout", (e) => {
			if (e.target.closest(".srow")) {
				tern.hover = null;
				tern.drawTip();
			}
		});

		const first = words(firstWords, FIRST_WORDS);
		const X = { q: "", picked: [], floor: 10, cursor: -1, lastKept: null };
		let current = -1;
		function stateFor(i) {
			const s = STEPS[i];
			if (!s) return;
			if (s.search) return exploreState();
			const lit = new Map(),
				labels = [],
				groups = [];
			for (const g of s.groups) {
				const p = person(g);
				const color = leanColor(groupRow(g).s);
				g.forEach((w) => BY.get(w) && lit.set(w, leanColor(BY.get(w).s)));
				groups.push({ terms: g });
				// a person: one label with the face; other words, a label each
				if (p) {
					labels.push({ terms: g, text: p.name, face: p.face, color });
				} else
					g.forEach(
						(w) =>
							BY.get(w) &&
							labels.push({
								terms: [w],
								text: w,
								color: leanColor(BY.get(w).s)
							})
					);
			}
			// the first step: the words of the chyron in its picture, the zones named
			if (i === 0)
				for (const w of first) {
					const t = BY.get(w);
					if (!t) continue;
					lit.set(w, leanColor(t.s));
					labels.push({ terms: [w], text: w, color: leanColor(t.s) });
				}
			return { lit, labels, groups, floor: 10, pin: null, zoneStrong: i === 0 };
		}
		function exploreState() {
			const q = X.q.trim().toLowerCase();
			const exact = q && BY.get(q) ? q : null;
			const partial =
				q && !exact
					? TERMS.filter((t) => t.term.includes(q))
							.slice(0, 30)
							.map((t) => t.term)
					: [];
			const lit = new Map(),
				labels = [];
			for (const w of [...X.picked, ...(exact ? [exact] : [])]) {
				const t = BY.get(w);
				lit.set(w, leanColor(t.s));
				labels.push({ terms: [w], text: w, color: leanColor(t.s) });
			}
			for (const w of partial) {
				const t = BY.get(w);
				lit.set(w, leanColor(t.s));
				if (partial.length <= 6)
					labels.push({ terms: [w], text: w, color: leanColor(t.s) });
			}
			// on a phone the kept word is listed in the card instead: a pinned tooltip would cover the triangle
			return {
				lit,
				labels,
				groups: [],
				floor: X.floor,
				pin: exact || (wide() ? X.lastKept : null) || null,
				zoneStrong: true
			};
		}
		function go(i) {
			if (i === current) return;
			current = i;
			stepsEl
				.querySelectorAll(".step")
				.forEach((s) => s.classList.toggle("on", +s.dataset.i === i));
			tern.hover = null;
			tern.set(stateFor(i));
		}
		function onScroll() {
			const line = innerHeight * (wide() ? 0.55 : 0.75);
			let active = 0;
			stepsEl.querySelectorAll(".step").forEach((s) => {
				if (s.querySelector(".step-card").getBoundingClientRect().top < line)
					active = +s.dataset.i;
			});
			go(active);
			holdExplore();
		}
		// the explore card is held mid-screen on wide screens, and just under the
		// triangle on narrower ones; the room below it makes it let go exactly
		// when the triangle does
		function holdExplore() {
			const step = stepsEl.querySelector(".step.explore"),
				card = step?.querySelector(".step-card");
			if (!card) return root.style.removeProperty("--explore-room");
			const past =
				step.getBoundingClientRect().bottom -
				root.getBoundingClientRect().bottom;
			if (wide())
				return root.style.setProperty(
					"--explore-room",
					Math.max(0, past + innerHeight / 2 - card.offsetHeight) + "px"
				);
			const svg = root.querySelector(".tern svg"),
				graphic = root.querySelector(".graphic");
			if (!svg || !graphic) return;
			const top =
				svg.getBoundingClientRect().bottom -
				graphic.getBoundingClientRect().top +
				EXPLORE_GAP;
			root.style.setProperty("--tern-bottom", top + "px");
			root.style.setProperty(
				"--explore-room",
				Math.max(0, past + innerHeight - top - card.offsetHeight) + "px"
			);
		}
		// checked again on the next frame: a sticky card settles after the scroll event
		const scrolled = () => (onScroll(), requestAnimationFrame(onScroll));
		const resized = () => (
			fit(),
			tern.layout(),
			tern.render(false),
			onScroll()
		);
		addEventListener("scroll", scrolled, { passive: true });
		addEventListener("resize", resized);
		cleanup.push(
			() => removeEventListener("scroll", scrolled),
			() => removeEventListener("resize", resized)
		);
		onScroll();

		// ---- explore
		const input = el("find");
		if (!input) return;
		const sugg = el("sugg"),
			hint = el("hint"),
			keptEl = el("kept");
		const refresh = () => STEPS[current]?.search && tern.set(exploreState());
		const suggestions = () => {
			const q = X.q.trim().toLowerCase();
			if (!q) return [];
			return [
				...TERMS.filter((t) => t.term.startsWith(q)),
				...TERMS.filter((t) => !t.term.startsWith(q) && t.term.includes(q))
			].slice(0, 8);
		};
		function drawSugg() {
			const list = suggestions();
			if (!list.length || document.activeElement !== input)
				return (sugg.style.display = "none");
			sugg.innerHTML = list
				.map(
					(t, i) =>
						`<li data-w="${esc(t.term)}" class="${i === X.cursor ? "on" : ""}"><b>${esc(t.term)}</b><small><i>${fmt(t.total)}</i><span style="color:${leanColor(t.s)}">Fox ${pct(t.s[0])}</span></small></li>`
				)
				.join("");
			sugg.style.display = "block";
		}
		function drawHint() {
			const q = X.q.trim().toLowerCase();
			if (!q) return (hint.textContent = "");
			if (BY.get(q)) return (hint.textContent = `Press Enter to keep “${q}”.`);
			const n = TERMS.filter((t) => t.term.includes(q)).length;
			hint.textContent = !n
				? `No chyron word contains “${q}”.`
				: n > 30
					? `${n} words contain “${q}”; the 30 most used are lit.`
					: `${n} word${n === 1 ? "" : "s"} contain${n === 1 ? "s" : ""} “${q}”.`;
		}
		function drawKept() {
			keptEl.innerHTML = shareRows(
				X.picked.map((w) => ({
					key: w,
					label: w,
					s: BY.get(w).s,
					uses: BY.get(w).total
				})),
				{ removable: true, labelW: 132 }
			);
		}
		function keep(w) {
			if (!BY.get(w)) return;
			if (!X.picked.includes(w)) X.picked.unshift(w);
			X.lastKept = w;
			X.q = input.value = "";
			X.cursor = -1;
			drawSugg();
			drawHint();
			drawKept();
			refresh();
		}
		input.addEventListener("input", () => {
			X.q = input.value;
			X.cursor = -1;
			X.lastKept = null;
			drawSugg();
			drawHint();
			refresh();
		});
		input.addEventListener("focus", drawSugg);
		input.addEventListener("blur", () =>
			setTimeout(() => (sugg.style.display = "none"), 120)
		);
		input.addEventListener("keydown", (e) => {
			const list = suggestions();
			if (e.key === "ArrowDown") {
				X.cursor = Math.min(X.cursor + 1, list.length - 1);
				drawSugg();
				e.preventDefault();
			} else if (e.key === "ArrowUp") {
				X.cursor = Math.max(X.cursor - 1, -1);
				drawSugg();
				e.preventDefault();
			} else if (e.key === "Enter")
				keep(X.cursor >= 0 ? list[X.cursor]?.term : X.q.trim().toLowerCase());
			else if (e.key === "Escape") sugg.style.display = "none";
		});
		sugg.addEventListener("pointerdown", (e) => {
			const li = e.target.closest("li");
			if (li) {
				e.preventDefault();
				keep(li.dataset.w);
			}
		});
		el("try").addEventListener("click", (e) => {
			const b = e.target.closest("button");
			if (b) keep(b.dataset.try);
		});
		keptEl.addEventListener("click", (e) => {
			const x = e.target.closest("[data-x]");
			if (!x) return;
			X.picked = X.picked.filter((w) => w !== x.dataset.x);
			X.lastKept = null;
			drawKept();
			refresh();
		});
		keptEl.addEventListener("pointerover", (e) => {
			const r = e.target.closest(".srow");
			if (r) {
				tern.hover = tern.by.get(r.dataset.k);
				tern.drawTip();
			}
		});
		keptEl.addEventListener("pointerout", (e) => {
			if (e.target.closest(".srow")) {
				tern.hover = null;
				tern.drawTip();
			}
		});
		el("floor").addEventListener("click", (e) => {
			const b = e.target.closest("button");
			if (!b) return;
			X.floor = +b.dataset.f;
			el("floor")
				.querySelectorAll("button")
				.forEach((x) => x.classList.toggle("on", x === b));
			refresh();
		});
		drawKept();
	}

	// ---- one topic's triangle ---------------------------------------------
	function buildTopic(D, cleanup) {
		const list = (D.topics[topic] ?? [])
			.map((w) => D.BY.get(w))
			.filter(Boolean);
		const tern = new Tern(el("tern"), D, { maxSide: 420 });
		cleanup.terns = [tern];
		cleanup.push(() => tern.destroy());
		const labelled = list
			.slice()
			.sort((a, b) => b.total - a.total)
			.filter((w) => w.total >= 4)
			.slice(0, TOPIC_LABELS);
		tern.set(
			{
				// each word in the colour of the zone it sits in
				lit: new Map(list.map((w) => [w.term, leanColor(w.s)])),
				floor: 10,
				groups: [],
				labels: labelled.map((w) => ({
					terms: [w.term],
					text: w.term,
					color: leanColor(w.s)
				}))
			},
			false
		);
	}
</script>

{#if steps}
	<section class="tri scrolly" bind:this={root}>
		<div class="graphic"><div class="tern" data-id="tern"></div></div>
		<div class="steps" data-id="steps"></div>
	</section>
{:else}
	<div class="tri topic" bind:this={root}>
		<div class="tern tern-solo" data-id="tern"></div>
	</div>
{/if}

<style>
	/* d3 and the step cards' HTML build most of this, hence :global */
	.tri {
		--ink: #1a1a1a;
		--ink-2: #4a4a4a;
		--ink-3: #727272;
		--rule: #e2e2e2;
		--card: #fff;
		color: var(--ink);
		font-family: var(--font-sans);
	}
	.tri :global(*) {
		box-sizing: border-box;
	}

	/* the walk-through: the triangle pinned, the cards scrolling past it */
	.scrolly {
		position: relative;
		max-width: 1080px;
		margin: 0 auto;
		padding: 0 16px;
	}
	.tri :global(.graphic) {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100svh;
		display: flex;
		align-items: center;
		padding: 16px 0;
	}
	.tri :global(.tern) {
		position: relative;
		width: 100%;
	}
	.tri :global(.tern svg) {
		display: block;
		overflow: visible;
	}
	.tri :global(.steps) {
		position: relative;
		z-index: 2;
		margin-top: -100vh;
		margin-top: -100svh;
		pointer-events: none;
	}
	.tri :global(.step) {
		min-height: 100vh;
		min-height: 100svh;
		display: flex;
		align-items: center;
	}
	.tri :global(.step-card) {
		pointer-events: auto;
		width: 340px;
		background: var(--card);
		border-radius: 4px;
		padding: 16px 18px;
		box-shadow: 0 2px 14px rgba(42, 21, 3, 0.16);
		opacity: 0.35;
		transition: opacity 240ms ease;
	}
	.tri :global(.step.on .step-card) {
		opacity: 1;
	}
	.tri :global(.step-text) {
		margin: 0;
		font-family: var(--font-serif);
		font-size: 17px;
		line-height: 1.5;
	}
	.tri :global(.step-text .fox),
	.tri :global(.step-text .others) {
		font-family: var(--font-sans);
		font-size: 0.93em;
		font-weight: 700;
	}
	.tri :global(.step-text .fox) {
		color: var(--wnba-red);
	}
	.tri :global(.step-text .others) {
		color: var(--wnba-purple);
	}
	.tri :global(.step-img) {
		display: block;
		width: 100%;
		height: auto;
		margin: 12px 0 0;
		border-radius: 3px;
		border: 1px solid var(--rule);
	}
	.tri :global(.face-inline) {
		display: inline-block;
		width: 1.45em;
		height: 1.45em;
		border-radius: 50%;
		object-fit: cover;
		object-position: 50% 20%;
		vertical-align: -0.38em;
		margin: 0 0.15em 0 0.1em;
		background: #f1ebe2;
	}
	.tri :global(.nowrap) {
		white-space: nowrap;
	}
	/* explore: on wide screens the card is held mid-screen beside the triangle
	   and lets go with it (the room below it is set by the script) */
	.tri :global(.step.explore) {
		min-height: 150vh;
		align-items: flex-start;
		padding-bottom: var(--explore-room, 0px);
	}
	.tri :global(.step.explore .step-card) {
		position: sticky;
		top: 50vh;
		transform: translateY(-50%);
		margin-top: 50vh;
	}

	/* the share list: one stacked bar per word, Fox | CNN | MSNBC */
	.tri :global(.shares) {
		margin: 14px 0 0;
		font-size: 13px;
	}
	.tri :global(.shares-head),
	.tri :global(.srow) {
		display: grid;
		grid-template-columns: var(--lw, 118px) minmax(0, 1fr) 46px;
		gap: 8px;
	}
	.tri :global(.shares-head) {
		font-size: 11.5px;
		font-weight: 700;
		color: var(--ink-3);
		margin-bottom: 4px;
	}
	.tri :global(.shares-head span:last-child) {
		text-align: right;
	}
	.tri :global(.shares-head i) {
		font-style: normal;
	}
	.tri :global(.shares-head .legend) {
		display: flex;
		gap: 7px;
		white-space: nowrap;
	}
	.tri :global(.srow) {
		align-items: center;
		height: 28px;
		border-radius: 3px;
	}
	.tri :global(.srow:hover) {
		background: #f5f2ec;
	}
	.tri :global(.srow .who) {
		display: flex;
		align-items: center;
		gap: 6px;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		min-width: 0;
	}
	.tri :global(.srow .who img) {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		object-fit: cover;
		object-position: 50% 20%;
		flex: 0 0 auto;
		background: #f1ebe2;
	}
	.tri :global(.srow .who small) {
		font-weight: 400;
		color: var(--ink-3);
		font-size: 11.5px;
	}
	.tri :global(.srow .who .x) {
		appearance: none;
		border: 0;
		background: none;
		font: 400 15px var(--font-sans);
		color: var(--ink-3);
		cursor: pointer;
		padding: 0 2px;
		line-height: 1;
	}
	.tri :global(.sbar) {
		display: flex;
		height: 10px;
		border-radius: 2px;
		overflow: hidden;
		background: #eee;
	}
	.tri :global(.sbar span) {
		display: block;
		height: 100%;
	}
	.tri :global(.sbar span + span) {
		box-shadow: inset 1px 0 0 #fff;
	}
	.tri :global(.srow .pct) {
		text-align: right;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	/* the explore controls */
	.tri :global(.find) {
		position: relative;
		margin: 12px 0 0;
	}
	.tri :global(.find input) {
		width: 100%;
		height: 32px;
		padding: 0 10px 0 30px;
		border: 1px solid #cfcac2;
		border-radius: 16px;
		font: 15px var(--font-sans);
		color: var(--ink);
		-webkit-appearance: none;
		appearance: none;
		background: #fff
			url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23727272' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-4-4'/%3E%3C/svg%3E")
			no-repeat 11px 50%;
	}
	.tri :global(.find input:focus) {
		outline: none;
		border-color: var(--ink);
	}
	.tri :global(.sugg) {
		position: absolute;
		left: 0;
		right: 0;
		top: 37px;
		z-index: 6;
		margin: 0;
		padding: 4px 0;
		list-style: none;
		background: #fff;
		border: 1px solid var(--rule);
		border-radius: 6px;
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.14);
		display: none;
	}
	.tri :global(.sugg li) {
		display: flex;
		justify-content: space-between;
		gap: 10px;
		padding: 6px 12px;
		font-size: 14px;
		cursor: pointer;
	}
	.tri :global(.sugg li.on),
	.tri :global(.sugg li:hover) {
		background: #f4f2ee;
	}
	.tri :global(.sugg li small) {
		font-size: 12px;
		font-weight: 700;
		white-space: nowrap;
	}
	.tri :global(.sugg li small i) {
		font-style: normal;
		font-weight: 400;
		color: var(--ink-3);
		margin-right: 6px;
	}
	.tri :global(.hint) {
		margin: 6px 0 0;
		font-size: 12.5px;
		line-height: 1.4;
		color: var(--ink-3);
		min-height: 1em;
	}
	.tri :global(.try) {
		margin: 8px 0 0;
		font-size: 12.5px;
		color: var(--ink-3);
	}
	.tri :global(.try button) {
		appearance: none;
		border: 0;
		border-radius: 0;
		background: none;
		padding: 0;
		margin: 0 2px;
		font: 700 12.5px var(--font-sans);
		color: var(--ink);
		text-decoration: underline;
		text-decoration-color: #cfcac2;
		text-underline-offset: 3px;
		cursor: pointer;
	}
	.tri :global(.floor) {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 12px;
		margin: 12px 0 0;
		padding-top: 10px;
		border-top: 1px solid var(--rule);
		font-size: 12.5px;
		color: var(--ink-3);
	}
	.tri :global(.floor button) {
		appearance: none;
		border: 0;
		border-radius: 0;
		background: none;
		padding: 0 0 2px;
		font: 700 12.5px var(--font-sans);
		color: var(--ink-3);
		cursor: pointer;
		border-bottom: 2px solid transparent;
	}
	.tri :global(.floor button.on) {
		color: var(--ink);
		border-bottom-color: var(--ink);
	}
	.tri :global(.kept) {
		max-height: 30vh;
		overflow-y: auto;
	}

	/* the triangle: pale cream on the page, no sheet behind it */
	.tri :global(.bed) {
		fill: rgba(255, 250, 242, 0.55);
	}
	.tri :global(.frame) {
		fill: none;
		stroke: rgba(42, 21, 3, 0.25);
		stroke-width: 1;
	}
	.tri :global(.zone-label),
	.tri :global(.centre-label) {
		font-size: 10.5px;
		font-weight: 700;
		letter-spacing: 0.07em;
		text-transform: uppercase;
		paint-order: stroke;
		stroke: #fff;
		stroke-width: 3px;
		stroke-linejoin: round;
		pointer-events: none;
		transition: opacity 300ms ease;
	}
	.tri :global(.centre-label) {
		fill: var(--wnba-tan-dark);
	}
	.tri :global(.corner) {
		font-size: 15px;
		font-weight: 700;
	}
	.tri :global(.dot.lit) {
		stroke: #fff;
		stroke-width: 1.5;
	}
	.tri :global(.ring) {
		fill: none;
		stroke: var(--ink);
		stroke-width: 1.5;
		pointer-events: none;
	}
	.tri :global(.wlabel) {
		font-size: 13px;
		font-weight: 700;
		paint-order: stroke;
		stroke: #fff;
		stroke-width: 3.5px;
		stroke-linejoin: round;
		pointer-events: none;
	}
	.tri :global(.leader) {
		stroke: var(--ink-3);
		stroke-width: 0.8;
		fill: none;
	}
	.tri :global(.pair) {
		stroke-width: 1.5;
		stroke-linecap: round;
		opacity: 0.55;
	}

	/* tooltip */
	.tri :global(.tip) {
		position: absolute;
		z-index: 5;
		pointer-events: none;
		width: 236px;
		padding: 10px 12px 11px;
		background: #fff;
		border: 1px solid rgba(28, 25, 23, 0.14);
		border-radius: 4px;
		box-shadow:
			0 6px 24px rgba(28, 25, 23, 0.14),
			0 1px 2px rgba(28, 25, 23, 0.06);
		font-size: 12.5px;
		line-height: 1.45;
		color: var(--ink-2);
		display: none;
	}
	.tri :global(.tip .w) {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
		font-size: 16px;
		font-weight: 700;
		color: var(--ink);
		margin-bottom: 6px;
	}
	.tri :global(.tip .w small) {
		font-size: 12px;
		font-weight: 400;
		color: var(--ink-3);
	}
	.tri :global(.tip .shares) {
		display: grid;
		grid-template-columns: auto auto;
		justify-content: space-between;
		row-gap: 1px;
		margin: 0;
		font-variant-numeric: tabular-nums;
		color: var(--ink);
	}
	.tri :global(.tip .shares span) {
		display: contents;
	}
	.tri :global(.tip .shares i) {
		font-style: normal;
		text-align: right;
	}
	.tri :global(.tip .ex) {
		margin: 8px 0 0;
		padding-left: 8px;
		border-left: 2px solid var(--rule);
		font-family: var(--font-serif);
		font-size: 13px;
		line-height: 1.4;
		color: var(--ink-2);
	}
	.tri :global(.tip .ex span) {
		display: block;
		font-family: var(--font-sans);
		font-size: 11.5px;
		color: var(--ink-3);
	}

	/* a topic's triangle, on its own */
	.tri :global(.tern-solo) {
		max-width: 520px;
		margin: 8px auto 18px;
	}

	/* narrower screens: the triangle pinned at the top, the cards passing under it */
	@media (max-width: 860px) {
		.scrolly {
			padding: 0;
		}
		.tri :global(.graphic) {
			align-items: flex-start;
			padding: 8px 12px 0;
		}
		.tri :global(.steps) {
			padding: 0 12px;
		}
		.tri :global(.step) {
			align-items: flex-end;
			padding-bottom: 3vh;
		}
		.tri :global(.step-card) {
			width: 100%;
			padding: 13px 15px;
		}
		.tri :global(.step-text) {
			font-size: 16px;
		}
		.tri :global(.step-img) {
			max-height: 22vh;
			object-fit: cover;
			object-position: 50% 100%;
		}
		/* explore: comes up from below and is held just under the triangle */
		.tri :global(.step.explore) {
			min-height: 200vh;
			align-items: flex-start;
		}
		.tri :global(.step.explore .step-card) {
			top: var(--tern-bottom, 50vh);
			margin-top: 70vh;
			transform: none;
		}
		/* suggestions open upward, clear of the phone keyboard */
		.tri :global(.sugg) {
			top: auto;
			bottom: 37px;
		}
		.tri :global(.kept) {
			max-height: 18vh;
		}
	}
	@media (max-width: 640px) {
		/* the bar legend's network names, small enough to stay clear of "Fox" */
		.tri :global(.shares-head .legend) {
			gap: 5px;
			font-size: 10.5px;
		}
		.tri :global(.wlabel) {
			font-size: 12.5px;
		}
		.tri :global(.corner) {
			font-size: 14px;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.tri :global(.step-card),
		.tri :global(.zone-label) {
			transition: none;
		}
	}
</style>
