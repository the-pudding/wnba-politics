<script>
	// Foul or passage reel/gallery
	import { base } from "$app/paths";
	import roster from "$data/people.json";
	import { faces } from "$utils/clips.js";
	import { tick } from "svelte";

	// mark: "bold" (default), "underline" or "highlight" 
	let { player = "Caitlin Clark", outlet = "fox", word = "", picks = "", layout = "", slides = [], mark = "bold", height = 560 } = $props();
	let underline = $derived(String(mark).trim().toLowerCase() === "underline");
	let highlight = $derived(String(mark).trim().toLowerCase() === "highlight");

	const TERM = /hip[- ]?check(?:ed|s|ing)?|\bpunch(?:ed|es|ing)?\b|\bthroat\b|\bpoke[ds]?\b|\bpoking\b|\bflagrant(?:ly)?\b|\bfoul(?:s|ed|ing)?\b|\bshove[sd]?\b|\bshoving\b|\belbow(?:s|ed|ing)?\b|\bclothesline[sd]?\b|\bcheap shot\b|\bhard hit\b|\btackle[sd]?\b|\bslap(?:ped|s)?\b|\bbloodied\b|\bblack eye\b|\bejected\b|\bejection\b|\btechnical\b|\bhit\b/i;
	const NAMES = Object.entries(roster)
		.filter(([, p]) => p.group === "players" && p.rx)
		.map(([name, p]) => [name, new RegExp(p.rx, "i")]);
	// a link only counts when it is one: a placeholder like "https://…"
	// left in the Doc would otherwise break the site build's link crawl
	const realUrl = (link) => {
		const u = String(link ?? "").trim();
		try {
			const parsed = new URL(u);
			return /^https?:$/.test(parsed.protocol) && /^[\w.-]+\.[a-z]{2,}$/i.test(parsed.hostname) ? u : "";
		} catch {
			return "";
		}
	};
	// the first match of a pattern that sits in the text, not inside a tag
	// (an inline face carries the name in its alt attribute)
	function findOutsideTags(rx, s) {
		const g = new RegExp(rx.source, rx.flags.includes("g") ? rx.flags : rx.flags + "g");
		let m;
		while ((m = g.exec(s))) {
			const before = s.slice(0, m.index);
			const open = before.lastIndexOf("<"), close = before.lastIndexOf(">");
			if (open <= close) return m;
		}
		return null;
	}
	function rowFromText(text, o, link, dateText) {

		const s = faces(String(text ?? "").trim().replace(/==([^=]+)==/g, "<mark>$1</mark>"), base);
		if (!s) return null;
		const m = findOutsideTags(TERM, s);
		let n = null;
		for (const [, rx] of NAMES) {
			const h = findOutsideTags(rx, s);
			if (h && (!m || h.index + h[0].length <= m.index || h.index >= m.index + m[0].length)) {
				n = [h.index, h.index + h[0].length];
				break;
			}
		}
		return { o, d: "", dateText: String(dateText ?? "").trim(), u: realUrl(link), s, t: m ? [m.index, m.index + m[0].length] : [0, 0], n, h: false, p: "", html: true };
	}
	let ownSlides = $derived(
		(Array.isArray(slides) ? slides : [])
			.map((sl) => ({
				d: "",
				oth: rowFromText(sl.outletText, sl.outlet || "the other outlets", sl.outletLink, sl.outletDate),
				fox: rowFromText(sl.foxText, sl.fox || "Fox News", sl.foxLink, sl.foxDate)
			}))
			.filter((sl) => sl.oth || sl.fox)
	);
	let gallery = $derived(String(layout).trim().toLowerCase() === "gallery");
	let paired = $derived(gallery || String(layout).trim().toLowerCase() === "pairs");

	// --- the gallery: one slide per incident, scroll-snapped ----------------
	let galleryEl = $state(null);
	let slide = $state(0);
	function onGalleryScroll() {
		if (!galleryEl) return;
		const w = galleryEl.clientWidth || 1;
		slide = Math.round(galleryEl.scrollLeft / w);
	}
	function goSlide(i) {
		if (!galleryEl) return;
		const n = pairs.length;
		const to = Math.max(0, Math.min(n - 1, i));
		galleryEl.scrollTo({ left: to * galleryEl.clientWidth, behavior: "smooth" });
		slide = to;
	}
	const mast = (o) => (o === "Fox News" ? "Fox News" : o);
	// the outlet's logo for the clipping's masthead, when the site has one
	import { LOGO } from "$utils/outlets.js";
	const LOGOS = { ...LOGO, MSNBC: "ms-now.svg", "MS NOW": "ms-now.svg" };
	// a hand-written slide may carry its own <b>, <i> or <a>
	const esc = (t) => t;
	function markup(r, color) {
		const hl = (t) => t;
		return pieces(r)
			.map((piece) =>
				piece.kind === "term"
					? `<b class="term" style="color:${color}">${piece.text}</b>`
					: piece.kind === "name"
						? `<b class="name">${piece.text}</b>`
						: hl(esc(piece.text))
			)
			.join("");
	}
	// word: a filter on the sentences ("dirty"), matched as a whole word with
	// its inflections
	let wordRx = $derived(
		String(word).trim() ? new RegExp("\\b" + String(word).trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\w*", "i") : null
	);
	let pickList = $derived(
		String(picks)
			.split("|")
			.map((t) => t.trim().toLowerCase())
			.filter(Boolean)
	);
	const ALL = "all";

	let data = $state(null);
	let loading = false;
	async function load() {
		if (data || loading) return;
		loading = true;
		try {
			data = await (await fetch(`${base}/data/foul_feed.json`)).json();
		} finally {
			loading = false;
		}
	}
	$effect(() => {
		load();
	});

	const FOX = "var(--color-fox-navy)";
	const OTHER = "var(--color-outlets)";
	const OUTLETS = [
		["fox", "Fox News"],
		["outlets", "the other outlets"],
		["all", "everyone"]
	];
	let who = $state(String(player).trim() || ALL);
	let side = $state(String(outlet).trim().toLowerCase());
	$effect(() => {
		who = String(player).trim() || (wordRx || pickList.length ? ALL : "Caitlin Clark");
		side = String(outlet).trim().toLowerCase();
	});

	// the players on offer: those the feed carries, most sentences first
	let players = $derived(Object.keys(data?.players ?? {}));
	const face = (name) => (roster[name]?.face ? `${base}/net/${roster[name].face}` : null);
	const surname = (name) => name.split(" ").slice(-1)[0];

	let rows = $derived.by(() => {
		const all = data?.rows ?? [];
		if (pickList.length) {
			// one row per pick, the first sentence carrying the snippet
			const seen = new Set();
			const out = [];
			for (const snip of pickList) {
				const hit = all.find((r) => r.s.toLowerCase().includes(snip) && !seen.has(r.o + r.s));
				if (hit) {
					seen.add(hit.o + hit.s);
					out.push(hit);
				}
			}
			return out;
		}
		const seen = new Set();
		return all.filter((r) => {
			if (who !== ALL && r.p !== who) return false;
			if (side !== "all" && (side === "fox") !== (r.o === "Fox News")) return false;
			if (wordRx && !wordRx.test(r.s)) return false;
			// with every player in, a sentence naming two of them appears once
			const key = r.o + r.d + r.s;
			if (who === ALL && seen.has(key)) return false;
			seen.add(key);
			return true;
		});
	});
	let foxCount = $derived(rows.filter((r) => r.o === "Fox News").length);

	// --- pairs: the same incident from both sides -------------------------
	// A Fox sentence and an outlet sentence are the same incident when they
	// are about the same player, fall within a few days of each other, and
	// share the foul word (or name the same other person). Each outlet
	// sentence pairs at most once; the rest stand alone on their side.
	const DAY = 86400000;
	const stem = (r) => r.s.slice(r.t[0], r.t[1]).toLowerCase().replace(/(ed|ing|es|s)$/, "");
	const otherNames = (r) => {
		const found = new Set();
		for (const name of players) if (name !== r.p && new RegExp("\\b" + name.split(" ").slice(-1)[0] + "\\b", "i").test(r.s)) found.add(name);
		return found;
	};
	// the partner for one sentence: the closest telling from the other side
	function partnerOf(r, others) {
		const rd = Date.parse(r.d), rs = stem(r), rn = otherNames(r);
		let best = null, score = -1;
		for (const o of others) {
			if (o.p !== r.p) continue;
			const gap = Math.abs(Date.parse(o.d) - rd) / DAY;
			if (gap > 4) continue;
			let sc = 0;
			if (stem(o) === rs) sc += 2;
			for (const n of otherNames(o)) if (rn.has(n)) sc += 1;
			if (sc === 0) continue;
			sc += 1 - gap / 5;
			if (sc > score) (score = sc), (best = o);
		}
		return best;
	}
	let pairs = $derived.by(() => {
		if (!paired) return [];
		if (ownSlides.length) return ownSlides;
		const base = data?.rows ?? [];
		if (pickList.length) {
			// hand-picked: "fox snippet :: outlet snippet", or one snippet whose
			// partner is found for it
			const find = (snip, side) =>
				base.find((r) => r.s.toLowerCase().includes(snip) && (side === "any" || (side === "fox") === (r.o === "Fox News")));
			const out = [];
			for (const entry of pickList) {
				const [a, b] = entry.split("::").map((t) => t.trim());
				if (b !== undefined) {
					const f = a ? find(a, "fox") : null, o = b ? find(b, "oth") : null;
					if (f || o) out.push({ d: (f ?? o).d, fox: f, oth: o });
					continue;
				}
				const hit = find(a, "any");
				if (!hit) continue;
				const fox = hit.o === "Fox News";
				const partner = partnerOf(hit, base.filter((r) => (r.o === "Fox News") !== fox));
				out.push({ d: hit.d, fox: fox ? hit : partner, oth: fox ? partner : hit });
			}
			return out;
		}
		const mine = base.filter((r) => (who === ALL || r.p === who) && (!wordRx || wordRx.test(r.s)));
		const fox = mine.filter((r) => r.o === "Fox News");
		const oth = mine.filter((r) => r.o !== "Fox News");
		const used = new Set();
		const out = [];
		for (const f of fox) {
			const fd = Date.parse(f.d), fs = stem(f), fn = otherNames(f);
			let best = null, score = -1;
			for (let i = 0; i < oth.length; i++) {
				if (used.has(i)) continue;
				const o = oth[i];
				if (o.p !== f.p) continue;
				const gap = Math.abs(Date.parse(o.d) - fd) / DAY;
				if (gap > 4) continue;
				let sc = 0;
				if (stem(o) === fs) sc += 2;
				for (const n of otherNames(o)) if (fn.has(n)) sc += 1;
				if (sc === 0) continue;
				sc += 1 - gap / 5;
				if (sc > score) (score = sc), (best = i);
			}
			if (best !== null) used.add(best);
			out.push({ d: f.d, fox: f, oth: best !== null ? oth[best] : null });
		}
		oth.forEach((o, i) => {
			if (!used.has(i)) out.push({ d: o.d, fox: null, oth: o });
		});
		return out.sort((a, b) => (a.d < b.d ? -1 : a.d > b.d ? 1 : 0));
	});
	let pairedCount = $derived(pairs.filter((p) => p.fox && p.oth).length);

	// the short cut: a few words either side of the foul word
	const BEFORE = 4,
		AFTER = 4;
	function cut(r) {
		// in word mode the short line centres on the searched word instead
		let [a, b] = r.t;
		if (wordRx) {
			const m = wordRx.exec(r.s);
			if (m) [a, b] = [m.index, m.index + m[0].length];
		}
		const pre = r.s.slice(0, a).trim().split(/\s+/).filter(Boolean);
		const post = r.s.slice(b).trim().split(/\s+/).filter(Boolean);
		const before = pre.slice(-BEFORE).join(" ");
		const after = post.slice(0, AFTER).join(" ");
		// "flagrant-1", "Cunningham's": no gap where the sentence has none
		const gapBefore = a > 0 && /\s/.test(r.s[a - 1]) ? " " : "";
		const gapAfter = b < r.s.length && /\s/.test(r.s[b]) ? " " : "";
		return {
			before: (pre.length > BEFORE ? "…" : "") + before + gapBefore,
			term: r.s.slice(a, b),
			after: gapAfter + after + (post.length > AFTER ? "…" : "")
		};
	}
	// the whole sentence as written: nothing is marked automatically any more
	// — only your own <b> and ==…== in a hand-written slide
	function pieces(r) {
		return [{ text: r.s }];
	}
	function piecesMarked(r) {
		const marks = r.t[1] > r.t[0] ? [{ at: r.t, kind: "term" }] : [];
		if (r.n && (r.n[1] <= r.t[0] || r.n[0] >= r.t[1])) marks.push({ at: r.n, kind: "name" });
		if (wordRx) {
			const m = wordRx.exec(r.s);
			if (m && m.index + m[0].length <= r.t[0] || (m && m.index >= r.t[1] && !(r.n && m.index < r.n[1] && m.index + m[0].length > r.n[0])))
				marks.push({ at: [m.index, m.index + m[0].length], kind: "term" });
		}
		marks.sort((x, y) => x.at[0] - y.at[0]);
		const out = [];
		let i = 0;
		for (const m of marks) {
			if (m.at[0] > i) out.push({ text: r.s.slice(i, m.at[0]) });
			out.push({ text: r.s.slice(m.at[0], m.at[1]), kind: m.kind });
			i = m.at[1];
		}
		if (i < r.s.length) out.push({ text: r.s.slice(i) });
		return out;
	}
	const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	const when = (d) => (d ? `${MONTHS[+d.slice(5, 7) - 1]} ${+d.slice(8, 10)}, ${d.slice(0, 4)}` : "");

	// --- the reel: the line nearest the middle is the open one --------------
	let reelEl = $state(null);
	let reelH = $state(0);
	let active = $state(0);
	let ticking = false;
	function settle() {
		if (!reelEl) return;
		const box = reelEl.getBoundingClientRect();
		const mid = box.top + box.height / 2;
		let best = 0,
			gap = Infinity;
		for (const el of reelEl.querySelectorAll(".line")) {
			const r = el.getBoundingClientRect();
			const d = Math.abs(r.top + r.height / 2 - mid);
			if (d < gap) {
				gap = d;
				best = +el.dataset.i;
			}
		}
		active = best;
	}
	function onScroll() {
		if (ticking) return;
		ticking = true;
		requestAnimationFrame(() => {
			ticking = false;
			settle();
		});
	}
	// a fresh list starts at its first line
	$effect(() => {
		rows;
		pairs;
		active = 0;
		tick().then(() => {
			if (reelEl) reelEl.scrollTop = 0;
		});
	});
	function go(i) {
		const el = reelEl?.querySelector(`.line[data-i="${i}"]`);
		if (!el) return;
		active = i;
		el.scrollIntoView({ block: "center", behavior: "smooth" });
	}
	function onKey(e) {
		if (e.key === "ArrowDown") (e.preventDefault(), go(Math.min((paired ? pairs.length : rows.length) - 1, active + 1)));
		if (e.key === "ArrowUp") (e.preventDefault(), go(Math.max(0, active - 1)));
	}
</script>

<figure class="foul-reel" class:underline class:highlight>
	{#if !data && !ownSlides.length}
		<p class="note">Loading the sentences…</p>
	{:else}
		<div class="pick" hidden={pickList.length > 0 || ownSlides.length > 0}>
			<div class="who" role="group" aria-label="Player">
				{#if wordRx}
					<button class:active={who === ALL} onclick={() => (who = ALL)}><span>everyone</span></button>
				{/if}
				{#each players as name (name)}
					<button class:active={who === name} onclick={() => (who = name)} title={name}>
						{#if face(name)}<img src={face(name)} alt="" />{/if}
						<span>{surname(name)}</span>
					</button>
				{/each}
			</div>
			<div class="side" role="group" aria-label="Outlet" hidden={paired}>
				{#each OUTLETS as [key, label] (key)}
					<button class:active={side === key} onclick={() => (side = key)}>{label}</button>
				{/each}
			</div>
		</div>
		<p class="count" hidden={gallery}>
			{#if gallery}
				{""}
			{:else if paired && pickList.length}
				<b>{pairs.length}</b> hand-picked incidents. Fox News on the left, the other outlets on the right.
			{:else if paired}
				<b>{pairs.length.toLocaleString()}</b> incidents{who === ALL ? "" : ` involving ${surname(who)}`}, <b>{pairedCount}</b> told by both sides. Fox News on the left, the other outlets on the right.
			{:else if pickList.length}
				<b>{rows.length}</b> hand-picked sentences. Scroll through them.
			{:else}
				<b>{rows.length.toLocaleString()}</b>
				{rows.length === 1 ? "sentence" : "sentences"} about a foul{wordRx ? ` with “${String(word).trim()}”` : ""}{who === ALL
					? ""
					: ` and ${surname(who)}`}{side === "all" ? ` · ${foxCount.toLocaleString()} of them in Fox News` : ""}. Scroll through them.
			{/if}
		</p>

		{#if gallery}
			<div class="gallery-wrap">
				<button class="arrow prev" aria-label="Previous" disabled={slide === 0} onclick={() => goSlide(slide - 1)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" /></svg></button>
				<div class="gallery" bind:this={galleryEl} onscroll={onGalleryScroll} tabindex="0" role="list" aria-label="Incidents"
					onkeydown={(e) => {
						if (e.key === "ArrowRight") (e.preventDefault(), goSlide(slide + 1));
						if (e.key === "ArrowLeft") (e.preventDefault(), goSlide(slide - 1));
					}}
				>
					{#each pairs as pr, i (i + pr.d)}
						<div class="slide" role="listitem">
							<span class="vs" aria-hidden="true">vs.</span>
							{#each [["oth", pr.oth], ["fox", pr.fox]] as [sideKey, r] (sideKey)}
								{@const fox = sideKey === "fox"}
								{#if r}
									<figure class="clip" class:fox class:alt={!fox}>
										<figcaption class="mast" style:color={fox ? FOX : OTHER}>
											{#if LOGOS[r.o]}<img class="logo" src="{base}/logos/square/{LOGOS[r.o]}" alt="" />{/if}
											<span>{mast(r.o)}</span>
										</figcaption>
										{#if r.html}
											<p>{@html markup(r, fox ? FOX : OTHER)}</p>
										{:else}
											<p>
												{#each pieces(r) as piece}{#if piece.kind === "term"}<b
															class="term"
															style:color={fox ? FOX : OTHER}>{piece.text}</b
														>{:else if piece.kind === "name"}<b class="name">{piece.text}</b
														>{:else}{piece.text}{/if}{/each}
											</p>
										{/if}
										<p class="dateline">
											{r.dateText || when(r.d)}{#if r.h}&nbsp;· <span class="badge">headline</span>{/if}{#if r.u}&nbsp;· <a href={r.u} target="_blank" rel="noopener">article ↗</a>{/if}
										</p>
									</figure>
								{:else}
									<figure class="clip empty" class:fox><figcaption class="mast" style:color={fox ? FOX : OTHER}>{fox ? "Fox News" : "the other outlets"}</figcaption><p class="none">No sentence on this incident.</p></figure>
								{/if}
							{/each}
						</div>
					{/each}
				</div>
				<button class="arrow next" aria-label="Next" disabled={slide >= pairs.length - 1} onclick={() => goSlide(slide + 1)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" /></svg></button>
			</div>
			<div class="dots" role="tablist">
				{#each pairs as _, i (i)}
					<button class="dot-btn" class:on={i === slide} aria-label={`Incident ${i + 1}`} onclick={() => goSlide(i)}></button>
				{/each}
			</div>
		{:else}
		<div
			class="reel"
			style:height="{height}px"
			bind:this={reelEl}
			bind:clientHeight={reelH}
			onscroll={onScroll}
			onkeydown={onKey}
			tabindex="0"
			role="list"
			aria-label="Sentences"
		>
			<div class="pad" style:height="{Math.max(0, reelH / 2 - 24)}px"></div>
			{#if paired}
				{#each pairs as pr, i (i + pr.d + (pr.fox?.s ?? "") + (pr.oth?.s ?? ""))}
					<div class="line pair" class:open={i === active} data-i={i} role="listitem" onclick={() => go(i)}>
						{#each [["fox", pr.fox], ["oth", pr.oth]] as [sideKey, r] (sideKey)}
							{@const fox = sideKey === "fox"}
							<div class="col" class:empty={!r}>
								{#if !r}
									<p class="short none">—</p>
								{:else if i === active}
									<p class="full">
										{#each pieces(r) as piece}{#if piece.kind === "term"}<b
													class="term"
													style:color={fox ? FOX : OTHER}>{piece.text}</b
												>{:else if piece.kind === "name"}<b class="name">{piece.text}</b
												>{:else}{piece.text}{/if}{/each}
									</p>
									<p class="source">
										<span class="outlet" style:color={fox ? FOX : OTHER}>{r.o}</span>
										<span class="dot">·</span>
										{when(r.d)}
										{#if r.h}<span class="dot">·</span><span class="badge">headline</span>{/if}
										{#if r.u}<span class="dot">·</span><a href={r.u} target="_blank" rel="noopener">article ↗</a>{/if}
									</p>
								{:else}
									{@const c = cut(r)}
									<p class="short"><span class="ctx">{c.before}</span><b
											class="term"
											style:color={fox ? FOX : OTHER}>{c.term}</b
										><span class="ctx">{c.after}</span></p>
								{/if}
							</div>
						{/each}
					</div>
				{/each}
			{:else}
			{#each rows as r, i (r.o + r.d + r.s)}
				{@const fox = r.o === "Fox News"}
				<div
					class="line"
					class:open={i === active}
					class:fox
					data-i={i}
					role="listitem"
					onclick={() => go(i)}
				>
					{#if i === active}
						<p class="full">
							{#each pieces(r) as piece}{#if piece.kind === "term"}<b
										class="term"
										style:color={fox ? FOX : OTHER}>{piece.text}</b
									>{:else if piece.kind === "name"}<b class="name">{piece.text}</b
									>{:else}{piece.text}{/if}{/each}
						</p>
						<p class="source">
							<span class="outlet" style:color={fox ? FOX : OTHER}>{r.o}</span>
							<span class="dot">·</span>
							{when(r.d)}
							{#if r.h}<span class="dot">·</span><span class="badge">headline</span>{/if}
							{#if r.u}<span class="dot">·</span><a href={r.u} target="_blank" rel="noopener">article ↗</a>{/if}
						</p>
					{:else}
						{@const c = cut(r)}
						<p class="short"><span class="ctx">{c.before}</span><b
								class="term"
								style:color={fox ? FOX : OTHER}>{c.term}</b
							><span class="ctx">{c.after}</span></p>
					{/if}
				</div>
			{/each}
			{/if}
			<div class="pad" style:height="{Math.max(0, reelH / 2 - 24)}px"></div>
		</div>
		{/if}
	{/if}
</figure>

<style>
	.foul-reel {
		margin: 0;
		max-width: 760px;
		margin-inline: auto;
		font-family: var(--font-chart);
	}
	.note,
	.count {
		text-align: center;
		font-size: 13.5px;
		color: rgba(42, 21, 3, 0.75);
		margin: 8px 0 4px;
	}
	.count b {
		color: var(--color-ink);
	}

	/* the pickers: faces for players, three words for the outlet */
	.pick[hidden],
	.side[hidden] {
		display: none;
	}
	.pick {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
	}
	.who {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 4px 6px;
	}
	.who button {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		border: 1px solid rgba(42, 21, 3, 0.25);
		border-radius: 999px;
		background: rgba(255, 253, 248, 0.35);
		padding: 3px 9px 3px 4px;
		font: inherit;
		font-size: 12.5px;
		font-weight: 700;
		color: var(--color-ink);
		opacity: 0.65;
		cursor: pointer;
		transition: opacity 150ms ease, background 150ms ease;
	}
	.who button img {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		object-fit: cover;
		background: #fff;
	}
	.who button:hover {
		opacity: 0.9;
	}
	.who button.active {
		opacity: 1;
		background: rgba(255, 253, 248, 0.95);
		border-color: var(--color-ink);
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.18);
	}
	.side {
		display: flex;
		gap: 4px;
	}
	.side button {
		border: 1px solid rgba(42, 21, 3, 0.25);
		border-radius: 999px;
		background: rgba(255, 253, 248, 0.35);
		padding: 3px 10px;
		font: inherit;
		font-size: 12.5px;
		color: var(--color-ink);
		opacity: 0.65;
		cursor: pointer;
	}
	.side button.active {
		opacity: 1;
		font-weight: 800;
		background: rgba(255, 253, 248, 0.95);
		border-color: var(--color-ink);
	}

	/* the gallery: newspaper clippings, one incident per slide */
	.gallery-wrap {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-top: 10px;
	}
	.gallery {
		flex: 1 1 auto;
		min-width: 0;
		display: flex;
		overflow-x: auto;
		scroll-snap-type: x mandatory;
		scrollbar-width: none;
		outline: none;
		-webkit-overflow-scrolling: touch;
	}
	.gallery::-webkit-scrollbar {
		display: none;
	}
	.slide {
		position: relative;
		flex: 0 0 100%;
		scroll-snap-align: center;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 44px;
		padding: 18px 14px 22px;
		box-sizing: border-box;
		align-items: center;
	}
	/* the "vs." sits in the gap between the two clippings */
	.slide .vs {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		font-family: var(--font-sans);
		font-weight: 700;
		font-size: 20px;
		color: var(--color-ink);
		padding: 2px 6px;
		border-radius: 999px;
		z-index: 1;
		pointer-events: none;
	}
	.clip {
		margin: 0;
		background: var(--color-white);
		border: 1px solid var(--color-rule);
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
    	padding: 10px 15px;
		transform: rotate(-0.8deg);
		text-align: left;
	}
	.clip.alt {
		transform: rotate(0.7deg);
	}
	.clip .mast .logo {
		height: 24px;
		width: auto;
		max-width: 90px;
		object-fit: contain;
		vertical-align: middle;
		margin-right: 7px;
	}
	.clip .mast {
		display: flex;
		align-items: center;
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		border-bottom: 2px solid currentColor;
		padding-bottom: 4px;
		margin-bottom: 8px;
	}
	.clip p {
		margin: 0;
		font-family: var(--font-serif);
		font-size: 17px;
		font-weight: 400;
		line-height: 1.42;
		color: var(--color-ink-dark);
	}
	.clip .name,
	.clip :global(.name) {
		color: var(--color-orange-deep);
		font-family: var(--font-chart);
		font-weight: 800;
	}
	.clip :global(.term) {
		font-weight: 800;
		font-family: var(--font-chart);
	}
	.clip p :global(b),
	.clip p :global(strong) {
		font-weight: 700;
	}
	.clip p :global(a) {
		color: inherit;
	}
	/* <mark> or ==text==: the yellow marker pen, in every mark: mode */
	.clip p :global(mark) {
		background: linear-gradient(to top, rgba(255, 230, 0, 0.55) 0 78%, transparent 78%);
		box-decoration-break: clone;
		-webkit-box-decoration-break: clone;
		padding: 0 2px;
		margin: 0 -2px;
		border-radius: 2px;
		color: inherit;
	}
	.clip .dateline {
		margin-top: 8px;
		font-family: var(--font-chart);
		font-size: 12px;
		font-weight: 400;
		color: rgba(42, 21, 3, 0.65);
	}
	.clip .dateline a {
		color: inherit;
	}
	.clip.empty .none {
		font-weight: 400;
		font-style: italic;
		color: rgba(42, 21, 3, 0.55);
	}
	/* the arrows and dots match the headline gallery's */
	.arrow {
		flex: 0 0 auto;
		width: 38px;
		height: 38px;
		border-radius: 50%;
		border: 1px solid var(--color-rule);
		background: var(--color-white);
		color: var(--color-gray-950);
		cursor: pointer;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.15);
		padding: 0;
	}
	.arrow :global(svg) {
		width: 20px;
		height: 20px;
	}
	.arrow:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	.arrow:disabled:hover {
		background: var(--color-white);
	}
	.dots {
		display: flex;
		justify-content: center;
		gap: 6px;
		margin-top: 2px;
	}
	.dot-btn {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		border: 0;
		background: var(--color-rule);
		padding: 0;
		cursor: pointer;
	}
	.dot-btn.on {
		background: var(--color-gray-950);
	}
	@media (max-width: 640px) {
		/* stacked on a phone: the two clippings close together, the type a
		   touch smaller, so a pair fits one screen */
		.slide {
			grid-template-columns: 1fr;
			gap: 10px;
			padding: 10px 10px 14px;
			/* rows hug their clippings instead of stretching to share the height */
			align-content: center;
		}
		/* stacked, the badge takes its own row between the two clippings (it is
		   first in the markup; order puts it in the middle) */
		.slide .vs {
			position: static;
			transform: none;
			order: 1;
			justify-self: center;
			margin: -4px 0;
			font-size: 16px;
			padding: 1px 6px;
		}
		.slide .clip:first-of-type {
			order: 0;
		}
		.slide .clip:last-of-type {
			order: 2;
		}
		.clip {
			padding: 9px 12px 9px;
		}
		.clip p {
			font-size: 14px;
			line-height: 1.38;
		}
	}

	/* the reel */
	.reel {
		position: relative;
		overflow-y: auto;
		scroll-snap-type: y proximity;
		outline: none;
		text-align: center;
		/* fade the ends so the reel reads as continuing */
		mask-image: linear-gradient(to bottom, transparent, #000 12%, #000 88%, transparent);
		-webkit-mask-image: linear-gradient(to bottom, transparent, #000 12%, #000 88%, transparent);
		scrollbar-width: none;
	}
	.reel::-webkit-scrollbar {
		display: none;
	}
	.line.pair {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0 28px;
		text-align: left;
		align-items: start;
	}
	.line.pair .col:first-child {
		text-align: right;
	}
	.line.pair .col.empty .none {
		opacity: 0.25;
	}
	.line.pair .full {
		font-size: 17px;
	}
	.line.pair .short {
		white-space: normal;
	}
	@media (max-width: 640px) {
		.line.pair {
			grid-template-columns: 1fr;
			gap: 6px 0;
			text-align: left;
		}
		.line.pair .col:first-child {
			text-align: left;
		}
	}
	.line {
		scroll-snap-align: center;
		padding: 7px 24px;
		cursor: pointer;
		transition: opacity 200ms ease;
	}
	.short {
		margin: 0;
		font-size: 17px;
		line-height: 1.3;
		opacity: 0.6;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.short .ctx {
		color: var(--color-ink);
	}
	.term {
		font-weight: 800;
	}
	.line.open {
		padding: 14px 24px;
	}
	.full {
		margin: 0;
		font-family: var(--font-serif);
		font-size: 21px;
		line-height: 1.4;
		color: var(--color-ink);
	}
	.full .term {
		font-family: var(--font-chart);
		font-size: 1.05em;
	}
	.full .name {
		color: var(--color-orange-deep);
		font-family: var(--font-chart);
	}
	.source {
		margin: 6px 0 0;
		font-size: 13px;
		color: rgba(42, 21, 3, 0.7);
	}
	.source .outlet {
		font-weight: 800;
	}
	.source .dot {
		margin: 0 5px;
		opacity: 0.5;
	}
	.source .badge {
		text-transform: uppercase;
		letter-spacing: 0.04em;
		font-size: 10.5px;
		font-weight: 800;
		border: 1px solid rgba(42, 21, 3, 0.35);
		border-radius: 3px;
		padding: 0 4px;
	}
	.source a {
		color: inherit;
	}
	@media (max-width: 640px) {
		.short {
			font-size: 15px;
		}
		.full {
			font-size: 18px;
		}
	}
	/* mark: underline — the word and the name keep the text's weight and
	   take a coloured underline instead of bold */
	.foul-reel.underline :global(.term),
	.foul-reel.underline :global(.name) {
		font-weight: inherit;
		font-family: inherit;
		font-size: inherit;
		text-decoration: underline;
		text-decoration-thickness: 2px;
		text-underline-offset: 3px;
	}
	.foul-reel.underline :global(.name) {
		text-decoration-color: var(--color-orange-deep);
	}
	/* mark: highlight — a yellow marker pen behind the words instead */
	.foul-reel.highlight :global(.term),
	.foul-reel.highlight :global(.name) {
		font-weight: inherit;
		font-family: inherit;
		font-size: inherit;
		color: inherit;
		background: linear-gradient(to top, rgba(255, 230, 0, 0.55) 0 78%, transparent 78%);
		box-decoration-break: clone;
		-webkit-box-decoration-break: clone;
		padding: 0 2px;
		margin: 0 -2px;
		border-radius: 2px;
	}
	/* your own <b> is always bold and ==…== always yellow, whatever mark:
	   says; mark: only governs the automatic word and name */
	.clip p :global(b:not(.term):not(.name)),
	.clip p :global(strong) {
		font-weight: 700 !important;
		text-decoration: none;
		background: none;
	}
</style>
