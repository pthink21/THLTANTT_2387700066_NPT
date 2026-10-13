import argparse
import json
from pathlib import Path
import secrets
from api_gateway.gateway import APIGateway
from token_manager.manager import TokenManager


def build(port=5000):
    runtime = Path(__file__).resolve().parents[1] / 'runtime'
    runtime.mkdir(exist_ok=True)
    key_file = runtime / 'jwt-key.txt'
    if not key_file.exists():
        key_file.write_text(secrets.token_urlsafe(48), encoding='utf-8')
    manager = TokenManager(key_file.read_text(encoding='utf-8').strip(), db_path=str(runtime / 'tokens.sqlite'))
    access, refresh = manager.generate_tokens('2387700066')
    (runtime / 'tokens.json').write_text(json.dumps({'access_token': access, 'refresh_token': refresh}), encoding='utf-8')
    # The curl config keeps actual tokens out of committed screenshots/transcripts.
    (runtime / 'access.curl').write_text(f'header = "Authorization: Bearer {access}"\n', encoding='utf-8')
    print(f'JWT Gateway: http://127.0.0.1:{port}/protected', flush=True)
    print('Access/Refresh Token saved locally: runtime/tokens.json (excluded from Git)', flush=True)
    return APIGateway(manager.secret, manager=manager, audit_path=runtime / 'gateway-audit.jsonl')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    build(args.port).run(args.port)
