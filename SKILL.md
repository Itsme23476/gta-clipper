---
name: gta-clipper
description: Turns a finished GTA 6 stream (a Twitch or Kick VOD, a Twitch clip, a YouTube link or a file) that the user has permission to clip into vertical Shorts, with the facecam on top, the gameplay below, captions and zooms. It picks the best moments, shows a ranked list for approval, then cuts them. Use when the user runs /gta-clipper or asks to clip a GTA or gaming stream.
---

# GTA Clipper

Everything runs on this computer except picking the moments, which is your own reading of the transcript.

## Rules

- Only clip streams the user owns or has permission to use, such as a streamer's clipping campaign. If it looks like someone else's stream, ask first.
- Never cut anything until the user approves the ranked list.
- Ask before installing or downloading anything.

## Steps

**1. Prepare.** Run this with the stream link or video file:

```bash
python3 ~/.claude/skills/gta-clipper/clipper.py prep "<LINK OR VIDEO>"
```

It takes a Twitch VOD (`twitch.tv/videos/<id>`), a Twitch clip, a Kick VOD (`kick.com/<channel>/videos/<id>`), a YouTube link or a file. For a link it downloads only the audio now, and each approved clip's video when it renders, so a 14-hour stream never fills the disk. A long stream takes a while to download and transcribe, so run it in the background and tell the user.

If it says the stream is still live, tell the user to come back once it has ended. If yt-dlp says the VOD is for subscribers only, it needs the user's Twitch login: they can download the VOD themselves and give you the file.

If it says no Whisper model was found, search for an existing `ggml-*.bin` file and pass it as `WHISPER_MODEL=<path>`. Only offer to download one if none exists. It is about 150 MB: `mkdir -p ~/.cache/whisper && curl -L -o ~/.cache/whisper/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin`. Add `--out <folder>` to choose where it works. The default is `~/Desktop/Clips/<stream title>-<id>/`. Running it again on the same link reuses what it already downloaded.

**2. Pick the moments.** Read all of `transcript.txt`. Each line starts with its time in seconds, and a `-` or `>>` marks a new speaker. A stream transcript is long, so read it in parts with the Read tool's offset and limit, and keep a shortlist as you go. Choose the best moments, 20 to 60 seconds each unless the user says otherwise:

- The moments a viewer would clip: big reactions, chases, crashes, funny fails, run-ins with NPCs or the police, and wins. Skip dead air, menus, loading screens, reading chat, and ad or sponsor reads.
- It makes sense to someone who never saw the stream, with no missing context.
- It starts on a strong first line, never in the middle of a thought.
- It ends on a payoff, not trailing off.
- Start and end on sentence boundaries from the transcript.

You only have what was said, so a moment that only looks good on screen won't show up. Score each out of 10, and be strict. A long stream might have ten good moments, not fifty.

**3. Show the ranked list, ask for a style, and stop.** A table with rank, score, start time, length, title, and the opening line. In the same message, ask which style to use. Each file in `~/.claude/skills/gta-clipper/styles/` is one style:

- `hormozi` (the default): bold white captions, punch words in giant capitals and key words in red script, and a title box for the first two seconds.
- `elegant`: lower-case captions that build word by word in stepped lines, key words in gold serif, and a title box for the first two seconds.
- `classic`: bold outlined capitals with yellow highlight words.
- `podcast`: small white subtitles that build word by word, and any caption holding a key word jumps up in size, with punch words in heavy capitals and emphasis words in a bold serif. A black title box with a red word for the first two seconds. Its accent colours are red `#E44848`, gold `#F0C048` and blue `#82C8FA`.
- Any other file there is a style the user taught it. Describe it from its keys.

Wait for the user's OK on both. They may drop or change some clips.

**4. Save the picks** to `picks.json` in the same folder, with the chosen style as `preset`:

