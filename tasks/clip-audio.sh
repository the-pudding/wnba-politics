#!/bin/bash
# Each clip's soundtrack as its own small file, for the story's one audio player
# (src/utils/sound.svelte.js): static/video/<clip>.mp4 -> static/audio/clips/<clip>.m4a.
# The sound is copied, not re-encoded, so it stays in step with the video.
# Run after adding or re-cutting a clip:  bash tasks/clip-audio.sh
# (set FFMPEG=/path/to/ffmpeg if ffmpeg isn't on your PATH)
cd "$(dirname "$0")/.."
FFMPEG=${FFMPEG:-ffmpeg}
mkdir -p static/audio/clips
for video in static/video/*.mp4; do
	name=$(basename "$video" .mp4)
	out=static/audio/clips/$name.m4a
	# already made, and newer than its clip
	[ "$out" -nt "$video" ] && continue
	if "$FFMPEG" -v error -y -i "$video" -map 0:a:0 -vn -c:a copy -movflags +faststart "$out" 2>/dev/null; then
		echo "$name"
	else
		rm -f "$out" # a clip without sound
	fi
done
