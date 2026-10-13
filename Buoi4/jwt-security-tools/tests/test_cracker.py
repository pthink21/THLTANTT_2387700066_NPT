import jwt
from jwt_cracker.cracker import JWTCracker


def test_crack(tmp_path):
    candidate = 'lab-word-b'
    path = tmp_path / 'words.txt'
    path.write_text('lab-word-a\nlab-word-b\n', encoding='utf-8')
    token = jwt.encode({'sub':'test'}, candidate, algorithm='HS256')
    assert JWTCracker(token, path).crack() == candidate


def test_limit(tmp_path):
    path = tmp_path / 'words.txt'
    path.write_text('lab-word-a\nlab-word-b\n', encoding='utf-8')
    token = jwt.encode({'sub':'test'}, 'lab-word-b', algorithm='HS256')
    assert JWTCracker(token, path, max_candidates=1).crack() is None
