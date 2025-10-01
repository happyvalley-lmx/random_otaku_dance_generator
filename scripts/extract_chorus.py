#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
# ensure repo root is on sys.path so imports work when running from ./scripts/
from pathlib import Path as _P
_ROOT = _P(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from chorus_extractor import extract_chorus_intervals


def main():
    p = argparse.ArgumentParser(description='Extract likely chorus interval from an audio file')
    p.add_argument('input', help='input audio file')
    p.add_argument('--k', type=int, default=5, help='number of clusters for kmeans')
    p.add_argument('--min-duration', type=float, default=10.0, help='minimum segment duration in seconds')
    args = p.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f'File not found: {path}')
        sys.exit(2)

    intervals = extract_chorus_intervals(str(path), k=args.k, min_segment_duration=args.min_duration)
    if not intervals:
        print('No chorus intervals detected')
        return

    for i, (t0, t1) in enumerate(intervals):
        print(f'chorus_{i}: {t0:.3f} - {t1:.3f}  duration={t1-t0:.3f}s')


if __name__ == '__main__':
    main()
