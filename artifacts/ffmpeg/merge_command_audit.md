# FFmpeg Merge Command Audit

- Timestamp: `2026-04-23T14:36:09`
- ffmpeg path: `C:\Users\SavanthGC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe`
- ffmpeg version: `8.1-essentials_build-www.gyan.dev`

## Merge command (DASH video + audio → single container)

Fast (stream copy):
```
"C:\Users\SavanthGC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe" -loglevel error -stats -y -i "video.mp4" -i "audio.m4a" -c copy "out.mp4"
```

Slow (transcode fallback):
```
"C:\Users\SavanthGC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe" -loglevel error -stats -y -i "video.mp4" -i "audio.m4a" "out.mp4"
```

## HLS process command

Fast:
```
"C:\Users\SavanthGC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe" -loglevel error -stats -y -protocol_whitelist "file,http,https,tcp,tls,crypto" -allowed_extensions ALL -i "local.m3u8" -c copy "file:out.mp4"
```

## Audio convert command

Fast:
```
"C:\Users\SavanthGC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe" -loglevel error -stats -y -i "in.m4a" -acodec copy "out.mp3"
```

## DASH audio extension pairing rules

| Video ext | Audio ext |
| --- | --- |
| `mp4` | `m4a` |
| `webm` | `webm` |
| `mkv` | `mkv` |

These rules live in `firedm/ffmpeg_commands.py :: dash_audio_extension_for`.