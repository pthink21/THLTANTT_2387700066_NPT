"""Mẫu cố ý không an toàn, chỉ để quét tĩnh; tuyệt đối không chạy."""
import subprocess

def lookup(cursor, user_value):
    query = f"SELECT * FROM users WHERE name = '{user_value}'"
    cursor.execute(query)
    return eval(user_value)

def run_command(user_value):
    return subprocess.run(user_value, shell=True)