```json
{"preset": "hormozi",
 "fix": {"Leo Nida": "Leonida"},
 "clips": [{"rank": 1, "score": 9, "title": "Short title", "caption": "Post caption with hashtags",
            "start": 123.4, "end": 171.2, "highlights": ["cops", "crashed"], "hook": "HE DID NOT SEE *THAT* COMING...",
            "emphasis": ["no way", "get out", {"wasted": "#F0484E"}]}]}
```

`highlights` is one to four words or short phrases spoken in that clip, at its biggest moments. Each one zooms into the gameplay. In `hormozi` they are also the punch words in giant capitals, so prefer one-word payoffs, and don't pick a word that is said many times.

`emphasis` is the key word or short phrase in most sentences, about one per caption. Each one gets the accent colour and font, without a zoom: red script in `hormozi`, gold serif in `elegant`, a big white serif in `podcast`. Write `{"word": "#hex"}` to give a word its own colour. Phrases match only as a whole, so "get out of here" never colours every "of".

`hook` is a teaser of up to six words in capitals, shown in a box for the first two seconds, such as `HE CRASHED *ON PURPOSE*...`. Make it a cliffhanger, not a summary, and wrap the word to colour in `*asterisks*`.

Whisper mishears names, GTA 6 ones included: Leonida, Vice City, Lucia, Jason, and the streamer's own name. Read for that and add a top-level `"fix"`. Put it on a single clip instead if a word is only wrong there.

**5. Render:**

```bash
python3 ~/.claude/skills/gta-clipper/clipper.py render "<FOLDER>"
```

For a link, the first render of each clip downloads just that clip's video. Clips land in `<FOLDER>/clips/`, with titles and captions in `post-copy.md`. Open at least one clip's frames to check the result before saying it's done.

## Changes

Edit `picks.json` and re-render only what changed with `--only 2`. For one clip, set `"zoom": false`, change `start` or `end`, or add `"style": {"highlight": "#00AAFF"}`. To change the whole batch, switch `preset` or add a top-level `"style"` with the keys to change.

The layout is chosen for you: `split` puts the streamer's facecam on top and the gameplay below, with the captions on the seam, for a stream with a facecam in a corner. `crop` follows a talking head, such as a Just Chatting stream, and `fit` is for gameplay with no facecam. Set `"layout"` on a clip to override it.

Split keys: `face_height` is the facecam's share of the height (0.4, so the gameplay gets 60%). `cam_size` scales the facecam crop (1.4): lower it if chat or gameplay shows around the cam, raise it if the cam is cut off.

Style keys: `font`, `size`, `color`, `highlight`, `stroke`, `stroke_width` (0 for no outline), `shadow` (blur in pixels, 0 for none), `y` (caption height, 0 to 1, except in `split`, where captions sit on the seam), `max_words` (words per caption), `upper`, `zoom`, `wide_zoom` (punch-in on wide shots in `crop`, 1 to turn it off).
- Key words: `highlight_font` and `highlight_scale` set highlights in a second font, larger, and `highlight_upper` puts them in capitals. `emphasis_font`, `emphasis_scale` and `emphasis_color` do the same for emphasis words, and default to the highlight ones.
- Layout: `line_words` breaks a caption into lines of that many words, and a key word gets its own line. `stagger` steps each line right by that many pixels. `reveal: true` shows each word as it is spoken. `frame: "square"` puts a 1:1 picture between black bars, for the crop layout. `kinetic` (such as 1.35) draws any caption holding a key word that many times bigger, so plain lines stay subtitle-sized.
- Hook: `hook_font`, `hook_highlight` (the starred word), `hook_box` (box colour).

Fonts are macOS font names such as `HelveticaNeue-Medium`, `Didot-Bold` or `AvenirNext-Heavy`.

## Teach it a style

When the user shows a Short they like, look at several frames of it and write the closest matching keys to `~/.claude/skills/gta-clipper/styles/<name>.json`, with a short name the user picks. From then on it is one of the styles offered in step 3. Start from the existing style closest to it and change only what differs. Check for an outline or a shadow, capitals or lower case, words appearing one at a time, stepped lines, one or two accent fonts for key words, and a title box at the start. Copy the caption style only, never the video.
