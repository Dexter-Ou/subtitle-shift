# Subtitle Shift

Shift all cues in a UTF-8 SRT subtitle file by an exact millisecond offset. Runs locally with Python 3.10 or later and no dependencies. Preview from Gong LLC.

Extract the package, open a terminal in this directory, then run:

```
python3 subtitle_shift.py example.srt shifted.srt --offset-ms 1250
python3 -m unittest -v
```

Use a negative offset to bring subtitles earlier. Output must be a new path. Exit 0 means the output was written; exit 2 means an error. Overlap warnings do not change the success exit code; overlapping subtitles can be intentional. Play the result against your video before delivery.

Numeric identifiers, ordered cue starts, `HH:MM:SS,mmm --> HH:MM:SS,mmm` timing and at least one text line are required. End must follow start. Negative resulting times and cue positioning/settings are rejected. Input limit: 8 MiB. BOM and CRLF input are accepted; output uses LF without BOM. Cue identifiers and text lines are preserved. This does not correct drift/frame rate, translate text, validate accessibility or inspect the video. No network or upload feature.

Use trusted local directories and keep originals. A disk/write failure can leave a partial new output file: remove it before retrying. Existing output files, including the input itself, are never overwritten. Only Linux/Python execution is tested so far; other environments are untested.
