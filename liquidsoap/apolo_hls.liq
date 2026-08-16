log.stdout.set(true)

hls_dir = "storage/hls"

next_request_url =
  "http://host.docker.internal:8000/radio/playout/next-request"

def get_next_request()
  log.important("Projeto Apolo: requesting next track from backend")

  try
    response =
      http.get(
        timeout=60.,
        headers=[
          ("Accept", "application/json")
        ],
        next_request_url
      )

    if response.status_code != 200 then
      log.important(
        "Projeto Apolo next-request HTTP status: #{response.status_code}"
      )

      []
    else
      let json.parse ({
        available,
        uri
      } : {
        available: bool,
        uri: string?
      }) = response

      if available and null.defined(uri) then
        track_uri = null.get(uri)

        log.important(
          "Projeto Apolo received dynamic URI: #{track_uri}"
        )

        [request.create(track_uri)]
      else
        log.important(
          "Projeto Apolo backend returned no available track"
        )

        []
      end
    end
  catch err do
    log.important(
      "Projeto Apolo next-request error: #{error.message(err)}"
    )

    []
  end
end

dynamic_source =
  request.dynamic.list(
    prefetch=1,
    retry_delay=2.,
    get_next_request
  )

def notify_track(m)
  apolo_track_id = m["apolo_track_id"]

  if apolo_track_id == "" then
    log.important(
      "Projeto Apolo: ignoring track event without apolo_track_id"
    )
  else
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
end

radio = mksafe(dynamic_source)

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