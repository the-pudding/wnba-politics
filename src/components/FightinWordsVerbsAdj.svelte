<script>
	// Verb-and-adjective scatter walked through
	// Each step takes: who, rel, vs, pair, words, text
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import FightinWords from "$components/FightinWords.svelte";
	import WordBars from "$components/WordBars.svelte";
	import {
		playerWordsSource,
		playerWordsPeople,
		playerWordsOutlets,
		playerOutletFile
	} from "../utils/playerWords.js";
	import { COMPARISON, LOGO } from "$utils/outlets.js";
	import LogoSelect from "$components/helpers/LogoSelect.svelte";
	import { checks } from "$utils/checks.svelte.js";
	import { base } from "$app/paths";
	import roster from "$data/people.json";
	import data from "$data/player_words.json";
	const faceFiles = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)])
	);

	// chart: "scatter" (the quadrant) or "bars" (mirrored top words)
	let {
		steps = null,
		chart = "scatter",
		labels = "on",
		scale = "linear",
		caps = false,
		scores = false,
		note = undefined,
		// the Doc's words, each optional, {slots} filled in (utils/fill.js):
		// {player} the player's name, {outlet} a single outlet, {unit} the
		// Words / Phrases tab's name, {fox} {others} the word counts
		headDescribe = "",
		headPlay = "",
		headSubject = "",
		headObject = "",
		headAll = "",
		comparedWith = "",
		// phones: "vs." in place of "compared with", and short tab names
		phoneVs = "",
		shortDescribe = "",
		shortPlay = "",
		shortSubject = "",
		shortObject = "",
		shortAll = "",
		allOutlets = "",
		tabDescribe = "",
		tabPlay = "",
		tabSubject = "",
		tabObject = "",
		tabAll = "",
		tabWords = "",
		tabPhrases = "",
		morePlayers = "",
		tooFew = "",
		tooFewOutlet = "",
		foxHead = "",
		othersHead = "",
		caption: captionText = "",
		outletCaption = "",
		previous = "",
		next = "",
		range = "",
		hoverCounts = "",
		...unused
	} = $props();
	import { fill, or } from "$utils/fill.js";

	const list = (value) =>
		(value ?? "")
			.split(",")
			.map((w) => w.trim())
			.filter(Boolean);

	const STEPS = $derived(
		(steps ?? [])
			.filter((step) => (step.text ?? "").trim())
			.map((step) => ({
				who: (step.who ?? "").trim(),
				rel: (step.rel ?? "describe").trim(),
				vs: (step.vs ?? "outlets").trim(),
				pair: (step.pair ?? "").trim() || null,
				words: list(step.words),
				// title: optional Doc heading replacing the generated one
				title: (step.title ?? "").trim(),
				// explore: true — the reader picks the player and the relation
				explore: step.explore === true || step.explore === "true",
				html: step.text ?? ""
			}))
	);

	let index = $state(0);
	// once no card is in view the chart keeps its last state
	let last = $state(0);
	$effect(() => {
		if (index !== undefined && index !== null) last = index;
	});
	let current = $derived(STEPS[last] ?? STEPS[0]);

	// the relations as tabs (2026-10-02), each with the plain-language heading
	// it gives the chart
	const RELATIONS = $derived([
		["describe", or(tabDescribe, "Described as")],
		["play", or(tabPlay, "Her play")],
		["subject", or(tabSubject, "What she does")],
		["object", or(tabObject, "Done to her")],
		["all", or(tabAll, "Every word")]
	]);
	// phones: the heading follows the tab as on a desktop, "vs.
	// [outlets]" and words / phrases share a line, and the tabs take their
	// short names
	let narrow = $state(false);
	$effect(() => {
		const mq = matchMedia("(max-width: 640px)");
		const sync = () => (narrow = mq.matches);
		sync();
		mq.addEventListener("change", sync);
		return () => mq.removeEventListener("change", sync);
	});
	const SHORT = $derived({
		describe: or(shortDescribe, "Described"),
		play: or(shortPlay, "Play"),
		subject: or(shortSubject, "Does"),
		object: or(shortObject, "Done to"),
		all: or(shortAll, "All")
	});
	const HEADING = $derived({
		describe: (n) =>
			fill(or(headDescribe, "How Fox News describes {player}"), { player: n }),
		play: (n) =>
			fill(or(headPlay, "How Fox News describes {player}’s play"), {
				player: n
			}),
		subject: (n) =>
			fill(or(headSubject, "What Fox News says {player} does"), { player: n }),
		object: (n) =>
			fill(or(headObject, "What Fox News says is done to {player}"), {
				player: n
			}),
		all: (n) =>
			fill(or(headAll, "Every word Fox News ties to {player}"), { player: n })
	});
	// players with a Fox-versus-the-other-outlets comparison stored, listed
	// by surname in the picker
	const PEOPLE = playerWordsPeople();
	const slugOf = (name) =>
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");
	const bySurname = (a, b) =>
		a.split(" ").pop().localeCompare(b.split(" ").pop()) || a.localeCompare(b);
	// the row: the players Fox writes about most first, as many as fit, then
	// a button for the rest (2026-10-02)
	const foxWords = (name) => data.players?.[name]?.vsCounts?.all?.clark ?? 0;
	const PICKABLE = [...PEOPLE].sort(
		(a, b) => foxWords(b) - foxWords(a) || bySurname(a, b)
	);
	let rowW = $state(760);
	const SLOT = $derived(rowW < 560 ? 62 : 76);
	let fits = $derived(Math.max(3, Math.floor((rowW + 4) / SLOT)));
	let inRow = $derived.by(() => {
		if (PICKABLE.length <= fits) return PICKABLE;
		const row = PICKABLE.slice(0, fits - 1);
		// a player picked from the list takes the row's last place
		if (pickedWho && !row.includes(pickedWho)) row[row.length - 1] = pickedWho;
		return row;
	});
	let rest = $derived(PICKABLE.filter((n) => !inRow.includes(n)));
	let moreOpen = $state(false);
	let moreEl = $state(null);
	$effect(() => {
		if (!moreOpen) return;
		const close = (e) => {
			if (
				e.type === "keydown" ? e.key === "Escape" : !moreEl?.contains(e.target)
			)
				moreOpen = false;
		};
		document.addEventListener("pointerdown", close);
		document.addEventListener("keydown", close);
		return () => {
			document.removeEventListener("pointerdown", close);
			document.removeEventListener("keydown", close);
		};
	});
	const faceUrl = (name) => {
		const slug = slugOf(name);
		return faceFiles[slug] ? `${base}/net/${slug}${faceFiles[slug]}` : null;
	};
	let pickedWho = $state(PEOPLE[0] ?? "");
	let pickedRel = $state("describe");
	// "all": Fox against every comparison outlet pooled (the story's chart);
	// an outlet's name: Fox against that outlet alone, to see what each one
	// contributes to the pooled picture
	let pickedOutlet = $state("all");
	$effect(() => {
		const step = current;
		if (step.who && PEOPLE.includes(step.who)) pickedWho = step.who;
		if (step.rel) pickedRel = step.rel;
		pickedOutlet = "all";
	});
	// the outlets with enough of this player's words, in this relation, to
	// stand alone; the rest grey out
	// A check, shown only with ?checks in the address (utils/checks.svelte.js):
	// with or without college coverage. The no-college numbers come from a rerun
	// of notebook 09 with college articles dropped (static/data/nocollege/,
	// 2026-09-30; words only, not two-word phrases).
	let college = $state("with");
	let ncWords = $state(null);
	$effect(() => {
		if (college !== "without" || ncWords) return;
		fetch(`${base}/data/nocollege/src/player_words.json`)
			.then((r) => r.json())
			.then((v) => (ncWords = v))
			.catch(() => {});
	});
	// words, or two-word phrases (each relation's word and its partner in the
	// parse: "foul out", "cheap shot"; notebook 09, 2026-09-30). The phrases
	// ship one file per player (static/data/player_phrases2), fetched on use
	let unit = $state("words");
	let phrases = $derived(unit === "phrases");
	const suffix = (rel) => (phrases ? rel + "2" : rel);
	let phraseFiles = $state({});
	const phraseFetching = new Set();
	$effect(() => {
		const who = pickedWho;
		if (!phrases || !who || phraseFiles[who] || phraseFetching.has(who)) return;
		phraseFetching.add(who);
		fetch(`${base}/data/player_phrases2/${slugOf(who)}.json`)
			.then((r) => (r.ok ? r.json() : {}))
			.catch(() => ({}))
			.then((v) => (phraseFiles = { ...phraseFiles, [who]: v }));
	});
	// the player's block with the phrase relations merged in
	let phraseAlt = $derived.by(() => {
		const f = phraseFiles[pickedWho];
		const base_ = data.players?.[pickedWho];
		if (!phrases || !f || !base_) return null;
		const merged = { ...base_ };
		for (const part of [
			"relations",
			"counts",
			"vsOutlets",
			"vsCounts",
			"vsByOutlet"
		])
			merged[part] = { ...(base_[part] ?? {}), ...(f[part] ?? {}) };
		return { ...data, players: { ...data.players, [pickedWho]: merged } };
	});
	let alt = $derived(
		phrases ? phraseAlt : college === "without" ? ncWords : null
	);
	let src_ = $derived(alt ?? data);
	let outletsHere = $derived(
		new Set(playerWordsOutlets(pickedWho, suffix(pickedRel), alt))
	);
	$effect(() => {
		if (pickedOutlet !== "all" && !outletsHere.has(pickedOutlet))
			pickedOutlet = "all";
	});
	let outlet = $derived(pickedOutlet === "all" ? null : pickedOutlet);
	// a single outlet's comparisons live in one file per player
	// (static/data/player_outlet, notebooks/site_data.py), fetched on first use
	let byOutlet = $state({});
	const fetching = new Set();
	$effect(() => {
		const who = pickedWho;
		const nc = college === "without" && !phrases;
		const k = nc ? `nc:${who}` : who;
		if (!outlet || !who || byOutlet[k] || fetching.has(k)) return;
		fetching.add(k);
		fetch(
			`${base}/data/${nc ? "nocollege/static/" : ""}${playerOutletFile(who)}`
		)
			.then((r) => (r.ok ? r.json() : {}))
			.catch(() => ({}))
			.then((block) => (byOutlet = { ...byOutlet, [k]: block }));
	});
	// "all" is the story's own chart; then each comparison outlet on its own
	const OUTLET_OPTIONS = ["all", ...COMPARISON];
	// a smaller cast member has too few attachments for some relations; those
	// buttons grey out, and the choice falls back to every word
	let available = $derived(
		new Set(
			Object.keys(src_?.players?.[pickedWho]?.vsOutlets ?? {})
				.filter((k) => k.endsWith("2") === phrases)
				.map((k) => (phrases ? k.slice(0, -1) : k))
		)
	);
	$effect(() => {
		if (available.size && !available.has(pickedRel)) pickedRel = "all";
	});
	// what the chart shows: the picker's choice; the step's own title, words
	// and pair comparison apply while the choice still matches the step
	let onStep = $derived(pickedWho === current.who && pickedRel === current.rel);
	let shown = $derived(
		onStep
			? { ...current, outlet, title: outlet || phrases ? "" : current.title }
			: {
					who: pickedWho,
					rel: pickedRel,
					vs: "outlets",
					pair: null,
					words: [],
					title: "",
					outlet
				}
	);
	// Fox's column head carries its wordmark; the other side is named in words
	let fresh = $derived.by(() => {
		const src = playerWordsSource({
			...shown,
			rel: suffix(shown.rel),
			byOutlet:
				byOutlet[
					college === "without" && !phrases ? `nc:${shown.who}` : shown.who
				] ?? null,
			alt
		});
		if (!src || shown.vs !== "outlets") return src;
		return { ...src, topLogo: LOGO["Fox News"] };
	});
	// while a picked player's file is still on its way (phrases, a single
	// outlet), the chart keeps showing what it had instead of blinking out
	let waiting = $derived(
		(phrases && !phraseFiles[pickedWho]) ||
			(!!outlet &&
				!byOutlet[
					college === "without" && !phrases ? `nc:${pickedWho}` : pickedWho
				] &&
				!data.players?.[pickedWho]?.vsByOutlet?.[suffix(pickedRel)]?.[outlet])
	);
	let lastSource = null;
	let source = $derived.by(() => {
		if (fresh) lastSource = fresh;
		const src = fresh ?? (waiting ? lastSource : null);
		// against the outlets, heads at the bars' edges saying who uses a word
		// more, as on the main chart (2026-10-02)
		if (!src || shown.vs !== "outlets") return src;
		return {
			...src,
			topHead: or(foxHead, "Fox News uses more"),
			bottomHead: outlet
				? outlet + (/s$/.test(outlet) ? " use more" : " uses more")
				: or(othersHead, "Other outlets use more")
		};
	});
	// the line under the bars, in the main chart's source-line style
	let caption = $derived.by(() => {
		if (shown.vs !== "outlets") return note;
		const counts = src_?.players?.[shown.who]?.vsCounts?.[suffix(shown.rel)];
		const n = (v) => Number(v ?? 0).toLocaleString();
		const vars = {
			unit: phrases ? or(tabPhrases, "Phrases") : or(tabWords, "Words"),
			player: shown.who,
			outlet,
			fox: n(counts?.clark),
			others: n(counts?.others)
		};
		const given = outlet ? outletCaption : captionText;
		if (String(given).trim()) return fill(given, vars);
		return (
			`${phrases ? "Two-word phrases" : "Words"} grammatically tied to ${shown.who} in WNBA articles (a dependency parse, with coreference so “she” counts)` +
			(counts && !outlet
				? `: Fox News ${n(counts.clark)}, the other outlets ${n(counts.others)}`
				: "") +
			`. Ranked by weighted log-odds with an informative prior (Monroe et al. 2008); bar length is the square root of the z-score. Faded bars are within noise (|z| under 1.96). Hover a bar for an example.`
		);
	});
