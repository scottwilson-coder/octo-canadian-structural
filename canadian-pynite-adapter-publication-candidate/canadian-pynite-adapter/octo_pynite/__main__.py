"""Local JSON analysis and offline reports; no resistance design or upload."""
import argparse
import json
from pathlib import Path
from .adapter import run
from .canonical import from_osm
from .planar import run_beam
from .report import write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text())
    if data.get('schema') == 'octo-planar-beam/1':
        reduced = run_beam(data)
        data, result = reduced['input'], reduced['result']
    else:
        data = from_osm(data) if 'elements' in data else data
        result = run(data)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    write_report(data, result, target.with_suffix('.html'))
    print('Analysis only; member resistance NOT_CHECKED. Output:', target)


if __name__ == '__main__':
    main()
