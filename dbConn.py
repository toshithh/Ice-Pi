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


class Interfaces:
    def __init__(self, cursor: sqlite3.Cursor):
        self.cursor = cursor
        self.update_interfaces()

    def update_interfaces(self):
        ips = (
            get_ip("wlan0"),
            get_ip("ap0"),
            get_ip("usb0")
        )
        self.cursor.execute("""
            INSERT INTO interfaces (name, enabled, config) VALUES
                ('wifi', 1, ?),
                ('ap', 2, ?),
                ('ethernet', 2, ?)
            ON CONFLICT(name) DO UPDATE SET
                config = excluded.config;
            """, 
                ips
        )

    def __getitem__(self, key: str) -> dict:
        return dict(self.cursor.execute("SELECT * FROM interfaces where name=?", (key,)).fetchone())


    def __setitem__(self, interface: str, value: int) -> bool:
        try:
            self.cursor.execute("UPDATE interfaces set enabled=? where name = ?", (value, interface))
            return True
        except Exception as err:
            print(err)
            return False




class DB:
    def __init__(self):
        self.CONN = sqlite3.connect("/var/local/IcePi/icepi.db")
        self.CONN.row_factory = sqlite3.Row
        self.cursor = self.CONN.cursor()
        self.cursor.execute("Create TABLE IF NOT EXISTS interfaces(name VARCHAR(50) PRIMARY KEY, enabled INT, config VARCHAR(16) )")
        self.cursor.execute("INSERT OR IGNORE INTO interfaces(name, enabled, config) values('storage', 0, '8gb'), ('hid', 1, '')")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings(key varchar(255) PRIMARY KEY, value TEXT)")
        self.Interfaces = Interfaces(self.cursor)
    
    



if __name__ == "__main__":
    db = DB()
    print(*(x for x in db.cursor.execute("SELECT name FROM sqlite_schema where type='table'").fetchall()))