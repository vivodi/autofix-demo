import os
import re
import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).parents[1] / 'tests'
CASSETTES_DIR = Path(__file__).parents[1] / 'tests' / 'cassettes'


def get_online_tests():
    result = subprocess.run(
        ['uv', 'run', 'pytest', str(TESTS_DIR), '--collect-only', '-q', '-m', 'online'],
        capture_output=True,
        text=True,
        check=True,
    )
    tests = set()
    for line in result.stdout.splitlines():
        parts = line.split('::', 1)
        if len(parts) == 2:

            def replacer(match):
                if match.group(1):
                    return '.'
                if match.group(2):
                    return ''
                raise NotImplementedError

            tests.add(f'{Path(parts[0]).stem}.{re.sub(r"(::)|(\[.*?\])", replacer, parts[1])}.yml')
    return tests


def cleanup_cassettes(cassette_dir: Path, used_tests: set):
    uncleanable_cassettes = set()
    for cassette in cassette_dir.iterdir():
        cassette_name = cassette.name
        if cassette_name not in used_tests:
            if new_cassettes := os.environ.get('NEW_CASSETTES'):
                new_cassettes_list = [Path(path).name for path in new_cassettes.splitlines()]
                if cassette_name in new_cassettes_list:
                    uncleanable_cassettes.add(cassette_name)
                    continue
            print(f'Deleting unused cassette: {cassette_name}')
            cassette.unlink()
    if uncleanable_cassettes:
        print(
            "The newly added cassettes include unnecessary files. To avoid unnecessary repository bloat, we won't remove them via a new commit. Please clean them up in the existing commits and force-push:"
        )
        for cassette_name in uncleanable_cassettes:
            print(cassette_name)
        raise RuntimeError('Newly added cassettes include unnecessary files')


if __name__ == '__main__':
    used_tests = get_online_tests()
    cleanup_cassettes(CASSETTES_DIR, used_tests)
