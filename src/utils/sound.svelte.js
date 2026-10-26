// The story's sound. Every clip on the walls is a muted video, always; all sound
// comes from one audio player, so only one thing is ever heard and a clip can't be
// heard by accident. A phone lets the player play once a tap has started it, so the
// sound switches start it (toggleSound), and from then on each clip's soundtrack
// (static/audio/clips/<clip>.m4a, made by tasks/clip-audio.sh) is swapped in and
// kept in step with its video.
import { base } from "$app/paths";

// `on`: the reader has turned sound on (one switch for the whole page). `playable`:
// per wall, whether a clip with sound is on screen right now (the corner switch
// only shows while one is). `blocked`: the phone refused to play, so the switches
// ask for a tap ("Tap for sound"). `call`: a sound to play as sound comes on, set
// while the title page is up (the announcer's call).
export const sound = $state({ on: false, playable: {}, blocked: false, call: null });

const DRIFT = 0.3; // seconds the sound may stray from its picture before it's put back
const SETTLE = 1000; // ms to leave the sound alone after it's started or put back
const SILENCE = `${base}/audio/silence.wav`;
const clipSrc = (name) => `${base}/audio/clips/${name}.m4a`;

let player = null;
let heard = null; // { src, video }: the clip being heard, and its picture
let movedAt = 0; // when the sound was last started or put back
let fixes = 0; // how many times it's been put back, for the ?checks readout
const getPlayer = () => (player ??= new Audio());

// Sounds fetched ahead (preloadSound), so they play the moment they're asked for
const ready = new Map();
export function preloadSound(src) {
	if (ready.has(src)) return;
	ready.set(src, null);
	fetch(src)
		.then((response) => (response.ok ? response.blob() : null))
		.then((blob) => blob && ready.set(src, URL.createObjectURL(blob)))
		.catch(() => {});
}

function playSrc(src, at = 0) {
	const p = getPlayer();
	if (p.dataset.src !== src) {
		p.dataset.src = src;
		p.src = ready.get(src) ?? src;
	}
	p.currentTime = at;
	movedAt = performance.now();
	p.play()
		.then(() => (sound.blocked = false))
		.catch((error) => {
			if (error.name === "NotAllowedError") sound.blocked = true;
		});
}

// The clips' muted videos, so the tap can start them too: some phones (an iPhone in
// Low Power Mode) don't autoplay even muted video, but play what a tap started
const videos = new Set();
const wanted = new Set();
export const wallVideos = {
	add: (video) => videos.add(video),
	remove(video) {
		videos.delete(video);
		wanted.delete(video);
	},
	// should this video be playing now
	want: (video, on) => (on ? wanted.add(video) : wanted.delete(video))
};

export const clipSound = {
	// fetch a clip's soundtrack ahead of its turn
	preload: (name) => preloadSound(clipSrc(name)),
	// a clip's turn to be heard: its soundtrack, in step with its video
	play(name, video) {
		heard = { src: clipSrc(name), video };
		if (sound.on) playSrc(heard.src, video.currentTime);
	},
	// its turn is over (only if it's still the one being heard)
	stop(video) {
		if (heard?.video !== video) return;
		heard = null;
		player?.pause();
	},
	// what the player is doing, for the ?checks readout (SoundCorner)
	status() {
		const name = (src) => src?.split("/").pop() ?? "none";
		return {
			on: sound.on,
			blocked: sound.blocked,
			loaded: name(player?.dataset.src),
			playing: !!player && !player.paused,
			time: player ? player.currentTime.toFixed(1) : "-",
			clip: name(heard?.src),
			clipTime: heard ? heard.video.currentTime.toFixed(1) : "-",
			fixes,
			// each video that should be playing: time, paused (p) or not, how much is
			// loaded (readyState 0-4), and any error code
			videos: [...wanted]
				.map(
					(v) =>
						`${name(v.getAttribute("src")).replace(".mp4", "")} ${v.currentTime.toFixed(1)}${v.paused ? " p" : ""} r${v.readyState}${v.error ? " e" + v.error.code : ""}`
				)
				.join("; ")
		};
	},
	// from the video's timeupdate: put the sound back in step if it has strayed,
	// and start it again when the video loops round. Not while either is still
	// seeking, or just after a start: putting it back again and again stutters.
	sync(video) {
		if (!sound.on || sound.blocked || heard?.video !== video || !player) return;
		if (player.paused) return playSrc(heard.src, video.currentTime);
		if (video.seeking || player.seeking || performance.now() - movedAt < SETTLE)
			return;
		if (Math.abs(player.currentTime - video.currentTime) > DRIFT) {
			player.currentTime = video.currentTime;
			movedAt = performance.now();
			fixes += 1;
		}
	}
};

// The sound switches (the title page's, each step card's, the corner's), from the
// tap itself. `call`: the announcer's call to play as sound comes on (title page).
// A tap while the phone is asking for one ("Tap for sound") turns sound on, not off.
export function toggleSound(call = null) {
	if (sound.blocked || !sound.on) {
		sound.on = true;
		// start the player inside the tap: the clip that's up (joining it wherever
		// it's got to), the call, or silence
		if (heard) playSrc(heard.src, heard.video.currentTime);
		else playSrc(call ?? SILENCE);
		for (const video of videos) {
			if (wanted.has(video)) video.play().catch(() => {});
			else
				video
					.play()
					.then(() => !wanted.has(video) && video.pause())
					.catch(() => {});
		}
	} else {
		sound.on = false;
		player?.pause();
	}
}
