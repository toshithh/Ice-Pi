# 🧊 Ice Pi  
**A mobile GNU/Linux network security & privacy platform**

<center>
  <img src="assets/rpi.png">
</center>

Ice Pi is a **GNU GPL–licensed**, mobile-controlled **Linux network security device** designed to help users **protect their devices and traffic on untrusted networks**.

It is built for people who want **full visibility and control over their network traffic**, whether operating in public environments or managing their own isolated networks.

Ice Pi turns a **Raspberry Pi Zero** into:
- **A hardened personal network gateway for untrusted environments**
- **A configurable network security and analysis platform**

No cloud. No lock-in. No hidden telemetry.

* The image is an AI-generated illustration.

---

## ⚠️ Legal & Ethical Use

Ice Pi is intended for:
- Network hardening and privacy protection  
- Personal device security on untrusted networks  
- Defensive network analysis 
- To convert phone into a Keyboard for PC  
- Security education and research  

You are responsible for complying with local laws and regulations.  
Do not interfere with networks or devices you do not own or have permission to manage.

---

## 🛡️ Network Safety & Privacy

Ice Pi is designed to act as a **trusted intermediary** between user devices and external networks.

It allows users to:

- Route all connected device traffic through:
  - Secure VPN gateways
  - Optional Tor routing for anonymity and censorship resistance
- Create isolated, hardened Wi-Fi networks
- Act as a secure gateway on public Wi-Fi
- Protect laptops, tablets, and phones from hostile or compromised networks
- Enforce strict DNS policies to reduce spoofing risks
- Block ads, trackers, and known malicious domains at the network level
- Inspect and control traffic before it reaches user devices
- Use USB-Ethernet as a secure wired gateway
- Act as a Keyboard that can be controlled via smartphone  

You don’t connect directly to unknown networks.  
You **bring your own controlled network**.

---

## 🔍 Network Analysis & Advanced Configuration

Ice Pi runs on a **full GNU/Linux environment**, allowing advanced users to:

- Inspect traffic flows for misconfiguration or exposure
- Analyze DNS and routing behavior
- Validate encryption and transport security
- Apply custom firewall and routing rules
- Perform defensive testing on user-owned networks

All configuration is local, transparent, and user-controlled.

---

## 🔄 One Device, One Control Surface

Ice Pi is built on the principle that **visibility, control, and isolation** are foundational to network security.

- Centralized traffic control  
- Explicit routing decisions  
- Auditable configuration  
- No background services  

Everything runs locally.  
Everything can be inspected.

---

## 🆚 Comparison

| Feature | **Ice Pi** | Hak5 Devices | P4wnP1 |
|------|-------|--------|--------|
| GNU GPL Licensed | ✅ | ❌ | ❌ |
| Fully Open Source | ✅ | ❌ | ✅ |
| Mobile App Control | ✅ | ⚠️ Limited | ❌ |
| Full GNU/Linux Environment | ✅ | ❌ | ⚠️ Partial |
| Network Gateway Mode | ✅ | ❌ | ⚠️ |
| VPN Routing | ✅ | ❌ | ❌ |
| Tor Routing | ✅ | ❌ | ❌ |
| Safe Public Wi-Fi Gateway | ✅ | ❌ | ❌ |
| No Vendor Lock-in | ✅ | ❌ | ✅ |

---

## ⚙️ Installation

On a fresh installation of Kali Linux on Raspberry Pi,

- To resolve dependencies:
  ```bash
  sudo apt-get install -y net-tools openvpn
  sudo apt-get install -y python3 python3-pip python3-venv
  sudo apt-get install -y hostapd dnsmasq
  sudo apt-get -y install tor
  ```
  OR 
  download the `dependencies.sh` file and
  ```bash
  chmod +x dependencies.sh
  ./dependencies.sh
  ```
- To install
  ```bash
  wget https://github.com/toshithh/Ice-Pi/releases/download/IcePi/IcePi.deb
  
  sudo apt install ./IcePi.deb
  ```

The installer:
- Prepares the GNU/Linux environment
- Configures networking and isolation
- Sets up routing, DNS, and gateway services
- Prepares the device for mobile management

**Default credentials (change after install):**
- SSID: `IcePi`
- WPA Passphrase: `T05h1thS1c3`
- Connection password: `T05h1th`

* A reboot may be required.

---

## 📱 AnyKBoard — Mobile App

Ice Pi is managed using the **AnyKBoard** mobile application.

<center><img src="assets/akb.png" width="200"></center>

The app allows users to:
- Securely connect to their Ice Pi device
- Enable or disable networking features
- Manage VPN and Tor routing
- Monitor connected devices
- Apply security policies in real time

Ice Pi is designed to be fully usable **without a laptop**.

The app is currently in **beta testing**.  
Early users can request access via Discord or wait for public availability.

---

## 🔐 Freedom by Design

- GNU GPL licensed  
- No telemetry  
- No forced updates  
- No cloud dependencies  
- No hidden firmware  
- User controls every packet  

---

## 📜 License

Ice Pi is licensed under the **GNU General Public License v3.0 or later**.

---

## ⚖️ Disclaimer

This project is provided **as-is**, without warranty.  
The authors are not responsible for misuse or illegal activity.