</script>

<section
	class="words-scrolly"
	class:bars={chart === "bars"}
	class:open={index >= STEPS.length}
	class:menu-open={moreOpen}
>
	<div class="sticky">
		{#if source}
			<!-- the players as faces in a row, one tap each (2026-10-02) -->
			<div
				class="players"
				role="radiogroup"
				aria-label="Player"
				bind:clientWidth={rowW}
			>
				{#each inRow as name (name)}
					{@const face = faceUrl(name)}
					<button
						type="button"
						role="radio"
						class="player"
						class:on={pickedWho === name}
						aria-checked={pickedWho === name}
						onclick={() => (pickedWho = name)}
					>
						{#if face}<img src={face} alt="" />{:else}<span class="blank"
							></span>{/if}
						<span class="player-name"
							>{name.split(" ")[0]}<br />{name
								.split(" ")
								.slice(1)
								.join(" ")}</span
						>
					</button>
				{/each}
				{#if rest.length}
					<div class="more" bind:this={moreEl}>
						<button
							type="button"
							class="player more-btn"
							class:open={moreOpen}
							aria-haspopup="listbox"
							aria-expanded={moreOpen}
							onclick={() => (moreOpen = !moreOpen)}
						>
							<span class="blank more-count">+{rest.length}</span>
							<span class="player-name"
								>{@html or(morePlayers, "More players").replace(
									/ /,
									"<br />"
								)}</span
							>
						</button>
						{#if moreOpen}
							<ul
								class="more-list"
								role="listbox"
								aria-label={or(morePlayers, "More players")}
							>
								{#each rest as name (name)}
									{@const face = faceUrl(name)}
									<li role="option" aria-selected="false">
										<button
											type="button"
											onclick={() => ((pickedWho = name), (moreOpen = false))}
										>
											{#if face}<img src={face} alt="" />{:else}<span
													class="blank"
												></span>{/if}
											{name}
										</button>
									</li>
								{/each}
							</ul>
						{/if}
					</div>
				{/if}
			</div>
			<!-- the heading, in plain words that follow the tab; a step's own
			     title, or a pair's, as before -->
			<div class="head">
				{#if narrow && shown.vs === "outlets"}
					<p class="heading">
						{HEADING[shown.rel]?.(shown.who) ?? source.relation}
					</p>
				{:else if shown.title}
					<p class="heading">{@html shown.title}</p>
				{:else if shown.vs === "outlets"}
					<p class="heading">
						{HEADING[shown.rel]?.(shown.who) ?? source.relation}
					</p>
				{/if}
				{#if shown.vs === "outlets" && (narrow || !shown.title)}
					<!-- a div, not a p: the menu inside renders block elements -->
					<div class="subheading">
						<span
							>{narrow
								? or(phoneVs, "vs.")
								: or(comparedWith, "compared with")}</span
						>
						<LogoSelect
							options={OUTLET_OPTIONS}
							bind:value={pickedOutlet}
							logoOf={(o) => (o === "all" ? null : (LOGO[o] ?? null))}
							nameOf={(o) =>
								o === "all" ? or(allOutlets, "six other outlets") : o}
							isDisabled={(o) =>
								o !== "all" && !outletsHere.has(o)
									? fill(
											or(
												tooFewOutlet,
												"Too few words about {player} in {outlet}"
											),
											{ player: pickedWho, outlet: o }
										)
									: false}
							label="Compared with"
						/>
						{#if narrow}{@render unitSwitch()}{/if}
					</div>
				{:else if shown.vs !== "outlets" && !shown.title}
					<p class="heading">
						<b>{source.relation}</b><br />
						{source.topLabel} <span class="vs">vs.</span>
						{source.bottomLabel}
					</p>
				{/if}
				{#if checks.on}
					<!-- a check: see `college` above -->
					<LogoSelect
						options={["with", "without"]}
						bind:value={college}
						nameOf={(o) => (o === "with" ? "With college" : "Without college")}
						label="College coverage"
					/>
				{/if}
			</div>
			<!-- the relations as tabs on a rule; words or phrases a quiet switch
			     at its right end -->
			{#snippet unitSwitch()}
				<div class="unit-switch" role="group" aria-label="Words or phrases">
					<button
						type="button"
						class:on={unit === "words"}
						aria-pressed={unit === "words"}
						onclick={() => (unit = "words")}>{or(tabWords, "Words")}</button
					>
					<button
						type="button"
						class:on={unit === "phrases"}
						aria-pressed={unit === "phrases"}
						onclick={() => (unit = "phrases")}
						>{or(tabPhrases, "Phrases")}</button
					>
				</div>
			{/snippet}
			<div class="tabrow">
				<div class="rel-tabs" role="tablist" aria-label="Kind of word">
					{#each RELATIONS as [rel, label] (rel)}
						<button
							type="button"
							role="tab"
							class:on={pickedRel === rel}
							aria-selected={pickedRel === rel}
							disabled={!available.has(rel)}
							title={available.has(rel)
								? ""
								: fill(or(tooFew, "Too few words of this kind for {player}"), {
										player: pickedWho
									})}
							onclick={() => (pickedRel = rel)}
							>{narrow ? SHORT[rel] : label}</button
						>
					{/each}
				</div>
				{#if !narrow}{@render unitSwitch()}{/if}
			</div>
			{#if chart === "bars"}
				<WordBars
					{source}
					{labels}
					{scale}
					{caps}
					{scores}
					highlight={shown.words}
					top={12}
					fill
					note={caption}
					noteKind={shown.vs === "outlets" ? "source" : ""}
					{previous}
					{next}
					{range}
					{hoverCounts}
				/>
			{:else}
				<FightinWords {source} highlight={shown.words} bare controls={false} />
			{/if}
		{:else}
			<p class="heading">
				No comparison stored for {shown.who} · {shown.rel}
			</p>
		{/if}
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div
					class="step"
					class:active={last === i}
					class:explore={step.explore}
				>
					<p class="card">{@html step.html}</p>
				</div>
			{/each}
			<!-- cardless final beat: the chart stays put for another screen and a
			     half with every card gone, so the reader can pick and hover -->
			<div class="step step-open" aria-hidden="true"></div>
		</Scrolly>
	</div>
</section>

<style>
	.words-scrolly {
		position: relative;
		margin: 24px 0;
	}

	.sticky {
		position: sticky;
		top: 0;
		height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}
	/* the bars hang from a fixed top: a step with more or fewer words only
	   lengthens the chart downward, instead of re-centring everything */
	.words-scrolly.bars .sticky {
		justify-content: flex-start;
		padding-top: 4vh;
		box-sizing: border-box;
	}
	.sticky :global(.fightin-words),
	.sticky :global(.word-bars) {
		width: min(900px, 100%);
	}
	/* the players: faces in a row that scrolls sideways */
	.players {
		position: relative;
		display: flex;
		gap: 4px;
		width: 100%;
		max-width: 760px;
		padding: 4px 2px 8px;
		margin: 0 0 6px;
	}
	.player {
		appearance: none;
		flex: 0 0 auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		width: 72px;
		padding: 0;
		border: 0;
		border-radius: 0;
		background: none;
		font: inherit;
		color: var(--color-ink-dark);
		cursor: pointer;
	}
	.player img,
	.player .blank {
		width: 46px;
		height: 46px;
		border-radius: 50%;
		object-fit: cover;
		background: #f6e7d6;
		transition: transform 120ms ease;
	}
	.player-name {
		font-family: var(--font-sans);
		font-size: 11px;
		font-weight: 700;
		line-height: 1.15;
		text-align: center;
		color: rgba(42, 21, 3, 0.7);
	}
	.player:hover img {
		transform: translateY(-2px);
	}
	.player.on img,
	.player.on .blank {
		box-shadow:
			0 0 0 2px var(--color-page-orange),
			0 0 0 4px var(--color-ink-dark);
	}
	.player.on .player-name {
		color: var(--color-ink-dark);
	}
	.player:focus-visible {
		outline: none;
	}
	.player:focus-visible .player-name {
		text-decoration: underline;
	}
	/* the open list sits over the step cards */
	.words-scrolly.menu-open .sticky {
		z-index: 2;
	}
	/* the players past the row, in a list under the +N button */
	.more {
		position: relative;
		margin-left: auto;
	}
	.more-count {
		display: flex;
		align-items: center;
		justify-content: center;
		box-sizing: border-box;
		border: 1.5px dashed rgba(42, 21, 3, 0.45);
		background: transparent !important;
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 700;
		color: var(--color-ink-dark);
	}
	.more-btn.open .more-count {
		border-style: solid;
		border-color: var(--color-ink-dark);
	}
	.more-list {
		position: absolute;
		z-index: 20;
		top: calc(100% + 4px);
		right: 0;
		width: 240px;
		max-height: 340px;
		overflow-y: auto;
		margin: 0;
		padding: 6px;
		list-style: none;
		background: #fff;
		border-radius: 4px;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.18);
	}
	.more-list button {
		display: flex;
		align-items: center;
		gap: 10px;
		width: 100%;
		padding: 5px 6px;
		border: 0;
		border-radius: 3px;
		background: none;
		font-family: var(--font-sans);
		font-size: 14px;
		font-weight: 600;
		text-align: left;
		color: var(--color-ink-dark);
		cursor: pointer;
	}
	.more-list button:hover,
	.more-list button:focus-visible {
		background: #f6efe6;
		outline: none;
	}
	.more-list img,
	.more-list .blank {
		flex: 0 0 auto;
		width: 30px;
		height: 30px;
		border-radius: 50%;
		object-fit: cover;
		background: #f6e7d6;
	}
	/* the heading in plain words, and what it is compared with */
	.head {
		width: 100%;
		max-width: 760px;
		margin: 0 0 10px;
	}
	.heading {
		margin: 0;
		font-family: var(--font-graphic);
		font-size: 24px;
		font-weight: 700;
		line-height: 1.22;
		letter-spacing: -0.01em;
		text-align: left;
	}
	.heading .vs {
		font-weight: 400;
		opacity: 0.7;
	}
	.subheading {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 6px;
		margin: 2px 0 0;
		font-family: var(--font-graphic);
		font-size: 15px;
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
	/* the compare-with menu sits in the line as a quiet underlined word */
	.subheading :global(.logo-select .current) {
		height: auto;
		min-width: 0;
		padding: 0 18px 0 0;
		border: 0;
		border-bottom: 1.5px solid currentColor;
		border-radius: 0;
		background: transparent;
		font-family: var(--font-graphic);
		font-size: 15px;
		color: var(--color-ink-dark);
	}
	.subheading :global(.logo-select .current::after) {
		right: 0;
	}
	/* phones: words / phrases at the right end of the "vs." line */
	.subheading .unit-switch {
		margin-left: auto;
		padding-left: 10px;
	}
	/* the relations as tabs on a rule; words / phrases at its right end */
	.tabrow {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		gap: 4px 20px;
		width: 100%;
		max-width: 760px;
		margin: 0 0 10px;
		border-bottom: 1px solid var(--color-ink-dark);
	}
	.rel-tabs {
		display: flex;
		flex-wrap: wrap;
		gap: 4px 16px;
	}
	.rel-tabs button,
	.unit-switch button {
		appearance: none;
		margin: 0 0 -1px;
		padding: 0 0 8px;
		border: 0;
		border-radius: 0;
		border-bottom: 3px solid transparent;
		background: none;
		font-family: var(--font-sans);
		font-size: 14px;
		font-weight: 700;
		color: rgba(42, 21, 3, 0.6);
		cursor: pointer;
	}
	.rel-tabs button.on {
		color: var(--color-ink-dark);
		border-bottom-color: var(--color-ink-dark);
	}
	.rel-tabs button:hover:not(:disabled),
	.unit-switch button:hover {
		color: var(--color-ink-dark);
	}
	.rel-tabs button:disabled {
		opacity: 0.35;
		cursor: not-allowed;
	}
	.rel-tabs button:focus-visible,
	.unit-switch button:focus-visible {
		outline: none;
		text-decoration: underline;
	}
	.unit-switch {
		display: flex;
		gap: 12px;
		margin-left: auto;
	}
	.unit-switch button {
		font-size: 13px;
		border-bottom: 0;
		padding-bottom: 9px;
	}
	.unit-switch button.on {
		color: var(--color-ink-dark);
		text-decoration: underline;
		text-decoration-thickness: 2px;
		text-underline-offset: 4px;
	}
	@media (max-width: 640px) {
		.player {
			width: 58px;
		}
		.player img,
		.player .blank {
			width: 38px;
			height: 38px;
		}
		.player-name {
			font-size: 10px;
		}
		.heading {
			font-size: 20px;
		}
		.subheading,
		.subheading :global(.logo-select .current) {
			font-size: 14px;
		}
		/* the five short tabs spread across the row, all in view */
		.rel-tabs {
			flex: 1 1 auto;
			flex-wrap: nowrap;
			justify-content: space-between;
			gap: 8px;
		}
		.rel-tabs button {
			flex: 0 0 auto;
			font-size: 13.5px;
			padding-bottom: 6px;
			white-space: nowrap;
		}
		.unit-switch {
			flex: 0 0 auto;
			gap: 8px;
		}
		.unit-switch button {
			font-size: 12px;
			padding-bottom: 7px;
		}
	}
	.words-scrolly:not(.bars) .sticky :global(svg) {
		max-height: 74vh;
	}

	.steps {
		position: relative;
		z-index: 1;
		margin-top: -100vh;
		pointer-events: none;
	}
	.step {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
	}
	.card {
		/* wider only where the screen leaves a margin beside the 900px chart */
		max-width: clamp(300px, calc((100vw - 900px) / 2 - 24px), 380px);
		margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px;
		border-radius: 3px;
		font-size: var(--step-text);
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.step.active .card {
		opacity: 1;
	}
	.step-open {
		height: 150vh;
	}
	/* on the open beat the cards leave the chart alone */
	.words-scrolly.open .card {
		opacity: 0;
	}
	/* the explore card keeps out of the chart's way */
	.step.explore {
		align-items: flex-end;
		padding-bottom: 6vh;
		box-sizing: border-box;
	}

	@media (max-width: 860px) {
		.card {
			max-width: 84vw;
		}
	}
	/* the step cards let the pointer through to the chart behind them, but a
	   link in a step's text must still be clickable */
	.steps :global(a) {
		pointer-events: auto;
	}
</style>
