#!/bin/bash
# Puts clips in the one format every browser plays smoothly, phones included. Each
# clip comes out as static/video/<name>.mp4, named after the file you give it.
# Run on a new or re-cut clip:  bash tasks/clip-video.sh path/to/clip.mp4 ...
# (set FFMPEG=/path/to/ffmpeg if ffmpeg isn't on your PATH)

# ---- settings ----
MAX_W=1280 # largest size; smaller clips keep their size
MAX_H=720
FPS=30
CRF=24 # picture quality: lower is sharper and bigger
KEYFRAME=$((FPS * 2)) # a keyframe every 2 seconds, so a clip can jump to any spot quickly
AUDIO_RATE=44100
AUDIO_BITRATE=128k
# ------------------

cd "$(dirname "$0")/.."
FFMPEG=${FFMPEG:-ffmpeg}
for clip in "$@"; do
	name=$(basename "$clip" .mp4)
	out=static/video/$name.mp4
	tmp=$(mktemp -t "$name").mp4
	# H.264 High at level 4.0 with 4:2:0 colour: iPhones refuse higher levels and 4:4:4
	"$FFMPEG" -v error -y -i "$clip" \
		-vf "fps=$FPS,scale='min($MAX_W,iw)':'min($MAX_H,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2" \
		-c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p -crf $CRF -g $KEYFRAME \
		-c:a aac -ar $AUDIO_RATE -ac 2 -b:a $AUDIO_BITRATE \
		-movflags +faststart "$tmp" && mv "$tmp" "$out" && echo "$name"
done
