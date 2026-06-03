![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# ARP Man-in-the-Middle (MitM) Attack

> **Autor:** Edgardy Olivero | **Matrícula:** 20250704
> **Laboratorio:** EGALDITO\_LAB | **Herramienta:** Python 3 + Scapy
> **Repositorio:** [github.com/Edgardy715/ARP-MitM](https://github.com/Edgardy715/ARP-MitM)

---

## 📋 Objetivo del Laboratorio

Demostrar cómo un atacante en el mismo segmento L2 puede posicionarse entre una víctima y su gateway mediante envenenamiento de tablas ARP (ARP Poisoning), interceptando y leyendo todo el tráfico en texto claro mientras la conexión de la víctima permanece activa y sin interrupciones. ARP es vulnerable porque no valida la autenticidad de las respuestas, lo que permite que un host malicioso falsifique asociaciones IP-MAC en la red local.

---

## 🎯 Objetivo del Script

Envenenar simultáneamente las cachés ARP de la víctima y del gateway con la MAC del atacante, habilitar IP forwarding para mantener la conectividad de la víctima, capturar e imprimir en tiempo real los flujos IP interceptados y, al detener el ataque, restaurar automáticamente las tablas ARP correctas en ambos extremos.

---

## 📁 Estructura del Repositorio

```text
ARP-MitM/
├── Script/
│   └── ARP-MitM.py                       ← Script principal del ataque
├── Mitigacion/
│   └── Mitigacion-ARP-MitM.ios           ← Comandos DAI (Cisco IOS)
├── Conf-Topologia/
│   └── scripts_bases_configs/
│       ├── R1.ios
│       ├── SW1-VTPSERVER.ios
│       └── SW2.ios
├── Topologia/
│   └── Topologia.png
└── README.md
```

---

## ⚙️ Parámetros del Script

| Variable | Valor | Descripción |
|---|---|---|
| `IFACE` | `eth0.10` | Subinterfaz VLAN 10 del atacante. |
| `GW_IP` | interactivo | IP del gateway ingresada por el usuario al ejecutar. |
| `VIC_IP` | interactivo | IP de la víctima ingresada por el usuario al ejecutar. |
| `GW_MAC` | auto | MAC del gateway resuelta automáticamente vía ARP request (`srp`). |
| `VIC_MAC` | auto | MAC de la víctima resuelta automáticamente vía ARP request (`srp`). |
| `ATK_MAC` | auto | MAC del atacante obtenida con `get_if_hwaddr(IFACE)`. |
| `sleep(2)` | 2 segundos | Intervalo de re-envenenamiento ARP para mantener el ataque activo. |

---

## 🛠️ Requisitos

```bash
# Dependencias
pip install scapy

# Crear subinterfaz VLAN 10 si no existe
ip link add link eth0 name eth0.10 type vlan id 10
ip link set eth0.10 up

# Ejecutar como root
sudo python3 Script/ARP-MitM.py
```

---

## 🔍 Funcionamiento del Script

### Flujo de ejecución

```text
1. Solicita GW_IP y VIC_IP al usuario.
2. Resuelve MACs vía ARP request broadcast (srp, timeout=3).
3. Activa IP forwarding:
   echo 1 > /proc/sys/net/ipv4/ip_forward
4. Inicia un hilo 'poison' que cada 2 segundos envía:
   → ARP Reply a la víctima:  "GW_IP tiene MAC_atacante"
   → ARP Reply al gateway:    "VIC_IP tiene MAC_atacante"
5. sniff() en eth0.10 filtrando ip host VIC_IP.
6. Imprime src_ip → dst_ip y el protocolo de cada paquete interceptado.
7. Ctrl+C → detiene el hilo y ejecuta restore().
8. restore() envía 5 respuestas ARP correctas a ambos extremos.
9. Desactiva IP forwarding.
```

### Envenenamiento ARP bidireccional

```text
Víctima cree que:   GW_IP  → MAC_atacante
Gateway cree que:   VIC_IP → MAC_atacante

Resultado:
  El atacante queda en el medio, reenviando tráfico entre víctima y gateway.
  La víctima no nota interrupción gracias al IP forwarding activo.
```

### Restauración automática al detener

```text
5 repeticiones de:
  ARP Reply → Víctima  : GW_IP  tiene GW_MAC_real
  ARP Reply → Gateway  : VIC_IP tiene VIC_MAC_real

IP Forwarding: OFF
```

---

## 🌐 Documentación de la Red

### Topología del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |◄──────►|  GNS3 vIOS-L2       |◄──────►|  GNS3 vIOS-L2       |
|  eth0 / eth0.10  | Gi0/1  | VTP Client          | Gi0/0  | VTP Server          |
| 0c:bf:c5:c2:00:00|        | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000      |
+------------------+        +---------------------+        +---------------------+
                                                                    | Gi0/1
                                                         +---------------------+
                                                         |         R1          |
                                                         |  192.168.10.1/24    |
                                                         +---------------------+
```

> Topología completa disponible en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Máscara | MAC | Rol |
|---|---|---|---|---|---|
| Kali Linux | `eth0.10` | 10 | 192.168.10.x/24 | `0c:bf:c5:c2:00:00` | Atacante |
| SW1 | Gi0/0 (trunk) | 1, 10 | — | `0cb5.a4d7.0000` | VTP Server / Root Bridge |
| SW2 | Gi0/1 (acceso) | 1, 10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP Server |

```text
VTP Domain  : EGALDITO_LAB
SW1         : VTP Server | STP Root Bridge | Priority 32769 | MAC 0cb5.a4d7.0000
SW2         : VTP Client
VLAN 10     : RED_LOCAL — 192.168.10.0/24
```

---

## 🛡️ Contramedidas

El archivo de mitigación está en `Mitigacion/Mitigacion-ARP-MitM.ios`.

### 1. Dynamic ARP Inspection (DAI) — defensa principal

```cisco
en
conf term
ip dhcp snooping
ip dhcp snooping vlan 10

ip arp inspection vlan 10

! Puerto troncal hacia SW1 = trusted
interface GigabitEthernet0/0
 ip dhcp snooping trust
 ip arp inspection trust
exit

! Puerto del atacante queda untrusted por defecto
do wr
```

> DAI valida cada paquete ARP contra la tabla de bindings construida por DHCP Snooping. Si la asociación IP-MAC del paquete ARP no coincide con un binding conocido, el paquete es descartado automáticamente, neutralizando el envenenamiento.
>
> **Nota:** La mitigación se aplica sobre `vlan 10` porque es la VLAN donde el script realiza el ataque (`eth0.10`). Aplicar DAI solo en VLAN 1 no protegería el segmento donde conviven la víctima y el atacante.

### 2. Mantener puertos de acceso como untrusted

```cisco
! Los puertos de usuario nunca deben marcarse como trusted.
! Solo los enlaces entre switches o hacia routers controlados
! deben recibir el comando ip arp inspection trust.
```

### Verificación

```cisco
SW2# show ip arp inspection vlan 10
SW2# show ip arp inspection statistics
SW2# show ip dhcp snooping binding
```

---

## 🎬 Video Demostrativo

**Lista de reproducción EGALDITO\_LAB — Layer 2 Network Attacks:**
[https://www.youtube.com/playlist?list=PL24FUvJVT9rBmlkIyA1pGp28VHhh3JK1j](https://www.youtube.com/playlist?list=PL24FUvJVT9rBmlkIyA1pGp28VHhh3JK1j)

**Video de este ataque:**
[https://youtu.be/XX4U93nse-E](https://youtu.be/XX4U93nse-E)

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*
*Autor: Edgardy Olivero | 20250704 | EGALDITO\_LAB*
