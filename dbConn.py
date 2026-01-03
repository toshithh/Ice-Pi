import sqlite3
import subprocess
import logging
import aiohttp
from aiohttp_socks import ProxyConnector
import requests
import threading, asyncio


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

async def get_pub_ip(tor=True):
    try:
        if tor:
            connector = ProxyConnector.from_url("socks5://127.0.0.1:9050")
        else:
            connector = None

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("https://api.ipify.org") as resp:
                return (await resp.text()).replace("'", "").replace("b", '').strip()
    except Exception as err:
        logging.error(f"get_pub_ip\t${err}")
        return ""
    
proxies = {
    "http":  "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}

def sync_get_pub_ip(tor=True):
    try:
        if tor:
            return str(requests.get("https://api.ipify.org", proxies=proxies, timeout=10).content)
        else: return str(requests.get("https://api.ipify.org", timeout=10).content)
    except:
        return ""


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
    def __init__(self, CONN: sqlite3.Connection, cursor: sqlite3.Cursor):
        self.cursor = cursor
        self.CONN = CONN
        self._async_update_wrapper()
    
    def _async_update_wrapper(self):
        threading.Thread(target=self.update_interfaces).start()

    def update_interfaces(self):
        pub_ip = asyncio.run(get_pub_ip())
        ips = (
            get_ip("wlan0"),
            get_ip("ap0"),
            get_ip("usb0"),
            pub_ip
        )
        self.cursor.execute("""
            INSERT INTO interfaces (name, enabled, config) VALUES
                ('wifi', 1, ?),
                ('ap', 2, ?),
                ('ethernet', 2, ?),
                ('tor', 0, ?)
            ON CONFLICT(name) DO UPDATE SET
                config = excluded.config;
            """, 
                ips
        )
        self.CONN.commit()

    def __getitem__(self, key: str) -> dict:
        return dict(self.cursor.execute("SELECT * FROM interfaces where name=?", (key,)).fetchone())


    def __setitem__(self, interface: str, value: int) -> bool:
        try:
            logging.info("DB Interfaces Start")
            self.cursor.execute("UPDATE interfaces set enabled=? where name = ?", (value, interface))
            self.CONN.commit()
            return True
        except Exception as err:
            logging.error(err)
            return False


class Settings:
    def __init__(self, CONN: sqlite3.Connection, cursor: sqlite3.Cursor):
        self.cursor = cursor
        self.CONN = CONN

    def __getitem__(self, key: str) -> dict:
        try:
            row = self.cursor.execute("SELECT value FROM settings where key=?", (key,)).fetchone()
            if row:
                return row[0]
            return ""
        except Exception as err:
            print(err)
            logging.error(f"Settings:__getitem__\t{err}")
    
    def __setitem__(self, key: str, value: int) -> bool:
        try:
            logging.info("DB Settings Start")
            self.cursor.execute("INSERT INTO settings(key, value) values(?, ?) ON CONFLICT(key) DO UPDATE SET  value=excluded.value", (key, value))
            self.CONN.commit()
            return True
        except Exception as err:
            logging.error(err)
            return False
    



class DB:
    def __init__(self):
        self.CONN = sqlite3.connect("/var/local/IcePi/icepi.db", check_same_thread=False)
        self.CONN.execute('PRAGMA journal_mode=WAL')
        self.CONN.row_factory = sqlite3.Row
        self.cursor = self.CONN.cursor()
        self.cursor.execute("Create TABLE IF NOT EXISTS interfaces(name VARCHAR(50) PRIMARY KEY, enabled INT, config VARCHAR(16) )")
        self.CONN.commit()
        self.cursor.execute("INSERT OR IGNORE INTO interfaces(name, enabled, config) values('storage', 0, '8gb'), ('hid', 1, '')")
        self.CONN.commit()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings(key varchar(255) PRIMARY KEY, value TEXT)")
        self.CONN.commit()
        self.cursor.execute("INSERT OR IGNORE INTO settings(key, value) values('DNSBlock','Ads & Trackers')")
        self.CONN.commit()
        self.Settings = Settings(self.CONN, self.cursor)
        self.Interfaces = Interfaces(self.CONN, self.cursor)
    