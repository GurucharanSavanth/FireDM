# Windows Manual QA

Use this sheet before publishing a Windows release. Fill pass/fail and blocker fields during a real run.

Log roots:
- installer logs: path passed through `--log`
- app logs: `%LOCALAPPDATA%\FireDM\logs`
- settings: `%APPDATA%\FireDM`

| Test | Steps | Expected result | Pass/Fail | Blocker |
| --- | --- | --- | --- | --- |
| Fresh install | `FireDM_Setup_<version>_<channel>_win_x64.exe --silent --log install.log` | App installs under `%LOCALAPPDATA%\Programs\FireDM`; Start Menu shortcut exists |  |  |
| Desktop shortcut install | Run installer with `--desktop-shortcut` | Desktop shortcut points to `FireDM-Launcher.cmd` |  |  |
| Start Menu launch | Open FireDM from Start Menu | GUI opens without immediate crash |  |  |
| GUI launch | Run installed `FireDM-GUI.exe` | Main window opens; no startup traceback |  |  |
| Direct HTTP download | Add a known safe HTTP test file | Download completes; progress and final file are correct |  |  |
| Pause/resume | Pause and resume the HTTP item | Download resumes or reports unsupported state clearly |  |  |
| Cancel/delete | Cancel a test download and delete item | UI state updates; no unrelated files removed |  |  |
| Restart state restore | Quit and reopen app with queued/completed items | Expected queue/session state is preserved |  |  |
| Video metadata extraction | Add a non-protected public video URL | Metadata and available streams appear |  |  |
| Stream selection | Choose a stream/quality | Selection is retained and queued correctly |  |  |
| yt-dlp handoff | Start public video download | Download handoff succeeds or fails with actionable error |  |  |
| FFmpeg post-processing | With FFmpeg installed, download media needing merge | Merge/post-process succeeds; ffmpeg errors are visible |  |  |
| Bad URL handling | Add invalid URL | UI shows clear failure without crash |  |  |
| Missing FFmpeg | Remove FFmpeg from app-local/PATH/Winget visibility | App shows missing-FFmpeg guidance for FFmpeg-required work |  |  |
| Uninstall | Run `--silent --uninstall --log uninstall.log` | Program files and shortcuts removed; user data preserved |  |  |
| Repair | Delete installed `FireDM-GUI.exe`; run `--repair` | Missing program file restored |  |  |
| Real upgrade | Install previous real installer, then current installer | Program files update; settings and queue data survive |  |  |
| Downgrade block | Install current build, run older installer | Older installer is blocked unless maintainer uses override |  |  |
| Portable ZIP launch | Extract portable ZIP and run `FireDM-GUI.exe` | GUI starts without registry/PATH changes |  |  |
| PATH pollution check | Compare machine/user PATH before and after install | No global PATH entry added by default |  |  |
