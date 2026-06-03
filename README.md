![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# ARP Man-in-the-Middle (MitM) Attack

> **Autor:** Edgardy Olivero | **Matricula:** 20250704  
> **Laboratorio:** EGALDITO_LAB | **Herramienta:** Python 3 + Scapy  
> **Repositorio:** [github.com/Edgardy715/ARP-MitM](https://github.com/Edgardy715/ARP-MitM)

---

## Objetivo del Laboratorio

Demostrar como un atacante en el mismo segmento L2 puede posicionarse entre una victima y su gateway mediante envenenamiento de tablas ARP (ARP Poisoning), interceptando y leyendo todo el trafico en texto claro mientras la conexion de la victima permanece activa y sin interrupciones. ARP es vulnerable porque no valida autenticidad de las respuestas, por lo que un host malicioso puede falsificar asociaciones IP-MAC en la red local [web:69][web:72][web:74].

## Objetivo del Script

Envenenar simultaneamente las cachés ARP de la victima y del gateway con la MAC del atacante, habilitar IP forwarding para mantener la conectividad de la victima, capturar e imprimir en tiempo real los flujos IP interceptados y, al detener el ataque, restaurar automaticamente las tablas ARP correctas [web:69][web:74][web:76].

---

## Estructura del Repositorio

```text
ARP-MitM/
├── Script/
│   └── ARP-MitM.py                       <- Script principal del ataque
├── Mitigacion/
│   └── Mitigacion-ARP-MitM.ios           <- Comandos DAI (Cisco IOS)
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

## Parametros del Script

| Variable | Valor | Descripcion |
|---|---|---|
| `IFACE` | `eth0.10` | Subinterfaz VLAN10 del atacante. |
| `GW_IP` | interactivo | IP del gateway ingresada por el usuario. |
| `VIC_IP` | interactivo | IP de la victima ingresada por el usuario. |
| `GW_MAC` | auto | MAC del gateway resuelta con ARP request (`srp`). |
| `VIC_MAC` | auto | MAC de la victima resuelta con ARP request (`srp`). |
| `ATK_MAC` | auto | MAC del atacante obtenida con `get_if_hwaddr(IFACE)`. |
| `sleep(2)` | 2 segundos | Intervalo de re-envenenamiento ARP. |

---

## Requisitos

```bash
# Dependencias
pip install scapy

# Configurar subinterfaz VLAN10 si no existe
ip link add link eth0 name eth0.10 type vlan id 10
ip link set eth0.10 up

# Ejecutar como root
sudo python3 Script/ARP-MitM.py
```

---

## Funcionamiento del Script

### Flujo de ejecucion

```text
1. Solicita GW_IP y VIC_IP al usuario.
2. Resuelve MACs via ARP request broadcast (srp, timeout=3).
3. Activa IP forwarding:
   echo 1 > /proc/sys/net/ipv4/ip_forward
4. Inicia un hilo 'poison' que cada 2 segundos envia:
   -> ARP Reply a la victima:  "GW_IP tiene MAC_atacante"
   -> ARP Reply al gateway:    "VIC_IP tiene MAC_atacante"
5. sniff() en eth0.10 filtrando ip host VIC_IP.
6. Imprime src_ip -> dst_ip y el protocolo de cada paquete.
7. Ctrl+C -> detiene el hilo y ejecuta restore().
8. restore() envia varias respuestas ARP correctas para ambos lados.
9. Desactiva IP forwarding.
```

### Envenenamiento ARP bidireccional

```text
Victima cree que:   GW_IP   -> MAC_atacante
Gateway cree que:   VIC_IP  -> MAC_atacante

Resultado:
Atacante queda en medio, reenviando trafico entre victima y gateway.
```

### Restauracion automatica al detener

```text
5 repeticiones de:
  ARP Reply -> Victima:  GW_IP  tiene GW_MAC_real
  ARP Reply -> Gateway:  VIC_IP tiene VIC_MAC_real

IP Forwarding: OFF
```

---

## Documentacion de la Red

### Topologia del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |<------>|  GNS3 vIOS-L2       |<------>|  GNS3 vIOS-L2      |
|  eth0 / eth0.10  |  Gi0/1 | VTP Client          |  Gi0/0 | VTP Server         |
| 0c:bf:c5:c2:0000 |        | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000    |
+------------------+        +---------------------+        +---------------------+
                                                                   |  Gi0/1
                                                        +---------------------+
                                                        |         R1          |
                                                        |  192.168.10.1/24    |
                                                        +---------------------+
```

> Topologia completa en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Mascara | MAC | Rol |
|---|---|---|---|---|---|
| Kali Linux | eth0.10 | 10 | 192.168.10.x/24 | `0c:bf:c5:c2:00:00` | Atacante |
| SW1 | Gi0/0 (trunk) | 1,10 | — | `0cb5.a4d7.0000` | VTP Server / Root |
| SW2 | Gi0/0 (trunk) | 1,10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP |

```text
VTP Domain: EGALDITO_LAB | SW1: VTP Server | SW2: VTP Client
STP Root Bridge: SW1 | Priority: 32769 | MAC: 0cb5.a4d7.0000
VLAN 10: RED_LOCAL (192.168.10.0/24)
```

---

## Capturas de Pantalla

| Momento | Descripcion |
|---|---|
| Pre-ataque | `arp -a` en la victima muestra el gateway real. |
| Durante ataque | `arp -a` cambia y el gateway apunta a la MAC del atacante. |
| Trafico visible | La terminal de Kali muestra el trafico interceptado. |
| Post-restauracion | Las tablas ARP vuelven a sus valores legitimos. |

---

## Contramedidas

El archivo de mitigacion esta en `Mitigacion/Mitigacion-ARP-MitM.ios`.

### 1. Dynamic ARP Inspection — defensa principal

```cisco
en
conf term
! Habilitar DAI en VLAN1 (ajustar a la VLAN correspondiente)
ip arp inspection vlan 1

! Si usas DHCP Snooping, debe estar habilitado para crear la tabla de bindings
ip dhcp snooping
ip dhcp snooping vlan 1

! Puerto troncal hacia el switch vecino = trusted
interface GigabitEthernet0/0
 ip arp inspection trust
exit

do wr
```

> DAI valida los paquetes ARP usando la base de bindings de DHCP Snooping y descarta mensajes ARP invalidos o inconsistentes [web:69][web:72][web:73][web:74].

### Verificacion

```cisco
SW2# show ip arp inspection vlan 1
SW2# show ip arp inspection statistics
```

### 2. Mantener puertos de acceso como untrusted

```cisco
interface GigabitEthernet0/1
 ! No confiar en puertos de usuario
```

> La recomendacion es dejar los puertos de usuario como untrusted y confiar solo en enlaces entre switches o uplinks controlados [web:70][web:77][web:78].

---

## Video Demostrativo

**Lista de reproduccion EGALDITO_LAB:** [Layer 2 Network Attacks](https://www.youtube.com/@Edgardy715)

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*  
*Autor: Edgardy Olivero | 20250704 | EGALDITO_LAB*
