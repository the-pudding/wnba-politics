<script>
	// How Fox frames each player — tone / political / appearance / celebrity —
	import FacesBeeswarm from "$components/FacesBeeswarm.svelte";
	import FramingControls from "$components/FramingControls.svelte";
	import HeadlineTable from "$components/HeadlineTable.svelte";
	import framingRows from "$data/framing.csv";
	import roster from "$data/people.json";

	// everyone in the framing data, players first, each alphabetical by surname
	const bySurname = (a, b) => a.split(" ").pop().localeCompare(b.split(" ").pop());
	const PEOPLE = [...new Set(framingRows.map((r) => r.name))];
	const PLAYERS = PEOPLE.filter((n) => roster[n]?.group === "players").sort(bySurname);

	let {
		words = [],
		// the first picture: "rows" (a dot plot, one row per player) or "swarm"
		layout: startLayout = "swarm",
		// morph: true — start with the rows and, once the chart has been in
		// view a moment, let the faces slide into the swarm
		morph = false
	} = $props();
	const ROWS = new Set(["rows", "list", "dots", "dot", "dotplot"]);
	let layout = $state(
		ROWS.has(String(startLayout).trim().toLowerCase()) ? "rows" : "swarm"
	);
	const morphing = morph === true || String(morph).trim().toLowerCase() === "true";
	let chartEl = $state(null);
	$effect(() => {
		if (!morphing || !chartEl || layout !== "rows") return;
		let timer = null;
		const io = new IntersectionObserver(
			([entry]) => {
				if (!entry.isIntersecting) return;
				io.disconnect();
				timer = setTimeout(() => (layout = "swarm"), 1800);
			},
			{ threshold: 0.35 }
		);
		io.observe(chartEl);
		return () => {
			io.disconnect();
			clearTimeout(timer);
		};
	});

	// the cross-outlet differential and receiving-end measures are still computed upstream
	const VIEWS = [
		{
			key: "tone",
			label: "Tone",
			blurb:
				"Average sentiment of every Fox headline naming her, from −1 to +1."
		},
		{
			key: "political",
			label: "Politicized",
			blurb:
				"Share of Fox headlines carrying political or culture-war language."
		},
		{
			key: "appearance",
			label: "Appearance",
			blurb: "Share of Fox headlines discussing appearances."
		},
		{
			key: "celebrity",
			label: "Celebrity",
			blurb:
				"Share of her Fox headlines about private life, appearance, and celebrity."
		},
		{
			key: "performance",
			label: "Performance",
			blurb:
				"Share of her Fox headlines about her actual play: points, rebounds, assists, records."
		}
	];
	// the table under the chart filters to the tab's measure (tone has no filter)
	const FRAME_OF = {
		tone: "all",
		political: "political",
		appearance: "appearance",
		celebrity: "celebrity",
		performance: "performance"
	};

	// the player clicked on the chart; the table beneath shows only her headlines
	let picked = $state(null);
	// faces the same size, or sized by how many headlines name her
	let sizing = $state("count");
	// measured over Fox's headlines, or over every Fox sentence naming her
	let basis = $state("sentences");
	let view = $state(
		words[0] && VIEWS.some((v) => v.key === words[0]) ? words[0] : "tone"
	);
	let current = $derived(VIEWS.find((v) => v.key === view));
</script>

<div class="framing-tabs">
	<!-- the picker, as on the player-words chart: who, and which measure -->
	<!-- only the player and the measure: the chart is by sentence, sized by
	     sentences, as a swarm -->
	<FramingControls
		players={PLAYERS}
		views={VIEWS}
		bind:picked
		bind:view
		bind:basis
		bind:layout
		bind:sizing
		showBasis={false}
		showLayout={false}
		showSizing={false}
	/>
	<p class="blurb">
		{basis === "sentences" ? current.blurb.replace("headline", "sentence").replace("headlines", "sentences") : current.blurb}
	</p>

	<div bind:this={chartEl}>
		<FacesBeeswarm
			metric={view}
			{sizing}
			{basis}
			{layout}
			selected={picked}
			onselect={(name) => (picked = name)}
		/>
	</div>
	<p class="pick-note">
		{#if picked}
			Showing headlines naming <b>{picked}</b>.
			<button class="clear" onclick={() => (picked = null)}
				>show everyone</button
			>
		{:else}
			Click a face to see only her headlines.
		{/if}
	</p>
	<HeadlineTable
		embedded
		frame={FRAME_OF[view]}
		players={picked ? [picked] : []}
	/>
</div>

<style>
	.framing-tabs {
		max-width: 920px;
		margin: 0 auto;
	}
	.blurb {
		text-align: center;
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.65);
		margin: 0 0 14px;
	}
	.pick-note {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.65);
		text-align: center;
		margin: 6px 0 0;
	}
	.pick-note .clear {
		font: inherit;
		border: 1px solid rgba(42, 21, 3, 0.3);
		background: transparent;
		color: rgba(42, 21, 3, 0.7);
		border-radius: 4px;
		padding: 1px 8px;
		margin-left: 6px;
		cursor: pointer;
	}
</style>
