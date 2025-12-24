import sqlite3
import subprocess

def get_ip(iface):
    try:
        out = subprocess.check_output(
            ["ip", "-4", "addr", "show", iface],
            stderr=subprocess.DEVNULL
        ).decode()
        for line in out.splitlines():
            if "inet " in line:
                return line.split()[1].split("/")[0]
    except Exception:
        return ""
    return ""


CONN = sqlite3.connect("icepi.db")
cursor = CONN.cursor()


def update_interfaces():
    ips = (
        get_ip("wlan0"),
        get_ip("ap0"),
        get_ip("usb0")
    )
    cursor.execute("""
        INSERT INTO interfaces (name, enabled, CONFIG) VALUES
            ('wifi', 1, ?),
            ('ap', 1, ?),
            ('ethernet', 1, ?)
        ON CONFLICT(name) DO UPDATE SET
            CONFIG = excluded.CONFIG;
        """, 
            ips
    )
    return ips

cursor.execute("Create TABLE IF NOT EXISTS interfaces(name TEXT PRIMARY KEY, enabled INT, CONFIG VARCHAR(16) )")

cursor.execute("INSERT OR IGNORE INTO interfaces(name, enabled, CONFIG) values('storage', 0, '8gb'), ('hid', 1, '')")
print(cursor.execute("SELECT name FROM sqlite_schema where type='table'").fetchall())
print(cursor.execute("SELECT * FROM interfaces").fetchall())