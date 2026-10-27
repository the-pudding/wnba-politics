<script>
	// The outlet-gap dot plot and the chyron ternary as one scrolly: the dot
	// plot's steps, then a stretch of scrolling where each player's face flies
	// to her surname's dot on the triangle, then the triangle's steps. Doc
	// options on the block:
	//   [.steps]         the dot plot's steps (as on OutletGapScrolly)
	//   [.ternarySteps]  the triangle's steps (as on TernaryScrollyOld); a step's
	//                    topic (polrace, lgbtq, fouls) shades the triangle's heat
	//   bridge           a card that scrolls by during the handoff
	//   heading, comparedWith, allOutlets, speed  (the dot plot's)
	//   note             (the triangle's line underneath)
	//   The find box sits under the triangle on every step; a step with
	//   `search: true` is a pause with no card, the triangle moved to the middle.
	//   bands            true/false: shade the triangle's "mostly Fox / CNN /
	//                    MSNBC" corners (default true); a ternary step's own
	//                    bands overrides it while that step is up; always
	//                    off through the bridge
	import { base } from "$app/paths";
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import OutletGapDotPlot from "$components/OutletGapDotPlot.svelte";
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import gapData from "$data/outlet_gap.json";
	import chy from "$data/chyrons.json";
	import chyYears from "$data/chyron_ternary_years.json";
	import roster from "$data/people.json";
	import { stageSteps } from "$utils/gapSteps.js";
	import { faces, clipPops } from "$utils/clips.js";
	import { or } from "$utils/fill.js";
	import { cubicInOut } from "svelte/easing";

	let {
		steps = null,
		ternarySteps = null,
		bridge = "",
		speed = 1000,
		heading = "",
		comparedWith = "",
		allOutlets = "",
		note = null,
		bands = true
	} = $props();
	// the Doc sends "true"/"false" as text; blank means "not set"
	const flag = (v) => {
		const s = String(v ?? "")
			.trim()
			.toLowerCase();
		return s === "" ? null : !["false", "no", "off", "0"].includes(s);
	};

	// the triangle's title when the Doc gives none (the dot plot's own)
	const HEADING = "The words used in Fox News television chyrons";

	// --- the dot plot's steps -----------------------------------------------
	const GAP = $derived(stageSteps(steps));
	let gapIndex = $state(0);
	let gapLast = $state(0);
	$effect(() => {
		if (gapIndex !== undefined && gapIndex !== null) gapLast = gapIndex;
	});

	// --- the triangle's steps (read as TernaryScrolly reads them) -------------
	const parseGroups = (step) => {
		const raw = (step.groups ?? step.words ?? "").trim();
		if (!raw) return [];
		return raw
			.split(/\/+/)
			.map((band) =>
				band
					.split(",")
					.map((w) => w.trim())
					.filter(Boolean)
			)
			.filter((band) => band.length);
	};
	const TER = $derived(
		(ternarySteps ?? [])
			.filter(
				(step) =>
					(step.text ?? "").trim() ||
					(step.title ?? "").trim() ||
					parseGroups(step).length ||
					step.search ||
					(step.topic ?? "").trim()
			)
			.map((step) => ({
				title: (step.title ?? "").trim(),
				groups: parseGroups(step),
				// polrace, lgbtq or fouls: light that topic's words and shade
				// the triangle where they cluster (TernaryStatic's heat)
				topic: (step.topic ?? "").trim() || null,
				img: (step.img ?? "").trim(),
				search: step.search === true || step.search === "true",
				bands: flag(step.bands),
				rows: parseGroups(step).map(shareRow).filter(Boolean),
				html: step.text ?? ""
			}))
	);
	// --- the cards' share bars (as on ChyronTriangle) ------------------------
	// each network's chyron total over every year: a group's shares are its
	// words' summed counts as rates of these, normalised across the three (the
	// same sum that places the dots on TernaryStatic)
	const TOTALS = [0, 1, 2].map((i) =>
		Object.values(chyYears.totals ?? {}).reduce(
			(sum, t) => sum + (t[i] ?? 0),
			0
		)
	);
	const COUNTS = new Map((chy.ternary ?? []).map((t) => [t.term, t]));
	// names keyed loosely: "a’ja, wilson" in the Doc finds A'ja Wilson
	const nameKey = (s) => s.toLowerCase().replace(/[’‘]/g, "'");
	const FACES = new Map(
		Object.entries(roster)
			.filter(([, p]) => p.face)
			.map(([name, p]) => [
				nameKey(name),
				{ name, face: `${base}/net/${p.face}` }
			])
	);
	// "A'ja Wilson" → "A. Wilson": first initial, then the rest of the name
	const initialName = (name) => {
		const [first, ...rest] = name.trim().split(/\s+/);
		return rest.length ? `${first[0]}. ${rest.join(" ")}` : first;
	};
	const shareRow = (group) => {
		const pts = group.map((w) => COUNTS.get(w.toLowerCase())).filter(Boolean);
		if (!pts.length) return null;
		const rates = [0, 1, 2].map(
			(i) =>
				pts.reduce((sum, p) => sum + p.counts[i], 0) / Math.max(TOTALS[i], 1)
		);
		const sum = rates.reduce((a, b) => a + b, 0) || 1;
		const person = FACES.get(nameKey(group.join(" ")));
		return {
			key: group.join(","),
			label: person ? person.name : group.join(", "),
			// narrow screens show the shorter name
			short: person ? initialName(person.name) : group.join(", "),
			face: person?.face ?? null,
			shares: rates.map((r) => r / sum),
			// hovering the row pins the group's most-used word on the triangle
			lead: pts.toSorted((a, b) => b.total - a.total)[0].term
		};
	};
	const pctOf = (v) => (v > 0 && v < 0.005 ? "<1%" : `${Math.round(v * 100)}%`);
	const SHARE_COLORS = [
		"var(--wnba-red)",
		"var(--wnba-purple)",
		"var(--wnba-navy)"
	];

	let terIndex = $state(0);
	let terLast = $state(0);
	$effect(() => {
		if (terIndex !== undefined && terIndex !== null) terLast = terIndex;
	});

	// --- the handoff ----------------------------------------------------------
	// t runs 0 → 1 as the bridge (an empty stretch between the two sets of
	// cards) crosses the middle of the screen; it drives everything in between
	let bridgeEl = $state(null);
	let t = $state(0);
	const clamp = (v) => Math.max(0, Math.min(1, v));
	let phase = $derived(t <= 0 ? "gap" : t >= 1 ? "ternary" : "bridge");

	// the dot plot holds its last step through the handoff and after
	let gapStep = $derived(
		phase === "gap" ? (GAP[gapLast] ?? GAP[0]) : GAP.at(-1)
	);
	let terStep = $derived(
		phase === "ternary" ? (TER[terLast] ?? TER[0] ?? null) : null
	);

	// each player's surname on the triangle (A'ja Wilson is "wilson"; a name
	// the chyrons never ran falls back to the first name, else nothing)
	const slugOf = (name) =>
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");
	const ternary = new Map((chy.ternary ?? []).map((row) => [row.term, row]));
	const termFor = (name) => {
		const parts = name.toLowerCase().replace(/[’‘]/g, "'").split(/\s+/);
		return [parts.at(-1), parts[0]].find((w) => ternary.has(w)) ?? null;
	};
	const TERM_OF = new Map(
		(gapData.people ?? [])
			.filter((p) => p.name)
			.map((p) => [slugOf(p.name), termFor(p.name)])
	);

	// where a word sits on the triangle, in its own drawing units: the same
	// geometry as TernaryStatic (keep the two in step)
	const SIDE = 700,
		PAD = 58,
		HEIGHT = SIDE * 0.92;
	const corners = (() => {
		const width = SIDE - PAD * 2;
		const tall = (width * Math.sqrt(3)) / 2;
		const top = (HEIGHT - tall) / 2 + 6;
		return {
			A: [SIDE / 2, top],
			B: [PAD, top + tall],
			C: [SIDE - PAD, top + tall]
		};
	})();
	const totals = (chy.ternary ?? [])
		.map((row) => row.total)
		.filter((n) => n >= 1);
	const BIGGEST = Math.max(1, ...totals);
	const SMALLEST = Math.max(1, Math.min(...totals));
	// the "big" radius, with no slider floor
	const dotRadius = (total) => {
		const span = Math.log(Math.max(2, BIGGEST / SMALLEST));
		return 2 + (Math.log(Math.max(1, total / SMALLEST)) / span) * 10;
	};
	const HIGHLIGHT = "var(--color-fox-navy)";
	// the band a word sits in, as TernaryStatic colours its dots (keep in step):
	// the network with more than half its uses, else the middle's tan
	const NETWORK_COLORS = {
		"Fox News": "var(--wnba-red)",
		CNN: "var(--wnba-purple)",
		MSNBC: "var(--wnba-navy)"
	};
	const regionColor = (shares) => {
		const top = Math.max(...shares);
		return top > 0.5
			? NETWORK_COLORS[(chy.channels ?? [])[shares.indexOf(top)]]
			: "var(--wnba-tan-dark)";
	};
	function spot(term) {
		const row = ternary.get(term);
		if (!row) return null;
		const [a, b, c] = row.shares;
		return {
			px: a * corners.A[0] + b * corners.B[0] + c * corners.C[0],
			py: a * corners.A[1] + b * corners.B[1] + c * corners.C[1],
			r: dotRadius(row.total),
			// lit as the triangle lights it: its band's network colour
			color: regionColor(row.shares)
		};
	}

	// the faces in flight: where each starts (its face on the dot plot) and
	// lands (its dot on the triangle), in pixels within the sticky frame,
	// measured afresh each frame of the handoff
	let stageEl = $state(null);
	let gapEl = $state(null);
	let terEl = $state(null);
	let flyers = $state([]);
	// the players' words, lit on the triangle while they land
	let bridgeWords = $state([]);
	function measure() {
		if (!stageEl || !gapEl || !terEl) return;
		const svg = terEl.querySelector("svg");
		const ctm = svg?.getScreenCTM();
		if (!ctm) return;
		const box = stageEl.getBoundingClientRect();
		const out = [];
		for (const mark of gapEl.querySelectorAll(".face-mark")) {
			const slug = mark.querySelector("clipPath")?.id.replace(/^gap-clip-/, "");
			const ring = mark.querySelector(".ring");
			if (!slug || !ring) continue;
			const rr = ring.getBoundingClientRect();
			const term = TERM_OF.get(slug);
			const at = term ? spot(term) : null;
			let end = null;
			if (at) {
				const p = new DOMPoint(at.px, at.py).matrixTransform(ctm);
				end = {
					x: p.x - box.left,
					y: p.y - box.top,
					r: at.r * ctm.a,
					color: at.color
				};
			}
			out.push({
				slug,
				term,
				img: mark.querySelector("image")?.getAttribute("href") ?? null,
				ring: getComputedStyle(ring).stroke,
				start: {
					x: rr.left + rr.width / 2 - box.left,
					y: rr.top + rr.height / 2 - box.top,
					r: rr.width / 2
				},
				end
			});
		}
		// the top row leaves first
		out.sort((a, b) => a.start.y - b.start.y);
		flyers = out;
		const words = out.filter((f) => f.end).map((f) => f.term);
		if (words.join() !== bridgeWords.join()) bridgeWords = words;
	}

	$effect(() => {
		if (!bridgeEl) return;
		let frame = null;
		const update = () => {
			frame = null;
			const r = bridgeEl.getBoundingClientRect();
			const mid = window.innerHeight / 2;
			t = clamp((mid - r.top) / Math.max(1, r.height));
			// (and once past it, if a fast scroll skipped it, so the names are known)
			// and while the heads sit on the triangle, so they follow a resize
			if ((t > 0 && t < 1) || (t >= 1 && (!bridgeWords.length || headsOn)))
				measure();
		};
		const queue = () => {
			if (frame === null) frame = requestAnimationFrame(update);
		};
		update();
		window.addEventListener("scroll", queue, { passive: true });
		window.addEventListener("resize", queue);
		return () => {
			window.removeEventListener("scroll", queue);
			window.removeEventListener("resize", queue);
			if (frame !== null) cancelAnimationFrame(frame);
		};
	});

	// the handoff's timing, as shares of the bridge: the faces fly between
	// FLY_FROM and FLY_TO, each leaving up to STAGGER after the first
	const FLY_FROM = 0.05,
		FLY_TO = 0.85,
		STAGGER = 0.25,
		ARC = 50, // px the path bows upward at its middle
		HEAD_MIN = 10; // px: the smallest a head lands, so the face still reads
	let gapOpacity = $derived(1 - clamp((t - 0.05) / 0.35));
	let terOpacity = $derived(clamp((t - 0.4) / 0.45));
	const lerp = (a, b, p) => a + (b - a) * p;
	function flight(f, i, n) {
		const delay = n > 1 ? (STAGGER * i) / (n - 1) : 0;
		const p = cubicInOut(
			clamp((t - FLY_FROM - delay) / (FLY_TO - FLY_FROM - STAGGER))
		);
		// a face with no word on the triangle fades where it is
		const end = f.end ?? f.start;
		const r = lerp(f.start.r, f.end ? Math.max(end.r, HEAD_MIN) : f.start.r, p);
		return {
			x: lerp(f.start.x, end.x, p),
			y: lerp(f.start.y, end.y, p) - (f.end ? Math.sin(Math.PI * p) * ARC : 0),
			r,
			// the photo stays; its ring takes on the dot's colour as it lands
			ring: f.end
				? `color-mix(in srgb, ${f.end.color} ${Math.round(clamp((p - 0.3) / 0.5) * 100)}%, ${f.ring})`
				: f.ring,
			opacity: f.end ? 1 : 1 - p
		};
	}

	// --- the triangle's explore step (as on TernaryScrolly) -------------------
	const MIN_TOTAL = 1;
	const vocabulary = (chy.ternary ?? [])
		.filter((row) => row.total >= MIN_TOTAL)
		.map((row) => ({ term: row.term, total: row.total }))
		.sort((a, b) => b.total - a.total);
	const MAX_LIT = 30;
	let query = $state("");
	let q = $derived(query.trim().toLowerCase());
	let exact = $derived(
		q ? (vocabulary.find((w) => w.term === q) ?? null) : null
	);
	let partial = $derived(
		q && !exact ? vocabulary.filter((w) => w.term.includes(q)) : []
	);
	let suggestions = $derived.by(() => {
		if (!q) return [];
		const starts = vocabulary.filter((w) => w.term.startsWith(q));
		const inside = vocabulary.filter(
			(w) => !w.term.startsWith(q) && w.term.includes(q)
		);
		return [...starts, ...inside].slice(0, 8);
	});
	let open = $state(false);
	let cursor = $state(-1);
	let picked = $state([]);
	let lastKept = $state(null);
	// on a touch screen, once a word is picked the keyboard closes so the triangle
	// shows again (on desktop the box keeps focus, for the next word)
	let inputEl = $state(null);
	const doneTyping = () => {
		if (window.matchMedia("(pointer: coarse)").matches) inputEl?.blur();
	};
	const choose = (word) => {
		if (!picked.includes(word)) picked = [...picked, word];
		lastKept = word;
		query = "";
		cursor = -1;
	};
	const keep = () => {
		if (!exact) return;
		if (!picked.includes(exact.term)) picked = [...picked, exact.term];
		lastKept = exact.term;
		query = "";
	};
	function onKey(e) {
		if (e.key === "ArrowDown") {
			cursor = Math.min(cursor + 1, suggestions.length - 1);
			e.preventDefault();
		} else if (e.key === "ArrowUp") {
			cursor = Math.max(cursor - 1, -1);
			e.preventDefault();
		} else if (e.key === "Enter") {
			if (cursor >= 0 && suggestions[cursor]) choose(suggestions[cursor].term);
			else keep();
			doneTyping();
		} else if (e.key === "Escape") {
			open = false;
		}
	}
	const drop = (word) => {
		picked = picked.filter((w) => w !== word);
		lastKept = null;
		focus = null;
	};
	let focus = $state(null);
	function unpin(event) {
		if (event.target.closest?.(".chip, .ter-tools")) return;
		focus = null;
		lastKept = null;
	}
	// the reader's own words, typed or kept, take over from the step's
	let search = $derived(
		Boolean(terStep) && (terStep.search || Boolean(q) || picked.length > 0)
	);
	let pinned = $derived(focus ?? (search ? (exact?.term ?? lastKept) : null));
	let groups = $derived(
		!terStep
			? bridgeWords.length
				? [bridgeWords]
				: []
			: search
				? [
						[
							...picked,
							...(exact
								? [exact.term]
								: partial.slice(0, MAX_LIT).map((w) => w.term))
						]
					]
				: holdNames
					? [bridgeWords]
					: terStep.groups
	);
	// the first triangle step keeps the players' names lit, as they landed,
	// unless it names words of its own
	let holdNames = $derived(
		terLast === 0 && !terStep?.groups.length && bridgeWords.length > 0
	);
	// the heads stay on their words through the handoff and for as long as
	// the names are held lit, then fade
	let headsOn = $derived(
		phase === "bridge" || (phase === "ternary" && holdNames)
	);
