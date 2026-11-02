"""Shift strict SRT timing locally; standard library only."""
import argparse
import re
import sys
from pathlib import Path

LIMIT = 8 * 1024 * 1024
STAMP = r"(\d{2,}):([0-5]\d):([0-5]\d),(\d{3})"
TIMING = re.compile(STAMP + r" --> " + STAMP)


def milliseconds(parts):
    h, m, s, ms = map(int, parts)
    return ((h * 60 + m) * 60 + s) * 1000 + ms


def timestamp(value):
    seconds, ms = divmod(value, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"


def shift(text, offset):
    text = text.removeprefix('\ufeff').replace('\r\n', '\n')
    if '\r' in text:
        raise ValueError('unsupported line ending')
    blocks = re.split(r'\n[ \t]*\n', text.strip('\n'))
    result, warnings = [], []
    maximum_end = 0
    previous_start = -1
    for position, block in enumerate(blocks, 1):
        lines = block.split('\n')
        if len(lines) < 3 or not re.fullmatch(r'[0-9]+', lines[0]):
            raise ValueError(f'cue {position}: expected numeric identifier, timing and text')
        match = TIMING.fullmatch(lines[1])
        if not match:
            raise ValueError(f'cue {position}: unsupported or malformed timing')
        start = milliseconds(match.groups()[:4])
        end = milliseconds(match.groups()[4:])
        if end <= start:
            raise ValueError(f'cue {position}: end must follow start')
        if start < previous_start:
            raise ValueError(f'cue {position}: cues must be ordered by start time')
        if start + offset < 0:
            raise ValueError(f'cue {position}: offset would create a negative timestamp')
        if position > 1 and start < maximum_end:
            warnings.append(f'cue {position}: overlaps an earlier cue')
        previous_start = start
        maximum_end = max(maximum_end, end)
        lines[1] = f'{timestamp(start + offset)} --> {timestamp(end + offset)}'
        result.append('\n'.join(lines))
    return '\n\n'.join(result) + '\n', warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--offset-ms', required=True, type=int)
    args = parser.parse_args()
    try:
        with args.input.open('rb') as source:
            data = source.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('input exceeds 8 MiB')
        rendered, warnings = shift(data.decode('utf-8'), args.offset_ms)
        # Exclusive creation prevents overwrite even when paths alias.
        with args.output.open('x', encoding='utf-8', newline='\n') as target:
            target.write(rendered)
        for warning in warnings:
            print('warning: ' + warning, file=sys.stderr)
        print(f'wrote shifted subtitles; {len(warnings)} overlap warning(s)')
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        # Do not echo subtitle content or filenames from OS exceptions.
        message = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, UnicodeError) else type(exc).__name__
        print('error: ' + message, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
