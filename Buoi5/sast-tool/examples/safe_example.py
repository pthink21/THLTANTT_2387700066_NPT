"""Ví dụ an toàn: truy vấn tham số hóa, không shell, không eval."""
def lookup(cursor, user_value):
    cursor.execute("SELECT * FROM users WHERE name = ?", (user_value,))
    return cursor.fetchone()
