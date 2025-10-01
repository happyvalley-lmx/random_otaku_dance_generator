#!/usr/bin/env python3
import sys
from pathlib import Path
import csv
import argparse

# ensure repo root on sys.path
from pathlib import Path as _P
_ROOT = _P(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from chorus_extractor import extract_chorus_intervals


def process_all(songs_dir: Path, out_csv: Path, dry_run: bool = False, min_duration: float = 10.0, k:int=5):
    mp3s = sorted([p for p in songs_dir.iterdir() if p.suffix.lower() == '.mp3'])
    with out_csv.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['源文件', '开始时间', '结束时间', '歌曲别名'])
        for p in mp3s:
            alias = p.stem
            if dry_run:
                # write placeholder empty times
                writer.writerow([p.name, '', '', alias])
                print(f'[dry] {p.name} -> (no analysis)')
                continue

            try:
                intervals = extract_chorus_intervals(str(p), k=k, min_segment_duration=min_duration)
            except Exception as e:
                print(f'Error processing {p.name}: {e}')
                intervals = []

            if intervals:
                # write first detected interval
                t0, t1 = intervals[0]
                writer.writerow([p.name, f'{t0:.3f}', f'{t1:.3f}', alias])
                print(f'{p.name} -> {t0:.3f}-{t1:.3f}')
            else:
                writer.writerow([p.name, '', '', alias])
                print(f'{p.name} -> no interval')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--songs-dir', default='songs', help='path to songs directory')
    p.add_argument('--out', default='songs_chorus.csv', help='output csv path')
    p.add_argument('--dry-run', action='store_true', help='only scan files and write placeholders')
    p.add_argument('--min-duration', type=float, default=10.0)
    p.add_argument('--k', type=int, default=5)
    args = p.parse_args()

    songs_dir = Path(args.songs_dir)
    if not songs_dir.exists():
        print('songs directory not found:', songs_dir)
        sys.exit(2)

    out_csv = Path(args.out)
    process_all(songs_dir, out_csv, dry_run=args.dry_run, min_duration=args.min_duration, k=args.k)


if __name__ == '__main__':
    main()
