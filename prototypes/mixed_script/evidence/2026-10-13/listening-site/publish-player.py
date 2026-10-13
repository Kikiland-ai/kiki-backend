"""Package this static player; receive the short-lived Site credential on stdin."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import termios

ROOT = Path('/workspace/sites/kiki-vco-listening-draft')
if sys.stdin.isatty():
    flags = termios.tcgetattr(sys.stdin.fileno())
    flags[3] &= ~termios.ECHO
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, flags)
print('Ready for Site credential JSON on stdin (input is hidden).', flush=True)
credential = json.loads(sys.stdin.readline())
assert credential['auth_mode'] == 'http_extra_header'
remote = credential['remote_url']
assert remote.startswith('https://') and '@' not in remote
branch = credential['branch']
assert branch and not branch.startswith('-')
token = credential['token']
env = os.environ.copy()
env.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.extraHeader',
           GIT_CONFIG_VALUE_0='Authorization: Bearer ' + token,
           GIT_TERMINAL_PROMPT='0')

def git(*args, cwd=None):
    result = subprocess.run(['git', *args], cwd=cwd or ROOT, env=env,
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        message = result.stderr.replace(token, '[redacted]')
        print(json.dumps({'status': 'failed', 'operation': args[0],
                          'returncode': result.returncode, 'message': message[:1600]}), flush=True)
        raise SystemExit(1)
    return result.stdout.strip()

checkout = ROOT / 'checkout'
if not (checkout / '.git').exists():
    assert not checkout.exists(), 'Preserve unexpected existing checkout.'
    git('clone', remote, str(checkout))
head = subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], cwd=checkout,
                      env=env, capture_output=True, text=True)
if head.returncode:
    git('symbolic-ref', 'HEAD', 'refs/heads/' + branch, cwd=checkout)
elif git('branch', '--show-current', cwd=checkout) != branch:
    git('checkout', branch, cwd=checkout)
git('config', 'user.name', 'arpanvihan5-sketch', cwd=checkout)
git('config', 'user.email', '317357476+arpanvihan5-sketch@users.noreply.github.com', cwd=checkout)
(checkout / '.openai').mkdir(exist_ok=True)
shutil.copyfile(ROOT / '.openai/hosting.json', checkout / '.openai/hosting.json')
shutil.copytree(ROOT / 'dist', checkout / 'dist', dirs_exist_ok=True)
assert hashlib.sha256((checkout / 'dist/speech-draft.mp3').read_bytes()).hexdigest() == '4b74cbd6bb25ddf5929e0187e1c1e20de87dab4b35b7326a14cd9824c1c93b54'
git('add', '.openai/hosting.json', 'dist', cwd=checkout)
changes = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=checkout,
                         env=env, capture_output=True, text=True)
if changes.returncode == 1:
    git('commit', '-m', 'Add private VCO listening draft and MP3 download', cwd=checkout)
else:
    assert changes.returncode == 0
commit = git('rev-parse', 'HEAD', cwd=checkout)
git('push', 'origin', 'HEAD:refs/heads/' + branch, cwd=checkout)
remote_head = git('ls-remote', 'origin', 'refs/heads/' + branch, cwd=checkout)
assert remote_head.split()[0] == commit
archive = ROOT / 'work/listening-player.tar'
git('archive', '--format=tar', '-o', str(archive), 'HEAD', '.openai/hosting.json', 'dist', cwd=checkout)
result = {'status': 'pushed_and_packaged', 'project_id': json.loads((checkout / '.openai/hosting.json').read_text())['project_id'],
          'commit_sha': commit, 'archive': str(archive), 'checkout_path': str(checkout),
          'archive_bytes': archive.stat().st_size}
(ROOT / 'work/source-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
