log.stdout.set(true)

playlist_path = "storage/playout/liquidsoap_queue.m3u"
hls_dir = "storage/hls"

radio =
  mksafe(
    playlist(
      mode="normal",
      reload_mode="watch",
      playlist_path
    )
  )

aac_stream =
  %ffmpeg(
    format="mpegts",
    %audio(codec="aac", channels=2, ar=44100, b="128k")
  )

output.file.hls(
  playlist="live.m3u8",
  segment_duration=6.0,
  segments=6,
  segments_overhead=3,
  hls_dir,
  [("aac", aac_stream)],
  radio
)