</script>

<svelte:window onclick={unpin} />

<!-- under the triangle on every step: find a word -->
{#snippet tools()}
	<div class="ter-tools">
		<label class="control">
			<div class="search-box">
				<input
					type="search"
					bind:this={inputEl}
					enterkeyhint="search"
					placeholder="Find a word…"
					bind:value={query}
					autocomplete="off"
					spellcheck="false"
					onfocus={() => (open = true)}
					onblur={() => (open = false)}
					oninput={() => ((open = true), (cursor = -1))}
					onkeydown={onKey}
				/>
				{#if open && q && suggestions.length}
					<ul class="suggest" role="listbox">
						{#each suggestions as w, i (w.term)}
							<li
								role="option"
								aria-selected={i === cursor}
								class:on={i === cursor}
								onpointerdown={(e) => (
									e.preventDefault(),
									choose(w.term),
									doneTyping()
								)}
							>
								<span class="term">{w.term}</span>
								<span class="uses">{w.total.toLocaleString()}</span>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</label>
		<!-- the note and the kept words hang under the box, out of the layout, so
		     the triangle above doesn't shift as they come and go -->
		<div class="find-below">
			{#if q && !exact}
				<span class="control-note">
					{#if !partial.length}
						No word contains “{q}”.
					{:else if partial.length > MAX_LIT}
						{partial.length} words contain “{q}”; the {MAX_LIT} most common
						are lit.
					{:else}
						{partial.length}
						{partial.length === 1 ? "word contains" : "words contain"} “{q}”.
					{/if}
				</span>
			{:else if exact}
				<span class="control-note"
					>Press Enter to keep “{exact.term}”.</span
				>
			{/if}
			{#if picked.length}
				<div class="chips">
					{#each picked as word (word)}
						<span
							class="chip"
							class:on={pinned === word}
							role="button"
							tabindex="0"
							onpointerenter={() => (focus = word)}
							onpointerleave={() => (focus = null)}
						>
							{word}
							<button
								class="x"
								aria-label="remove {word}"
								onclick={() => drop(word)}>×</button
							>
						</span>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/snippet}

<section
	class="gap-ternary"
	class:handing={phase !== "gap"}
>
	<div class="sticky" bind:this={stageEl}>
		<div
			class="stage gap"
			bind:this={gapEl}
			style:opacity={gapOpacity}
			style:visibility={gapOpacity > 0 ? null : "hidden"}
			inert={phase !== "gap"}
		>
			<OutletGapDotPlot
				highlight={gapStep?.explore ? null : gapStep?.names}
				bare={!gapStep?.explore}
				placed={gapStep?.placed ?? null}
				centered={gapStep?.center}
				{speed}
				centerLine
				wide
				{heading}
				{comparedWith}
				{allOutlets}
			/>
		</div>

		<div
			class="stage ternary"
			class:centred={terStep?.search}
			bind:this={terEl}
			style:opacity={terOpacity}
			inert={phase !== "ternary"}
		>
			<div class="ter-col">
				<TernaryStatic
					heading={or(heading, HEADING)}
					{groups}
					{note}
					bare
					big
					highlightColor={HIGHLIGHT}
					enclose={Boolean(terStep) && !search && !holdNames}
					focus={pinned}
					quiet={open && suggestions.length > 0}
					topic={terStep?.topic ?? null}
					bands={phase === "ternary" && (terStep?.bands ?? flag(bands) ?? true)}
				/>
				{@render tools()}
			</div>
		</div>

		<!-- the faces in flight, from their rows to their words -->
		{#if phase !== "gap"}
			<div class="flyers" aria-hidden="true" style:opacity={headsOn ? 1 : 0}>
				{#each flyers as f, i (f.slug)}
					{@const at = flight(f, i, flyers.length)}
					<div
						class="flyer"
						style:width="{at.r * 2}px"
						style:height="{at.r * 2}px"
						style:transform="translate({at.x - at.r}px, {at.y - at.r}px)"
						style:opacity={at.opacity}
					>
						{#if f.img}<img src={f.img} alt="" />{/if}
						<span class="ring" style:border-color={at.ring}></span>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<div class="steps">
		<Scrolly bind:value={gapIndex}>
			{#each GAP as step, i}
				<div class="gap-step" class:active={phase === "gap" && gapIndex === i}>
					{#if step.html.trim()}
						<div class="stack">
							<p class="gap-card">
								{@html clipPops(faces(step.html, base), base)}
							</p>
						</div>
					{/if}
				</div>
			{/each}
		</Scrolly>

		<!-- scrolling through it carries the faces to the triangle -->
		<div class="bridge" bind:this={bridgeEl}>
			{#if bridge?.trim()}
				<div class="card bridge-card" class:active={phase === "bridge"}>
					<p class="card-text">{@html clipPops(faces(bridge, base), base)}</p>
				</div>
			{/if}
		</div>

		<Scrolly bind:value={terIndex}>
			{#each TER as step, i}
				<div
					class="ter-step"
					class:search-step={step.search}
					class:active={phase === "ternary" && terLast === i}
				>
					{#if step.search}
						<!-- a pause with no card: the find box is under the triangle -->
					{:else}
						<div class="card">
							{#if step.title}<h4 class="card-title">{step.title}</h4>{/if}
							{#if step.html}<p class="card-text">
									{@html clipPops(faces(step.html, base), base)}
								</p>{/if}
							<!-- one stacked bar per word group: Fox | CNN | MSNBC, then Fox's share -->
							{#if step.rows.length}
								<div class="shares">
									<span></span>
									<span class="legend">
										<i style:color={SHARE_COLORS[0]}>Fox</i>
										<i style:color={SHARE_COLORS[1]}>CNN</i>
										<i style:color={SHARE_COLORS[2]}>MSNBC</i>
									</span>
									<!-- over the rows' numbers: they're Fox's share -->
									<span class="head-pct" style:color={SHARE_COLORS[0]}>Fox%</span>
									{#each step.rows as row (row.key)}
										<button
											class="srow"
											class:on={focus === row.lead}
											onpointerenter={() => (focus = row.lead)}
											onpointerleave={() => (focus = null)}
											onclick={() =>
												(focus = focus === row.lead ? null : row.lead)}
										>
											<span class="who">
												{#if row.face}<img src={row.face} alt="" />{/if}
												<span class="full">{row.label}</span>
												<span class="short">{row.short}</span>
											</span>
											<span class="sbar">
												{#each row.shares as v, i}
													<span
														style:width="{(v * 100).toFixed(2)}%"
														style:background={SHARE_COLORS[i]}
													></span>
												{/each}
											</span>
											<!-- Fox's share, in Fox's colour whichever way the row leans -->
											<span class="pct" style:color={SHARE_COLORS[0]}
												>{pctOf(row.shares[0])}</span
											>
										</button>
									{/each}
								</div>
							{/if}
							{#if step.img}
								<img
									class="figure"
									src="{base}/images/{step.img}"
									alt=""
									loading="lazy"
								/>
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		</Scrolly>
		<div class="linger"></div>
	</div>
</section>

<style>
	.gap-ternary {
		position: relative;
		margin: 3rem 0;
		/* the triangle's cards at the left: their width and padding, and a gap */
		--cards: calc(460px + 4rem);
	}

	.sticky {
		position: sticky;
		top: 0;
		height: 100vh;
	}
	/* the two charts share the frame, one over the other */
	.stage {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* the triangle sits as near the middle as the cards beside it allow (in the
	   middle on wide screens, nudged right on narrower ones); on the cardless last
	   step it slides to the middle to be explored */
	.stage.ternary {
		justify-content: center;
	}
	.ter-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		transform: translateX(max(0px, calc(var(--cards) - 50vw + 50%)));
		transition: transform 700ms ease;
	}
	.stage.ternary.centred .ter-col {
		transform: none;
	}

	/* the dot plot, framed as on OutletGapScrolly */
	.gap :global(.outlet-gap) {
		width: min(1040px, 97vw);
		height: 96vh;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
	.gap :global(.outlet-gap > .plot) {
		flex: 0 1 auto;
		min-height: 0;
	}
	.gap :global(.outlet-gap > .plot > svg) {
		width: 100%;
		height: auto;
		display: block;
	}
	/* once the handoff starts the faces in flight stand in for the faces */
	.handing .gap :global(.face-mark) {
		opacity: 0;
	}
	/* and the named faces settle back to size, so every head leaves the same */
	.handing .gap :global(.face-scale) {
		transform: scale(1) !important;
	}

	/* the triangle, framed as on TernaryScrolly, with the find box under it */
	.ternary :global(svg) {
		max-height: 74vh;
	}
	.ter-tools {
		position: relative;
		display: flex;
		flex-wrap: wrap;
		align-items: flex-start;
		justify-content: center;
		gap: 6px 28px;
		width: 100%;
		max-width: 560px;
		margin-top: 10px;
	}
	.ter-tools .control {
		flex: 1 1 200px;
		max-width: 260px;
	}
	/* near the bottom of the screen, the suggestions open upward, over the
	   triangle and its word card */
	.ter-tools .suggest {
		top: auto;
		bottom: calc(100% + 4px);
		z-index: 6;
	}
	.find-below {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		text-align: center;
	}
	.find-below .chips {
		justify-content: center;
	}

	.flyers {
		position: absolute;
		inset: 0;
		pointer-events: none;
		z-index: 3;
		transition: opacity 300ms ease;
	}
	.flyer {
		position: absolute;
		left: 0;
		top: 0;
		border-radius: 50%;
		overflow: hidden;
		background: var(--wnba-tan-light);
		will-change: transform;
	}
	/* the photo framed as the dot plot frames it: a little large, a little low */
	.flyer img {
		position: absolute;
		width: 120%;
		height: 120%;
		left: -10%;
		top: -2.5%;
		max-width: none;
		object-fit: cover;
	}
	.flyer .ring {
		position: absolute;
		inset: 0;
		border-radius: 50%;
		border: 3px solid;
		box-sizing: border-box;
	}

	.steps {
		position: relative;
		z-index: 4;
		margin-top: -100vh;
		pointer-events: none;
	}
	.bridge {
		max-width: 460px;
		padding: 0 2rem;
		height: 160vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
	}
	/* at the left, as the triangle's cards sit, clear of the faces in flight */
	.bridge-card.active {
		opacity: 1;
		pointer-events: auto;
	}
	.linger {
		height: 20vh;
	}

	/* the dot plot's cards: centred over the plot */
	.gap-step {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.stack {
		max-width: 460px;
		opacity: 0.3;
		pointer-events: auto;
		margin: 0 auto;
		transition: opacity 250ms ease;
	}
	.gap-step.active .stack {
		opacity: 1;
	}
	.gap-card {
		max-width: 460px;
		font-size: 18px;
		margin: 0;
		background: var(--wnba-tan-bg);
		padding: 14px 18px;
		border-radius: 4px;
		font-size: var(--step-text);
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
	}
	@media(max-width: 640px) {
		font-size: 16px;
	}

	/* the triangle's cards: at the left */
	.ter-step {
		max-width: 460px;
		padding: 0 2rem;
		position: relative;
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
		pointer-events: none;
	}
	.card {
		max-width: 460px;
		margin: 0;
		background: var(--wnba-tan-bg);
		padding: 14px 16px 15px;
		border-radius: 3px;
		font-size: var(--step-text);
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.ter-step.active .card {
		opacity: 1;
		pointer-events: auto;
	}
	.figure {
		width: 100%;
		object-fit: contain;
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.2);
		border-radius: 4px;
		box-shadow: 0 8px 30px rgba(42, 21, 3, 0.22);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.ter-step.active .figure {
		opacity: 1;
	}
	.card-title {
		margin: 0 0 6px;
		font-size: 19px;
		line-height: 1.2;
	}
	.card-text {
		font-size: 18px;
		margin: 0;
	}
	@media(max-width: 640px) {
		.card-text {
			font-size: 16px;
		}
	}

	/* it's the last thing the reader meets, so it stays above the triangle */
	.ter-step.search-step {
		z-index: 5;
	}

	/* the share bars: one grid, so every row's bar starts at the same place */
	.shares {
		display: grid;
		grid-template-columns: minmax(0, max-content) minmax(70px, 1fr) auto;
		column-gap: 8px;
		align-items: center;
		margin-top: 12px;
		font-family: var(--font-chart);
		font-size: 13px;
	}
	.shares > span {
		font-size: 11.5px;
		font-weight: 700;
		color: rgba(42, 21, 3, 0.6);
		margin-bottom: 2px;
	}
	.shares .legend {
		display: flex;
		gap: 7px;
		white-space: nowrap;
	}
	.shares .legend i {
		font-style: normal;
	}
	.shares .head-pct {
		text-align: right;
	}
	/* a row is a button spanning the three columns */
	.srow {
		grid-column: 1 / -1;
		display: grid;
		grid-template-columns: subgrid;
		align-items: center;
		height: 28px;
		padding: 0;
		border: 0;
		border-radius: 3px;
		background: none;
		font: inherit;
		color: var(--color-ink);
		text-align: left;
		cursor: pointer;
	}
	.srow:hover,
	.srow.on {
		background: rgba(42, 21, 3, 0.06);
	}
	.srow .who {
		display: flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.srow .who span {
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.srow .who .short {
		display: none;
	}
	.srow .who img {
		flex: 0 0 auto;
		width: 22px;
		height: 22px;
		border-radius: 50%;
		object-fit: cover;
		object-position: 50% 20%;
		background: var(--color-card);
	}
	.sbar {
		display: flex;
		height: 10px;
		border-radius: 2px;
		overflow: hidden;
		background: var(--color-sand);
	}
	.sbar span {
		display: block;
		height: 100%;
	}
	.sbar span + span {
		box-shadow: inset 1px 0 0 #fff;
	}
	.srow .pct {
		text-align: right;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 10px;
	}
	.chip {
		font-family: var(--font-chart);
		font-size: 11.5px;
		font-weight: 800;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--color-ink);
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.18);
		border-radius: 3px;
		padding: 4px 8px;
		cursor: pointer;
		box-shadow: 0 1px 3px rgba(42, 21, 3, 0.14);
		transition:
			transform 120ms ease,
			background 120ms ease;
	}
	.chip .x {
		font: inherit;
		font-size: 12px;
		line-height: 1;
		border: 0;
		background: none;
		color: inherit;
		opacity: 0.55;
		margin-left: 5px;
		padding: 0;
		cursor: pointer;
	}
	.chip .x:hover {
		opacity: 1;
	}
	.chip:hover,
	.chip.on {
		background: var(--color-fox);
		color: #fff;
		border-color: var(--color-fox);
		transform: translateY(-1px);
	}

	.control {
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 14px;
	}
	.control-note {
		display: block;
		font-size: 12px;
		line-height: 1.4;
		color: rgba(42, 21, 3, 0.65);
		margin-top: 4px;
	}
	.control input[type="search"] {
		width: 200px;
		height: 30px;
		padding: 0 10px 0 28px;
		border: 1px solid var(--wnba-tan-light);
		border-radius: 4px;
		background: var(--color-white)
			url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23727272' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-4-4'/%3E%3C/svg%3E")
			no-repeat 10px 50%;
		font-family: var(--font-sans);
		font-size: 14px;
		color: var(--color-ink-dark);
	}
	.control input[type="search"]:focus {
		outline: 2px solid var(--color-ink-dark);
		outline-offset: -2px;
	}
	.search-box {
		position: relative;
	}
	.suggest {
		position: absolute;
		left: 0;
		right: 0;
		top: calc(100% + 4px);
		margin: 0;
		padding: 0;
		list-style: none;
		background: #fff;
		border: 1px solid rgba(42, 21, 3, 0.2);
		border-radius: 3px;
		box-shadow: 0 6px 18px rgba(42, 21, 3, 0.18);
		z-index: 4;
		overflow: hidden;
	}
	.suggest li {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		padding: 7px 10px;
		font-size: 14px;
		cursor: pointer;
	}
	.suggest li + li {
		border-top: 1px solid rgba(42, 21, 3, 0.08);
	}
	.suggest li:hover,
	.suggest li.on {
		background: rgba(42, 21, 3, 0.07);
	}
	.suggest .term {
		font-weight: 700;
	}
	.suggest .uses {
		font-family: var(--font-chart);
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
	}

	@media (max-width: 860px) {
		.linger {
			height: 70vh;
		}
		/* the dot plot's cards keep 2rem clear of the edges, as the triangle's do */
		.gap-step {
			padding: 0 2rem;
		}
		/* the triangle and its find box centred, inside the page's gutters */
		.stage.ternary {
			padding: 0 16px;
		}
		.ter-col {
			transform: none;
		}
		.ter-tools {
			gap: 6px 16px;
		}
		.ter-tools .control {
			flex: 1 1 140px;
		}
		/* the share rows' players as "A. Wilson" */
		.srow .who .full {
			display: none;
		}
		.srow .who .short {
			display: inline;
		}
		/* the bridge card and the triangle's cards centred, with the triangle */
		.bridge,
		.ter-step {
			margin-inline: auto;
		}
		.bridge {
			justify-content: center;
		}
		.ter-step {
			flex-direction: column;
			justify-content: center;
			gap: 12px;
		}
		.figure {
			position: static;
			transform: none;
			width: 84vw;
			max-height: 40vh;
		}
		.suggest {
			position: static;
			margin-top: 4px;
			box-shadow: none;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.flyers {
			display: none;
		}
		.ter-col {
			transition: none;
		}
	}
	.steps :global(a) {
		pointer-events: auto;
	}
</style>
