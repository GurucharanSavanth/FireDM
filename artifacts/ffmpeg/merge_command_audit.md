# FFmpeg Merge Command Audit

- Timestamp: `2026-04-23T13:47:39`
- ffmpeg path: `(not located)`
- ffmpeg version: `(unknown)`

## Merge command (DASH video + audio → single container)

Fast (stream copy):
```
"ffmpeg" -loglevel error -stats -y -i "video.mp4" -i "audio.m4a" -c copy "out.mp4"
```

Slow (transcode fallback):
```
"ffmpeg" -loglevel error -stats -y -i "video.mp4" -i "audio.m4a" "out.mp4"
```

## HLS process command

Fast:
```
"ffmpeg" -loglevel error -stats -y -protocol_whitelist "file,http,https,tcp,tls,crypto" -allowed_extensions ALL -i "local.m3u8" -c copy "file:out.mp4"
```

## Audio convert command

Fast:
```
"ffmpeg" -loglevel error -stats -y -i "in.m4a" -acodec copy "out.mp3"
```

## DASH audio extension pairing rules

| Video ext | Audio ext |
| --- | --- |
| `mp4` | `m4a` |
| `webm` | `webm` |
| `mkv` | `mkv` |

These rules live in `firedm/ffmpeg_commands.py :: dash_audio_extension_for`.