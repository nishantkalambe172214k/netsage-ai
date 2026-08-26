import json
import csv
import os
from typing import List, Dict, Any

CASES_DATA: List[Dict[str, Any]] = [
    # --- 1. VLAN CASES (1-4) ---
    {
        "case_id": "CASE-VLAN-001",
        "title": "Inter-VLAN Routing Blocked by Sub-interface Dot1Q Tag Mismatch",
        "category": "VLAN",
        "description": "PC1 in VLAN 10 cannot ping PC2 in VLAN 20 via Router-on-a-Stick R1.",
        "symptoms": "Ping destination host unreachable from 192.168.10.10 to 192.168.20.10.",
        "target_rule": "Missing VLAN / VLAN Mismatch",
        "osi_layer": "Layer 2 - Data Link",
        "expected_root_cause": "Router sub-interface GigabitEthernet0/0.20 is configured with encapsulation dot1Q 30 instead of dot1Q 20.",
        "expected_fix": "Configure 'encapsulation dot1Q 20' under interface GigabitEthernet0/0.20 on R1.",
        "network_topology": {
            "devices": ["R1", "SW1", "PC1", "PC2"],
            "links": [
                {"from": "PC1:Fa0", "to": "SW1:Fa0/1", "vlan": 10},
                {"from": "PC2:Fa0", "to": "SW1:Fa0/2", "vlan": 20},
                {"from": "SW1:Gi0/1", "to": "R1:Gi0/0", "mode": "trunk"}
            ],
            "clients": [
                {"name": "PC1", "ip": "192.168.10.10", "mask": "255.255.255.0", "gateway": "192.168.10.1", "vlan": 10},
                {"name": "PC2", "ip": "192.168.20.10", "mask": "255.255.255.0", "gateway": "192.168.20.1", "vlan": 20}
            ]
        },
        "raw_configs": {
            "SW1": "vlan 10\n name Sales\nvlan 20\n name Eng\ninterface FastEthernet0/1\n switchport mode access\n switchport access vlan 10\ninterface FastEthernet0/2\n switchport mode access\n switchport access vlan 20\ninterface GigabitEthernet0/1\n switchport mode trunk",
            "R1": "interface GigabitEthernet0/0\n no shutdown\ninterface GigabitEthernet0/0.10\n encapsulation dot1Q 10\n ip address 192.168.10.1 255.255.255.0\ninterface GigabitEthernet0/0.20\n encapsulation dot1Q 30\n ip address 192.168.20.1 255.255.255.0"
        }
    },
    {
        "case_id": "CASE-VLAN-002",
        "title": "Access Port Assigned to Non-Existent VLAN 30 on Switch SW2",
        "category": "VLAN",
        "description": "Finance workstation PC3 connected to Fa0/5 cannot communicate on the local LAN.",
        "symptoms": "Interface status shows down/inactive and frames are dropped at ingress.",
        "target_rule": "Missing VLAN",
        "osi_layer": "Layer 2 - Data Link",
        "expected_root_cause": "Port Fa0/5 is assigned to VLAN 30, but VLAN 30 was never created in the switch VLAN database.",
        "expected_fix": "Create 'vlan 30' with name Finance in global configuration on SW2.",
        "network_topology": {
            "devices": ["SW2", "PC3"],
            "links": [{"from": "PC3:Fa0", "to": "SW2:Fa0/5", "vlan": 30}],
            "clients": [{"name": "PC3", "ip": "192.168.30.50", "mask": "255.255.255.0", "gateway": "192.168.30.1", "vlan": 30}]
        },
        "raw_configs": {
            "SW2": "vlan 10\n name HR\nvlan 20\n name Sales\ninterface FastEthernet0/5\n switchport mode access\n switchport access vlan 30\n no shutdown"
        }
    },
    {
        "case_id": "CASE-VLAN-003",
        "title": "Trunk Link Pruning Drops Allowed VLAN 50 Between SW1 and SW2",
        "category": "VLAN",
        "description": "Hosts in VLAN 50 on SW2 cannot reach core servers in VLAN 50 on SW1.",
        "symptoms": "Broadcast and unicast traffic in VLAN 50 drops across switch uplink.",
        "target_rule": "Missing VLAN",
        "osi_layer": "Layer 2 - Data Link",
        "expected_root_cause": "Uplink Gi0/2 has 'switchport trunk allowed vlan 10,20', omitting VLAN 50.",
        "expected_fix": "Execute 'switchport trunk allowed vlan add 50' on interface Gi0/2 on SW1 and SW2.",
        "network_topology": {
            "devices": ["SW1", "SW2"],
            "links": [{"from": "SW1:Gi0/2", "to": "SW2:Gi0/2", "mode": "trunk"}],
            "clients": [{"name": "Server1", "ip": "10.50.0.100", "mask": "255.255.255.0", "gateway": "10.50.0.1", "vlan": 50}]
        },
        "raw_configs": {
            "SW1": "vlan 10\nvlan 20\nvlan 50\ninterface GigabitEthernet0/2\n switchport mode trunk\n switchport trunk allowed vlan 10,20",
            "SW2": "vlan 10\nvlan 20\nvlan 50\ninterface GigabitEthernet0/2\n switchport mode trunk\n switchport trunk allowed vlan 10,20"
        }
    },
    {
        "case_id": "CASE-VLAN-004",
        "title": "Native VLAN Mismatch on Trunk Link Between SW1 and SW3",
        "category": "VLAN",
        "description": "CDP logs warn about native VLAN mismatch and untagged traffic is leaking between VLAN 1 and VLAN 99.",
        "symptoms": "CDP native vlan mismatch warning on console, traffic misrouted.",
        "target_rule": "Missing VLAN / VLAN Mismatch",
        "osi_layer": "Layer 2 - Data Link",
        "expected_root_cause": "SW1 Gi0/1 configured with native vlan 99 while SW3 Gi0/1 is using default native vlan 1.",
        "expected_fix": "Configure 'switchport trunk native vlan 99' on SW3 interface Gi0/1.",
        "network_topology": {
            "devices": ["SW1", "SW3"],
            "links": [{"from": "SW1:Gi0/1", "to": "SW3:Gi0/1", "mode": "trunk"}]
        },
        "raw_configs": {
            "SW1": "interface GigabitEthernet0/1\n switchport mode trunk\n switchport trunk native vlan 99",
            "SW3": "interface GigabitEthernet0/1\n switchport mode trunk"
        }
    },

    # --- 2. GATEWAY CASES (5-8) ---
    {
        "case_id": "CASE-GW-005",
        "title": "Workstation Configured with Inactive Default Gateway IP",
        "category": "Gateway",
        "description": "PC4 on subnet 192.168.1.0/24 cannot access any external network or internet.",
        "symptoms": "Local pings work within subnet, but pings to 8.8.8.8 fail with Request Timed Out.",
        "target_rule": "Gateway mismatch",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "PC4 has default gateway set to 192.168.1.254, but Router R1 interface is 192.168.1.1.",
        "expected_fix": "Set PC4 default gateway to 192.168.1.1.",
        "network_topology": {
            "devices": ["R1", "SW1", "PC4"],
            "clients": [{"name": "PC4", "ip": "192.168.1.50", "mask": "255.255.255.0", "gateway": "192.168.1.254", "vlan": 1}]
        },
        "raw_configs": {
            "R1": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n no shutdown"
        }
    },
    {
        "case_id": "CASE-GW-006",
        "title": "Router Default Gateway Interface In Administratively Down State",
        "category": "Gateway",
        "description": "Branch office PCs cannot reach HQ because Router R2 LAN interface is disabled.",
        "symptoms": "Default gateway 10.1.1.1 does not respond to ARP requests or ICMP echo.",
        "target_rule": "Interface down",
        "osi_layer": "Layer 1 - Physical",
        "expected_root_cause": "Router R2 interface GigabitEthernet0/0 is administratively shutdown.",
        "expected_fix": "Execute 'no shutdown' under interface GigabitEthernet0/0 on R2.",
        "network_topology": {
            "devices": ["R2", "PC5"],
            "clients": [{"name": "PC5", "ip": "10.1.1.20", "mask": "255.255.255.0", "gateway": "10.1.1.1"}]
        },
        "raw_configs": {
            "R2": "interface GigabitEthernet0/0\n ip address 10.1.1.1 255.255.255.0\n shutdown"
        }
    },
    {
        "case_id": "CASE-GW-007",
        "title": "Default Gateway Subnet Mask Mismatch on LAN Interface",
        "category": "Gateway",
        "description": "Hosts on 172.16.10.0/24 subnet experience intermittent gateway routing drops.",
        "symptoms": "Hosts with IPs > 172.16.10.127 cannot route packets through gateway.",
        "target_rule": "Wrong subnet mask",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Router interface configured with mask 255.255.255.128 (/25) instead of 255.255.255.0 (/24).",
        "expected_fix": "Reconfigure 'ip address 172.16.10.1 255.255.255.0' on Router interface Gi0/1.",
        "network_topology": {
            "devices": ["R3", "PC6"],
            "clients": [{"name": "PC6", "ip": "172.16.10.150", "mask": "255.255.255.0", "gateway": "172.16.10.1"}]
        },
        "raw_configs": {
            "R3": "interface GigabitEthernet0/1\n ip address 172.16.10.1 255.255.255.128\n no shutdown"
        }
    },
    {
        "case_id": "CASE-GW-008",
        "title": "Duplicate Default Gateway IP Assigned to Backup Device",
        "category": "Gateway",
        "description": "ARP flapping causes widespread intermittent packet loss across all LAN clients.",
        "symptoms": "Duplicate IP address detected syslog message and flapping ARP cache entries.",
        "target_rule": "Duplicate IP",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Switch SW1 management SVI interface VLAN 1 configured with 192.168.1.1, colliding with Router R1.",
        "expected_fix": "Change SW1 interface vlan 1 IP to 192.168.1.2 255.255.255.0.",
        "network_topology": {
            "devices": ["R1", "SW1", "PC1"],
            "clients": [{"name": "PC1", "ip": "192.168.1.10", "mask": "255.255.255.0", "gateway": "192.168.1.1"}]
        },
        "raw_configs": {
            "R1": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n no shutdown",
            "SW1": "interface Vlan1\n ip address 192.168.1.1 255.255.255.0\n no shutdown"
        }
    },

    # --- 3. DHCP CASES (9-12) ---
    {
        "case_id": "CASE-DHCP-009",
        "title": "Missing IP Helper-Address on Remote Branch Router",
        "category": "DHCP",
        "description": "Branch clients on VLAN 10 fail to receive automatic IP addresses from centralized HQ DHCP server.",
        "symptoms": "Clients get APIPA 169.254.x.x addresses after DHCP Discover timeout.",
        "target_rule": "Missing route / Gateway mismatch",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Branch router sub-interface Gi0/0.10 lacks 'ip helper-address 10.0.0.50' forwarding DHCP broadcasts.",
        "expected_fix": "Add 'ip helper-address 10.0.0.50' under interface GigabitEthernet0/0.10 on Branch Router.",
        "network_topology": {
            "devices": ["Branch-R1", "HQ-DHCP"],
            "clients": [{"name": "Branch-PC1", "vlan": 10, "ip": "169.254.10.5", "mask": "255.255.0.0", "gateway": ""}]
        },
        "raw_configs": {
            "Branch-R1": "interface GigabitEthernet0/0.10\n encapsulation dot1Q 10\n ip address 192.168.10.1 255.255.255.0\n no shutdown"
        }
    },
    {
        "case_id": "CASE-DHCP-010",
        "title": "Cisco IOS DHCP Pool Default-Router Points to Invalid Network",
        "category": "DHCP",
        "description": "DHCP clients obtain IP addresses but cannot route to other subnets.",
        "symptoms": "Client ipconfig shows Default Gateway 192.168.99.1 for client on 192.168.1.0/24 subnet.",
        "target_rule": "Gateway mismatch",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "DHCP pool POOL-A has 'default-router 192.168.99.1' instead of 192.168.1.1.",
        "expected_fix": "Change 'default-router 192.168.1.1' in ip dhcp pool POOL-A on Router R1.",
        "network_topology": {
            "devices": ["R1", "PC1"],
            "clients": [{"name": "PC1", "ip": "192.168.1.15", "mask": "255.255.255.0", "gateway": "192.168.99.1"}]
        },
        "raw_configs": {
            "R1": "ip dhcp pool POOL-A\n network 192.168.1.0 255.255.255.0\n default-router 192.168.99.1\n dns-server 8.8.8.8\ninterface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0"
        }
    },
    {
        "case_id": "CASE-DHCP-011",
        "title": "Router Default Gateway IP Not Excluded in DHCP Scope",
        "category": "DHCP",
        "description": "DHCP server leases the router gateway IP 192.168.1.1 to a new client, triggering IP conflict.",
        "symptoms": "IP conflict error message, intermittent gateway connectivity for all devices.",
        "target_rule": "Duplicate IP",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Missing 'ip dhcp excluded-address 192.168.1.1 192.168.1.10' in global configuration.",
        "expected_fix": "Configure 'ip dhcp excluded-address 192.168.1.1 192.168.1.10' on Router R1.",
        "network_topology": {
            "devices": ["R1", "PC1"],
            "clients": [{"name": "PC1", "ip": "192.168.1.1", "mask": "255.255.255.0", "gateway": "192.168.1.1"}]
        },
        "raw_configs": {
            "R1": "ip dhcp pool LAN-POOL\n network 192.168.1.0 255.255.255.0\n default-router 192.168.1.1\ninterface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0"
        }
    },
    {
        "case_id": "CASE-DHCP-012",
        "title": "DHCP Snooping Untrusted Uplink Port Drops Server Responses",
        "category": "DHCP",
        "description": "Switch SW1 drops DHCP Offer and Ack packets from core DHCP server.",
        "symptoms": "DHCP DISCOVER sent but no OFFER received by client.",
        "target_rule": "Interface down / Missing VLAN",
        "osi_layer": "Layer 2 - Data Link",
        "expected_root_cause": "Uplink interface Gi0/1 on SW1 is not configured with 'ip dhcp snooping trust'.",
        "expected_fix": "Apply 'ip dhcp snooping trust' to interface GigabitEthernet0/1 on SW1.",
        "network_topology": {
            "devices": ["SW1", "DHCP-Server"],
            "links": [{"from": "SW1:Gi0/1", "to": "DHCP-Server:Fa0"}]
        },
        "raw_configs": {
            "SW1": "ip dhcp snooping\nip dhcp snooping vlan 10\ninterface GigabitEthernet0/1\n switchport mode trunk"
        }
    },

    # --- 4. DNS CASES (13-16) ---
    {
        "case_id": "CASE-DNS-013",
        "title": "Incorrect DNS Server IP Configured on Client Workstations",
        "category": "DNS",
        "description": "Users cannot browse domain names (e.g. www.cisco.com) but can ping raw IP addresses.",
        "symptoms": "nslookup fails with server failure or timeout, direct IP ping to 8.8.8.8 succeeds.",
        "target_rule": "Gateway mismatch / DNS",
        "osi_layer": "Layer 7 - Application",
        "expected_root_cause": "Client DNS server is set to 192.168.1.250 which does not exist, instead of actual DNS server 192.168.1.10.",
        "expected_fix": "Update client / DHCP pool DNS configuration to 192.168.1.10.",
        "network_topology": {
            "devices": ["R1", "DNS-Server", "PC1"],
            "clients": [{"name": "PC1", "ip": "192.168.1.50", "mask": "255.255.255.0", "gateway": "192.168.1.1", "dns": "192.168.1.250"}]
        },
        "raw_configs": {
            "DNS-Server": "interface FastEthernet0\n ip address 192.168.1.10 255.255.255.0\n no shutdown"
        }
    },
    {
        "case_id": "CASE-DNS-014",
        "title": "DNS Server Service Port Inactive on Server in Packet Tracer",
        "category": "DNS",
        "description": "DNS queries sent to valid server IP 10.0.0.53 are rejected with ICMP port unreachable.",
        "symptoms": "DNS service turned off in Packet Tracer server config tab.",
        "target_rule": "Interface down",
        "osi_layer": "Layer 7 - Application",
        "expected_root_cause": "The DNS Service daemon on Server 10.0.0.53 is switched OFF.",
        "expected_fix": "Enable DNS Service in the Server configuration and verify A record entries.",
        "network_topology": {
            "devices": ["Server-DNS", "PC1"],
            "clients": [{"name": "PC1", "ip": "10.0.0.100", "mask": "255.255.255.0", "gateway": "10.0.0.1", "dns": "10.0.0.53"}]
        },
        "raw_configs": {
            "Server-DNS": "interface FastEthernet0\n ip address 10.0.0.53 255.255.255.0\nservice dns status: OFF"
        }
    },
    {
        "case_id": "CASE-DNS-015",
        "title": "Missing A Record for Intranet Web Server",
        "category": "DNS",
        "description": "Employees cannot resolve 'portal.corp.local' but can resolve external websites.",
        "symptoms": "Non-existent domain (NXDOMAIN) returned for internal portal hostname.",
        "target_rule": "Missing route / DNS",
        "osi_layer": "Layer 7 - Application",
        "expected_root_cause": "The internal DNS zone lacks an A record mapping portal.corp.local to 10.10.10.80.",
        "expected_fix": "Add A record 'portal.corp.local -> 10.10.10.80' on the DNS Server.",
        "network_topology": {
            "devices": ["DNS-Server", "Web-Server"],
            "clients": [{"name": "PC1", "dns": "10.10.10.5"}]
        },
        "raw_configs": {
            "DNS-Server": "ip host intranet.corp.local 10.10.10.70\n! missing portal.corp.local"
        }
    },
    {
        "case_id": "CASE-DNS-016",
        "title": "Subnet Mask Misconfiguration on Central DNS Server",
        "category": "DNS",
        "description": "DNS Server cannot reply to clients from adjacent subnets due to improper local mask.",
        "symptoms": "Local clients resolve DNS, remote subnet clients time out.",
        "target_rule": "Wrong subnet mask",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "DNS Server interface configured with 255.255.255.240 (/28) while router uses 255.255.255.0 (/24).",
        "expected_fix": "Correct DNS Server interface mask to 255.255.255.0.",
        "network_topology": {
            "devices": ["R1", "DNS-Server"],
            "clients": [{"name": "DNS-Server", "ip": "172.16.1.50", "mask": "255.255.255.240", "gateway": "172.16.1.1"}]
        },
        "raw_configs": {
            "R1": "interface GigabitEthernet0/0\n ip address 172.16.1.1 255.255.255.0\n no shutdown"
        }
    },

    # --- 5. ROUTING CASES (17-20) ---
    {
        "case_id": "CASE-ROUTE-017",
        "title": "Missing Default Static Route on Edge Router to ISP Gateway",
        "category": "Routing",
        "description": "Internal LAN cannot access external internet hosts because Edge Router has no default gateway route.",
        "symptoms": "Pings to internet IP 209.165.200.225 drop with 'no route to host'.",
        "target_rule": "Missing route",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Edge Router R1 is missing static default route 'ip route 0.0.0.0 0.0.0.0 203.0.113.2'.",
        "expected_fix": "Add 'ip route 0.0.0.0 0.0.0.0 203.0.113.2' on Router R1.",
        "network_topology": {
            "devices": ["R1", "ISP-R2"],
            "links": [{"from": "R1:Gi0/1", "to": "ISP-R2:Gi0/1"}]
        },
        "raw_configs": {
            "R1": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\ninterface GigabitEthernet0/1\n ip address 203.0.113.1 255.255.255.252\n! missing default route"
        }
    },
    {
        "case_id": "CASE-ROUTE-018",
        "title": "OSPF Link MTU Mismatch Halts Neighbor Adjacency in EXSTART",
        "category": "Routing",
        "description": "Routers R1 and R2 fail to form full OSPF routing adjacency over GigabitEthernet0/0.",
        "symptoms": "show ip ospf neighbor shows state EXSTART/EXCHANGE indefinitely.",
        "target_rule": "Wrong subnet mask / Routing",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Interface Gi0/0 on R2 is set to MTU 1400 while R1 uses standard MTU 1500.",
        "expected_fix": "Set 'ip mtu 1500' on interface GigabitEthernet0/0 on R2 (or apply 'ip ospf mtu-ignore').",
        "network_topology": {
            "devices": ["R1", "R2"],
            "links": [{"from": "R1:Gi0/0", "to": "R2:Gi0/0"}]
        },
        "raw_configs": {
            "R1": "interface GigabitEthernet0/0\n ip address 10.0.0.1 255.255.255.252\n ip mtu 1500\nrouter ospf 1\n network 10.0.0.0 0.0.0.3 area 0",
            "R2": "interface GigabitEthernet0/0\n ip address 10.0.0.2 255.255.255.252\n ip mtu 1400\nrouter ospf 1\n network 10.0.0.0 0.0.0.3 area 0"
        }
    },
    {
        "case_id": "CASE-ROUTE-019",
        "title": "OSPF Passive-Interface Configured on Transit Inter-Router Link",
        "category": "Routing",
        "description": "Router R1 and R3 do not exchange OSPF LSAs across transit link Gi0/2.",
        "symptoms": "No OSPF Hello packets sent or received on Gi0/2; neighbor relationship is down.",
        "target_rule": "Missing route",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Interface GigabitEthernet0/2 was mistakenly set to passive-interface under router ospf 1.",
        "expected_fix": "Execute 'no passive-interface GigabitEthernet0/2' under router ospf 1 on R1.",
        "network_topology": {
            "devices": ["R1", "R3"],
            "links": [{"from": "R1:Gi0/2", "to": "R3:Gi0/2"}]
        },
        "raw_configs": {
            "R1": "interface GigabitEthernet0/2\n ip address 10.1.0.1 255.255.255.252\nrouter ospf 1\n passive-interface GigabitEthernet0/2\n network 10.1.0.0 0.0.0.3 area 0",
            "R3": "interface GigabitEthernet0/2\n ip address 10.1.0.2 255.255.255.252\nrouter ospf 1\n network 10.1.0.0 0.0.0.3 area 0"
        }
    },
    {
        "case_id": "CASE-ROUTE-020",
        "title": "EIGRP Autonomous System Number Mismatch Between R1 and R2",
        "category": "Routing",
        "description": "EIGRP routes are not populated in routing table between adjacent routers.",
        "symptoms": "EIGRP neighbor table is empty.",
        "target_rule": "Missing route",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "R1 runs EIGRP AS 100 while R2 runs EIGRP AS 200.",
        "expected_fix": "Reconfigure R2 to run 'router eigrp 100'.",
        "network_topology": {
            "devices": ["R1", "R2"]
        },
        "raw_configs": {
            "R1": "interface GigabitEthernet0/0\n ip address 10.2.0.1 255.255.255.252\nrouter eigrp 100\n network 10.2.0.0 0.0.0.3",
            "R2": "interface GigabitEthernet0/0\n ip address 10.2.0.2 255.255.255.252\nrouter eigrp 200\n network 10.2.0.0 0.0.0.3"
        }
    },

    # --- 6. ACL CASES (21-24) ---
    {
        "case_id": "CASE-ACL-021",
        "title": "Standard Access List Implicit Deny Dropping Department Subnet",
        "category": "ACL",
        "description": "Sales department PCs on 192.168.20.0/24 are completely unable to reach Server Farm.",
        "symptoms": "Pings fail with 'Communication administratively prohibited' from router.",
        "target_rule": "Missing route / ACL",
        "osi_layer": "Layer 4 - Transport",
        "expected_root_cause": "ACL 10 only permits 192.168.10.0 and hits implicit deny all for 192.168.20.0.",
        "expected_fix": "Add 'access-list 10 permit 192.168.20.0 0.0.0.255' to R1 configuration.",
        "network_topology": {
            "devices": ["R1", "ServerFarm"],
            "clients": [{"name": "PC-Sales", "ip": "192.168.20.50", "mask": "255.255.255.0", "gateway": "192.168.20.1"}]
        },
        "raw_configs": {
            "R1": "access-list 10 permit 192.168.10.0 0.0.0.255\ninterface GigabitEthernet0/1\n ip access-group 10 out"
        }
    },
    {
        "case_id": "CASE-ACL-022",
        "title": "Extended ACL Applied in Inbound Direction on Wrong Router Interface",
        "category": "ACL",
        "description": "Web traffic to port 80 is blocked for all incoming traffic from LAN.",
        "symptoms": "HTTP connections fail to initialize; ACL match counter increases on deny statement.",
        "target_rule": "Interface down / ACL",
        "osi_layer": "Layer 4 - Transport",
        "expected_root_cause": "Extended ACL 101 applied 'in' on internal LAN interface with source set to external IP.",
        "expected_fix": "Correct direction to 'ip access-group 101 out' or revise source/destination in ACL 101.",
        "network_topology": {
            "devices": ["R1"]
        },
        "raw_configs": {
            "R1": "access-list 101 permit tcp 10.0.0.0 0.255.255.255 any eq 80\ninterface GigabitEthernet0/0\n ip access-group 101 in"
        }
    },
    {
        "case_id": "CASE-ACL-023",
        "title": "ACL Rule Ordering: Broad Deny Placed Above Specific Permit",
        "category": "ACL",
        "description": "Admin PC at 192.168.1.50 cannot SSH into Router despite specific permit rule.",
        "symptoms": "SSH connection refused/blocked due to top-level deny 192.168.1.0/24 rule.",
        "target_rule": "ACL",
        "osi_layer": "Layer 4 - Transport",
        "expected_root_cause": "Rule 'deny ip 192.168.1.0 0.0.0.255 any' is evaluated before 'permit tcp host 192.168.1.50 any eq 22'.",
        "expected_fix": "Place 'permit tcp host 192.168.1.50 any eq 22' before the subnet deny statement.",
        "network_topology": {
            "devices": ["R1", "Admin-PC"],
            "clients": [{"name": "Admin-PC", "ip": "192.168.1.50"}]
        },
        "raw_configs": {
            "R1": "ip access-list extended MGMT-ACL\n 10 deny ip 192.168.1.0 0.0.0.255 any\n 20 permit tcp host 192.168.1.50 any eq 22\ninterface GigabitEthernet0/0\n ip access-group MGMT-ACL in"
        }
    },
    {
        "case_id": "CASE-ACL-024",
        "title": "ICMP Echo Denied by Restrictive Security ACL on Gateway",
        "category": "ACL",
        "description": "Network monitoring tool cannot ping router gateway interface.",
        "symptoms": "Ping echo requests are dropped, while TCP application traffic succeeds.",
        "target_rule": "ACL",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "ACL denies all ICMP protocol traffic without permit icmp statement.",
        "expected_fix": "Add 'permit icmp any any echo' and 'permit icmp any any echo-reply' to ACL.",
        "network_topology": {
            "devices": ["R1", "Monitor-PC"]
        },
        "raw_configs": {
            "R1": "ip access-list extended SEC-FILTER\n 10 deny icmp any any\n 20 permit ip any any\ninterface GigabitEthernet0/0\n ip access-group SEC-FILTER in"
        }
    },

    # --- 7. NAT CASES (25-27) ---
    {
        "case_id": "CASE-NAT-025",
        "title": "Missing IP NAT Inside Designation on Router LAN Interface",
        "category": "NAT",
        "description": "LAN hosts cannot translate private addresses to public IP when browsing internet.",
        "symptoms": "show ip nat translations displays empty table; outside hosts drop untranslated RFC1918 packets.",
        "target_rule": "Missing route / NAT",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Interface GigabitEthernet0/0 is missing 'ip nat inside' configuration.",
        "expected_fix": "Add 'ip nat inside' under interface GigabitEthernet0/0 on Router R1.",
        "network_topology": {
            "devices": ["R1", "PC1"],
            "clients": [{"name": "PC1", "ip": "192.168.1.100", "gateway": "192.168.1.1"}]
        },
        "raw_configs": {
            "R1": "ip nat inside source list 1 interface GigabitEthernet0/1 overload\naccess-list 1 permit 192.168.1.0 0.0.0.255\ninterface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n! missing ip nat inside\ninterface GigabitEthernet0/1\n ip address 203.0.113.1 255.255.255.252\n ip nat outside"
        }
    },
    {
        "case_id": "CASE-NAT-026",
        "title": "NAT Overload Access-List Subnet Wildcard Mask Inversion",
        "category": "NAT",
        "description": "NAT overload fails to match internal host packets attempting internet outbound access.",
        "symptoms": "Zero translation hits in show ip nat statistics.",
        "target_rule": "Wrong subnet mask / NAT",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "Access-list 1 configured with subnet mask 255.255.255.0 instead of wildcard mask 0.0.0.255.",
        "expected_fix": "Reconfigure 'access-list 1 permit 192.168.1.0 0.0.0.255'.",
        "network_topology": {
            "devices": ["R1"]
        },
        "raw_configs": {
            "R1": "ip nat inside source list 1 interface GigabitEthernet0/1 overload\naccess-list 1 permit 192.168.1.0 255.255.255.0\ninterface GigabitEthernet0/0\n ip nat inside\ninterface GigabitEthernet0/1\n ip nat outside"
        }
    },
    {
        "case_id": "CASE-NAT-027",
        "title": "Missing IP NAT Outside Designation on Internet Gateway Link",
        "category": "NAT",
        "description": "NAT translation table creates entries but return packets are not de-NATted.",
        "symptoms": "TCP SYN sent outward but return SYN-ACK dropped at router boundary.",
        "target_rule": "Interface down / NAT",
        "osi_layer": "Layer 3 - Network",
        "expected_root_cause": "WAN interface Serial0/0/0 or Gi0/1 lacks 'ip nat outside'.",
        "expected_fix": "Add 'ip nat outside' on WAN interface GigabitEthernet0/1.",
        "network_topology": {
            "devices": ["R1"]
        },
        "raw_configs": {
            "R1": "ip nat inside source list 1 interface GigabitEthernet0/1 overload\naccess-list 1 permit 10.0.0.0 0.255.255.255\ninterface GigabitEthernet0/0\n ip nat inside\ninterface GigabitEthernet0/1\n ip address 198.51.100.1 255.255.255.252"
        }
    },

    # --- 8. WIRELESS CASES (28-30) ---
    {
        "case_id": "CASE-WLAN-028",
        "title": "SSID Name Mismatch Between Laptop Client and Lightweight AP",
        "category": "Wireless",
        "description": "Laptop wireless adapter fails to associate with office WLAN access point.",
        "symptoms": "Laptop wireless association indicator remains unlinked / disconnected.",
        "target_rule": "Missing VLAN / Wireless",
        "osi_layer": "Layer 2 - Data Link",
        "expected_root_cause": "Laptop SSID is configured as 'Cisco-Corp' while Access Point broadcasts 'Cisco_Corp'.",
        "expected_fix": "Update laptop wireless client profile SSID to match 'Cisco_Corp'.",
        "network_topology": {
            "devices": ["WLC1", "AP1", "Laptop1"],
            "clients": [{"name": "Laptop1", "ssid": "Cisco-Corp"}]
        },
        "raw_configs": {
            "AP1": "dot11 ssid Cisco_Corp\n authentication open\n authentication key-management wpa2"
        }
    },
    {
        "case_id": "CASE-WLAN-029",
        "title": "WPA2 Pre-Shared Key (PSK) Passphrase Mismatch on Client",
        "category": "Wireless",
        "description": "Wireless host associates with AP but 4-way WPA2 handshake fails.",
        "symptoms": "Authentication failure message, client disconnected immediately after association attempt.",
        "target_rule": "Wireless",
        "osi_layer": "Layer 2 - Data Link",
        "expected_root_cause": "Client entered pre-shared key 'Cisco12345!' while AP expects 'Cisco123!'.",
        "expected_fix": "Configure correct WPA2-PSK key 'Cisco123!' on wireless client.",
        "network_topology": {
            "devices": ["AP1", "Smartphone1"],
            "clients": [{"name": "Smartphone1", "ssid": "OfficeWiFi", "psk": "Cisco12345!"}]
        },
        "raw_configs": {
            "AP1": "dot11 ssid OfficeWiFi\n authentication key-management wpa2\n wpa-psk ascii Cisco123!"
        }
    },
    {
        "case_id": "CASE-WLAN-030",
        "title": "Wireless Access Point Switch Port Missing Trunk / Native VLAN Mapping",
        "category": "Wireless",
        "description": "Wireless clients associating to AP get no IP address because AP management and client traffic are untagged.",
        "symptoms": "AP fails to communicate with WLC; clients on multi-SSID cannot bridge traffic to VLAN 40.",
        "target_rule": "Missing VLAN / Interface down",
        "osi_layer": "Layer 2 - Data Link",
        "expected_root_cause": "Switch port Fa0/12 connected to AP configured as access port instead of trunk.",
        "expected_fix": "Configure 'switchport mode trunk' on Switch interface Fa0/12.",
        "network_topology": {
            "devices": ["SW1", "AP1"],
            "links": [{"from": "SW1:Fa0/12", "to": "AP1:Eth0"}]
        },
        "raw_configs": {
            "SW1": "interface FastEthernet0/12\n switchport mode access\n switchport access vlan 1"
        }
    }
]


def export_cases_to_csv(filepath: str = "data/cases.csv") -> str:
    """Exports all 30 cases to CSV format."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fieldnames = [
        "case_id", "title", "category", "description", "symptoms",
        "target_rule", "osi_layer", "expected_root_cause", "expected_fix",
        "network_topology", "raw_configs"
    ]
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for case in CASES_DATA:
            row = case.copy()
            row["network_topology"] = json.dumps(case.get("network_topology", {}))
            row["raw_configs"] = json.dumps(case.get("raw_configs", {}))
            writer.writerow(row)
    return filepath
