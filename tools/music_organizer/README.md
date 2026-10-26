# Music Organizer

A standalone CLI tool that scans a directory of audio files and organises them into a clean folder hierarchy:

```
<output>/
└── Artist/
    └── Album/
        └── 01 - Title.mp3
```

## How it resolves metadata

For each file the tool tries, in order:

| Step | Method | Requires |
|------|--------|----------|
| 1 | **Embedded tags** (ID3, FLAC, Vorbis, MP4 …) | `mutagen` |
| 2 | **AcoustID audio fingerprint** → MusicBrainz | `pyacoustid` + `fpcalc` binary |
| 3 | **MusicBrainz text search** (using hints from tags / filename) | Internet |
| 4 | **Filename parsing** (`Artist - Title.mp3` etc.) | — |

If a file cannot be categorised it is left exactly where it is.

## Installation

```bash
pip install -r requirements.txt
```

### Optional: AcoustID fingerprinting

1. Download **Chromaprint** (`fpcalc`) from <https://acoustid.org/chromaprint> and put it on your `PATH`.
2. Install the Python binding:
   ```bash
   pip install pyacoustid
   ```

## Usage

```bash
# Preview what would happen (dry run)
python music_organizer.py /path/to/music --dry-run

# Copy into an organised library (default)
python music_organizer.py /path/to/music --output /path/to/library

# Move files instead of copying
python music_organizer.py /path/to/music --mode move

# Skip internet lookup (tags + filename only, faster / offline)
python music_organizer.py /path/to/music --no-online

# Use 8 parallel workers
python music_organizer.py /path/to/music --workers 8
```

## All options

```
positional arguments:
  input                 Directory to scan for audio files

options:
  --output / -o         Destination root  [default: <input>/organized]
  --mode                copy | move  [default: copy]
  --dry-run / -n        Preview only, do not touch files
  --no-online           Skip internet lookup
  --workers / -j        Parallel threads  [default: cpu_count]
  --no-recursive        Do not recurse into sub-directories
  --log-level           DEBUG | INFO | WARNING | ERROR  [default: INFO]
```

## Supported formats

`.mp3` · `.flac` · `.ogg` · `.opus` · `.m4a` · `.aac` · `.wav` · `.wma` · `.ape` · `.wv` · `.mka` · `.aiff` · `.aif`
