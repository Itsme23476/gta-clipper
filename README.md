# GTA Clipper

A free Claude Code skill that turns a finished GTA 6 stream into vertical Shorts: the streamer's facecam on top, the gameplay below, captions in between, and zooms on the big moments. It picks the best moments, shows you a ranked list, and only cuts what you approve.

Give it a Twitch VOD or clip, a Kick VOD, a YouTube link or a video file. For a link it downloads only the audio to find the moments, then only the video each approved clip needs, so a 14-hour stream doesn't fill your disk.

Everything runs on your own computer except picking the moments, which uses your Claude plan.

## What you need

- A Mac. Face detection and captions use frameworks built into macOS.
- Claude Code, which needs a paid Claude plan.
- FFmpeg and whisper.cpp: `brew install ffmpeg whisper-cpp`
- Swift, from the Xcode Command Line Tools: `xcode-select --install`
- A Whisper model, about 150 MB. The skill offers to download one if you don't have it.
- yt-dlp, for Twitch, Kick and YouTube links: `brew install yt-dlp`

## Install

Paste this repo's link into Claude Code and say: "Install this skill and set it up for me."

Or do it by hand:

```bash
git clone https://github.com/Itsme23476/gta-clipper ~/.claude/skills/gta-clipper
```

The skill must live in `~/.claude/skills/gta-clipper`. Restart Claude Code after installing. It's separate from [Claude Clipper](https://github.com/Itsme23476/claude-clipper), so you can have both.

## Use

In Claude Code, type `/gta-clipper` and paste a finished stream's link, such as `https://www.twitch.tv/videos/<id>`. You get a ranked list of moments with a score, start time and opening line for each, and it asks which style you want. Tell it which clips to keep, and it renders them to `~/Desktop/Clips/<stream name>/clips/`, with titles and post captions in `post-copy.md`.

To change anything, just ask: a bigger facecam, no zooms on one clip, a shorter cut.

## Layout

- **Stream with a facecam in a corner:** the facecam on top, taking 40% of the height, and the gameplay below with 60%. Captions sit on the seam, and the gameplay zooms in on the big moments.
- **Just Chatting or a talking head:** a crop that follows the face.
- **No facecam:** the full frame, with bars above and below.

## Styles

- **Hormozi** (default): bold white captions build word by word, punch words land in giant capitals and key words in red script.
- **Elegant**: lower-case captions that build word by word in stepped lines, with key words in gold serif.
- **Classic**: bold outlined capitals with yellow highlight words.
- **Podcast**: small white subtitles that jump up in size on key words.

Each style is a small file in `styles/`. Show it a Short whose captions you like and ask it to learn that style, and it saves a new one there that you can pick next time.

## Limits

- Mac only for now.
- Finished streams only, not live ones.
- It picks moments from what's said, not what's on screen, so a moment that only looks good won't be found.
- Subscriber-only VODs need your Twitch login. Download those yourself and give it the file.
- Long streams take a while to download and transcribe.
- It's set up for English. Whisper mishears names, so read the captions and tell it what to fix.

Only clip videos you own or have permission to use, such as a streamer's clipping campaign. Read each campaign's rules before posting: some don't accept AI-edited clips.

## License

MIT
