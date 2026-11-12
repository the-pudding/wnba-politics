#!/bin/bash
# Puts clips in the one format every browser plays smoothly, phones included, with
# every clip's sound at the same loudness. Each clip comes out as
# static/video/<name>.mp4, named after the file you give it.
# Run on a new or re-cut clip:  bash tasks/clip-video.sh path/to/clip.mp4 ...
# Re-level the sound of clips already in static/video, picture left as it is:
#   bash tasks/clip-video.sh --sound-only static/video/*.mp4
# (set FFMPEG=/path/to/ffmpeg if ffmpeg isn't on your PATH)

# ---- settings ----
MAX_W=1280 # largest size; smaller clips keep their size
MAX_H=720
FPS=30
CRF=24 # picture quality: lower is sharper and bigger
KEYFRAME=$((FPS * 2)) # a keyframe every 2 seconds, so a clip can jump to any spot quickly
AUDIO_RATE=44100
AUDIO_BITRATE=128k
LOUDNESS=-20 # how loud every clip plays, in LUFS (the announcer's call is about -20)
PEAK=-1.5 # the loudest any moment may get, in dBTP
# ------------------

cd "$(dirname "$0")/.."
FFMPEG=${FFMPEG:-ffmpeg}
SOUND_ONLY=false
if [ "$1" = "--sound-only" ]; then
	SOUND_ONLY=true
	shift
fi

# a clip's loudness, measured first, so the leveling is one even change of volume
# (empty for a clip with no sound)
measure() {
	"$FFMPEG" -nostdin -hide_banner -i "$1" -af "loudnorm=I=$LOUDNESS:TP=$PEAK:LRA=20:print_format=json" -f null - 2>&1 |
		grep -E '"(input_i|input_tp|input_lra|input_thresh|target_offset)"' | tr -d ' \t",'
}

for clip in "$@"; do
	name=$(basename "$clip" .mp4)
	out=static/video/$name.mp4
	tmp=$(mktemp -t "$name").mp4

	m=$(measure "$clip")
	if [ -n "$m" ]; then
		val() { echo "$m" | grep "^$1:" | cut -d: -f2; }
		level="loudnorm=I=$LOUDNESS:TP=$PEAK:LRA=20:measured_I=$(val input_i):measured_TP=$(val input_tp)"
		level="$level:measured_LRA=$(val input_lra):measured_thresh=$(val input_thresh):offset=$(val target_offset):linear=true"
		sound=(-af "$level" -c:a aac -ar $AUDIO_RATE -ac 2 -b:a $AUDIO_BITRATE)
	else
		sound=(-an)
	fi

	if $SOUND_ONLY; then
		picture=(-c:v copy)
	else
		# H.264 High at level 4.0 with 4:2:0 colour: iPhones refuse higher levels and 4:4:4
		picture=(-vf "fps=$FPS,scale='min($MAX_W,iw)':'min($MAX_H,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2"
			-c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p -crf $CRF -g $KEYFRAME)
	fi

	"$FFMPEG" -nostdin -v error -y -i "$clip" "${picture[@]}" "${sound[@]}" \
		-movflags +faststart "$tmp" && mv "$tmp" "$out" && echo "$name"
done
