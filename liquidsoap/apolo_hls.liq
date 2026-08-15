log.stdout.set(true)

playlist_path = "storage/playout/liquidsoap_queue.m3u"
hls_dir = "storage/hls"

playlist_source =
  playlist(
    mode="normal",
    reload_mode="watch",
    playlist_path
  )

def notify_track(m)
  apolo_track_id = m["apolo_track_id"]
  filename = m["filename"]
  initial_uri = m["initial_uri"]
  rid = m["rid"]

  payload_data = {
    apolo_track_id = apolo_track_id,
    filename = filename,
    initial_uri = initial_uri,
    rid = rid
  }

  payload = json.stringify(
    compact=true,
    payload_data
  )

  log.important("Track started: #{payload}")

  response =
    http.post(
      timeout=2.,
      headers=[
        ("Content-Type", "application/json; charset=UTF-8")
      ],
      data=payload,
      "http://host.docker.internal:8000/radio/playback/liquidsoap/track-start"
    )

  log.important(
    "Projeto Apolo callback HTTP status: #{response.status_code}"
  )
end

radio = mksafe(playlist_source)

aac_stream =
  %ffmpeg(
    format="mpegts",
    %audio(
      codec="aac",
      channels=2,
      ar=44100,
      b="128k"
    )
  )

hls_output =
  output.file.hls(
    playlist="live.m3u8",
    segment_duration=6.0,
    segments=6,
    segments_overhead=3,
    hls_dir,
    [("aac", aac_stream)],
    radio
  )

hls_output.on_track(
  synchronous=false,
  notify_track
)
