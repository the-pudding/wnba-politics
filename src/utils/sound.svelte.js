// The story's sound. Every clip on the walls is a muted video; the clip whose turn it
// is to be heard is unmuted and plays its own sound, so the browser keeps sound and
// picture together. A phone only lets a video make sound once a tap has touched it,
// so the sound switches (toggleSound) touch every clip on the page; from then on
// each one can be unmuted when its turn comes.

// `on`: the reader has turned sound on (one switch for the whole page). `playable`:
// per wall, whether a clip with sound is on screen right now (the corner switch
// only shows while one is). `blocked`: the phone refused to play a clip's sound, so
// the switches ask for a tap ("Tap for sound").
export const sound = $state({ on: false, playable: {}, blocked: false });

let heard = null; // the video whose sound is on
let call = null; // the announcer's call (title page), its own player
let presses = 0; // sound switch presses, for the ?checks readout

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

// a video's sound on: if the phone won't allow it, it plays on muted and the
// switches ask for a tap
function unmute(video) {
	video.muted = false;
	video
		.play()
		.then(() => (sound.blocked = false))
		.catch((error) => {
			if (error.name !== "NotAllowedError") return;
			video.muted = true;
			video.play().catch(() => {});
			sound.blocked = true;
		});
}

// The clips' videos, so the tap can reach them all
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
	// a clip's turn to be heard
	play(name, video) {
		if (heard && heard !== video) heard.muted = true;
		heard = video;
		if (sound.on) unmute(video);
	},
	// its turn is over (only if it's still the one being heard)
	stop(video) {
		if (heard !== video) return;
		video.muted = true;
		heard = null;
	},
	// what the sound is doing, for the ?checks readout (SoundCorner)
	status() {
		const name = (v) =>
			v?.getAttribute("src")?.split("/").pop().replace(".mp4", "") ?? "none";
		return {
			on: sound.on,
			blocked: sound.blocked,
			presses,
			// seconds since the page loaded: a sudden drop means it reloaded
			page: Math.round(performance.now() / 1000),
			clip: name(heard),
			clipTime: heard ? heard.currentTime.toFixed(1) : "-",
			// everything on the page making sound: 1 while a clip is heard, else 0
			heard: [...document.querySelectorAll("video, audio")]
				.filter((m) => !m.muted && !m.paused)
				.map(name)
				.join(", "),
			// each video that should be playing: time, paused (p) or not, muted (m) or
			// not, how much is loaded (readyState 0-4), and any error code
			videos: [...wanted]
				.map(
					(v) =>
						`${name(v)} ${v.currentTime.toFixed(1)}${v.paused ? " p" : ""}${v.muted ? " m" : ""} r${v.readyState}${v.error ? " e" + v.error.code : ""}`
				)
				.join("; ")
		};
	}
};

// The sound switches (the title page's, each step card's, the corner's), from the
// tap itself. `callSrc`: the announcer's call to play as sound comes on (title page).
// A tap while the phone is asking for one ("Tap for sound") turns sound on, not off.
export function toggleSound(callSrc = null) {
	presses += 1;
	if (sound.blocked || !sound.on) {
		sound.on = true;
		// touch every clip inside the tap, so each can be unmuted later on its turn
		// without another one. A phone that won't autoplay even muted video (an
		// iPhone in Low Power Mode) leaves the clips on screen paused: then they're
		// started from the tap as well.
		const stuck = [...wanted].some((video) => video.paused);
		for (const video of videos) {
			if (video === heard) continue;
			video.muted = false;
			video.muted = true;
			if (wanted.has(video)) video.play().catch(() => {});
			else if (stuck)
				video
					.play()
					.then(() => !wanted.has(video) && video.pause())
					.catch(() => {});
		}
		// the clip that's up, joined wherever it's got to, or the call
		if (heard) unmute(heard);
		else if (callSrc) {
			call ??= new Audio();
			call.src = ready.get(callSrc) ?? callSrc;
			call.play().catch(() => {});
		}
	} else {
		sound.on = false;
		if (heard) heard.muted = true;
		call?.pause();
	}
}
