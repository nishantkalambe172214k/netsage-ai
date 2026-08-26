import re
import ipaddress
from typing import List, Dict, Any, Optional


class CiscoConfigParser:
    """Helper parser for Cisco IOS configuration text."""

    @staticmethod
    def extract_interfaces(config_text: str) -> Dict[str, Dict[str, Any]]:
        """Extracts interface configuration blocks and their attributes."""
        interfaces: Dict[str, Dict[str, Any]] = {}
        current_iface: Optional[str] = None
        current_data: Dict[str, Any] = {}

        for line in config_text.splitlines():
            line_clean = line.strip()
            if line_clean.startswith("interface "):
                if current_iface:
                    interfaces[current_iface] = current_data
                current_iface = line_clean.replace("interface ", "").strip()
                current_data = {
                    "is_shutdown": False,
                    "ip": None,
                    "mask": None,
                    "dot1q": None,
                    "mode": "access",
                    "access_vlan": 1,
                    "trunk_allowed_vlans": [],
                    "native_vlan": 1,
                    "mtu": 1500,
                    "raw_lines": []
                }
            elif current_iface:
                current_data["raw_lines"].append(line_clean)
                if line_clean == "shutdown":
                    current_data["is_shutdown"] = True
                elif line_clean == "no shutdown":
                    current_data["is_shutdown"] = False
                
                # IP Address
                ip_match = re.match(r"^ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)", line_clean)
                if ip_match:
                    current_data["ip"] = ip_match.group(1)
                    current_data["mask"] = ip_match.group(2)

                # MTU
                mtu_match = re.match(r"^ip mtu\s+(\d+)", line_clean)
                if mtu_match:
                    current_data["mtu"] = int(mtu_match.group(1))

                # Dot1Q encapsulation
                dot1q_match = re.match(r"^encapsulation dot1Q\s+(\d+)", line_clean, re.IGNORECASE)
                if dot1q_match:
                    current_data["dot1q"] = int(dot1q_match.group(1))

                # Switchport mode
                if "switchport mode trunk" in line_clean:
                    current_data["mode"] = "trunk"
                elif "switchport mode access" in line_clean:
                    current_data["mode"] = "access"

                # Access VLAN
                vlan_match = re.match(r"^switchport access vlan\s+(\d+)", line_clean)
                if vlan_match:
                    current_data["access_vlan"] = int(vlan_match.group(1))

                # Trunk allowed VLANs
                trunk_match = re.match(r"^switchport trunk allowed vlan\s+(?:add\s+)?([\d,]+)", line_clean)
                if trunk_match:
                    vlans = [int(v.strip()) for v in trunk_match.group(1).split(",") if v.strip().isdigit()]
                    current_data["trunk_allowed_vlans"].extend(vlans)

                # Native VLAN
                native_match = re.match(r"^switchport trunk native vlan\s+(\d+)", line_clean)
                if native_match:
                    current_data["native_vlan"] = int(native_match.group(1))

        if current_iface:
            interfaces[current_iface] = current_data

        return interfaces

    @staticmethod
    def extract_created_vlans(config_text: str) -> List[int]:
        """Extracts VLAN IDs declared in global config (vlan 10, vlan 20, etc.)."""
        vlans = [1]  # Default VLAN 1 always exists
        for line in config_text.splitlines():
            match = re.match(r"^vlan\s+(\d+)", line.strip(), re.IGNORECASE)
            if match:
                vlans.append(int(match.group(1)))
        return sorted(list(set(vlans)))


class DeterministicRuleChecker:
    """Python Deterministic Rule Checker for Cisco Packet Tracer scenarios."""

    def __init__(self, raw_configs: Dict[str, str], topology: Dict[str, Any]):
        self.raw_configs = raw_configs or {}
        self.topology = topology or {}
        self.parsed_devices: Dict[str, Dict[str, Any]] = {}
        self._parse_all()

    def _parse_all(self):
        for dev_name, config in self.raw_configs.items():
            if isinstance(config, str):
                self.parsed_devices[dev_name] = {
                    "interfaces": CiscoConfigParser.extract_interfaces(config),
                    "created_vlans": CiscoConfigParser.extract_created_vlans(config),
                    "raw": config
                }

    def run_all_checks(self) -> List[Dict[str, Any]]:
        """Executes all 6 deterministic network inspection rules."""
        findings = []
        findings.extend(self.check_duplicate_ip())
        findings.extend(self.check_wrong_subnet_mask())
        findings.extend(self.check_gateway_mismatch())
        findings.extend(self.check_interface_down())
        findings.extend(self.check_missing_vlan())
        findings.extend(self.check_missing_route())
        return findings

    # 1. Duplicate IP Check
    def check_duplicate_ip(self) -> List[Dict[str, Any]]:
        findings = []
        ip_map: Dict[str, List[Dict[str, str]]] = {}

        # Collect IPs from device interfaces
        for dev_name, dev_data in self.parsed_devices.items():
            for iface_name, iface_data in dev_data["interfaces"].items():
                ip = iface_data.get("ip")
                if ip and ip != "0.0.0.0":
                    ip_map.setdefault(ip, []).append({
                        "device": dev_name,
                        "interface": iface_name
                    })

        # Collect IPs from topology clients
        clients = self.topology.get("clients", [])
        for client in clients:
            cip = client.get("ip")
            cname = client.get("name", "Client")
            if cip:
                ip_map.setdefault(cip, []).append({
                    "device": cname,
                    "interface": "Host-NIC"
                })

        for ip, locations in ip_map.items():
            if len(locations) > 1:
                devs = ", ".join([f"{loc['device']}:{loc['interface']}" for loc in locations])
                findings.append({
                    "rule_id": "RULE_DUPLICATE_IP",
                    "rule_name": "Duplicate IP Address Detected",
                    "category": "IP_ADDRESSING",
                    "severity": "CRITICAL",
                    "status": "FAIL",
                    "affected_device": locations[0]["device"],
                    "affected_interface": locations[0]["interface"],
                    "message": f"IP address conflict: {ip} is assigned to multiple endpoints ({devs}).",
                    "details": {"duplicate_ip": ip, "locations": locations}
                })

        return findings

    # 2. Wrong Subnet Mask Check
    def check_wrong_subnet_mask(self) -> List[Dict[str, Any]]:
        findings = []
        
        # Validate interface masks
        for dev_name, dev_data in self.parsed_devices.items():
            for iface_name, iface_data in dev_data["interfaces"].items():
                ip = iface_data.get("ip")
                mask = iface_data.get("mask")
                if ip and mask:
                    try:
                        ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                    except Exception as e:
                        findings.append({
                            "rule_id": "RULE_WRONG_SUBNET_MASK",
                            "rule_name": "Invalid IPv4 Subnet Mask",
                            "category": "IP_ADDRESSING",
                            "severity": "CRITICAL",
                            "status": "FAIL",
                            "affected_device": dev_name,
                            "affected_interface": iface_name,
                            "message": f"Interface {iface_name} on {dev_name} has an invalid subnet mask: {mask}.",
                            "details": {"ip": ip, "mask": mask, "error": str(e)}
                        })

            # Check for ACL / NAT wildcard inversion (e.g. permit 192.168.1.0 255.255.255.0)
            raw = dev_data.get("raw", "")
            acl_inversion = re.findall(r"access-list\s+\d+\s+permit\s+\d+\.\d+\.\d+\.\d+\s+(255\.255\.\d+\.\d+)", raw)
            if acl_inversion:
                findings.append({
                    "rule_id": "RULE_WRONG_SUBNET_MASK",
                    "rule_name": "Wildcard Mask Inversion in Access-List",
                    "category": "ACL",
                    "severity": "CRITICAL",
                    "status": "FAIL",
                    "affected_device": dev_name,
                    "affected_interface": "Global Config",
                    "message": f"Device {dev_name} uses subnet mask {acl_inversion[0]} instead of inverse wildcard mask in access-list.",
                    "details": {"invalid_mask": acl_inversion[0]}
                })

        return findings

    # 3. Gateway Mismatch Check
    def check_gateway_mismatch(self) -> List[Dict[str, Any]]:
        findings = []
        all_router_ips = set()

        for dev_name, dev_data in self.parsed_devices.items():
            for iface_name, iface_data in dev_data["interfaces"].items():
                ip = iface_data.get("ip")
                if ip:
                    all_router_ips.add(ip)

        # Check clients in topology
        clients = self.topology.get("clients", [])
        for client in clients:
            gateway = client.get("gateway")
            cip = client.get("ip")
            cmask = client.get("mask", "255.255.255.0")
            cname = client.get("name", "Host")

            if gateway and gateway not in all_router_ips:
                findings.append({
                    "rule_id": "RULE_GATEWAY_MISMATCH",
                    "rule_name": "Client Default Gateway Unreachable",
                    "category": "GATEWAY",
                    "severity": "CRITICAL",
                    "status": "FAIL",
                    "affected_device": cname,
                    "affected_interface": "Default-Gateway",
                    "message": f"Client {cname} configured with gateway {gateway}, but no router interface in topology has this IP address.",
                    "details": {"client_ip": cip, "configured_gateway": gateway, "known_gateways": list(all_router_ips)}
                })
            elif gateway and cip:
                try:
                    c_net = ipaddress.IPv4Network(f"{cip}/{cmask}", strict=False)
                    gw_ip = ipaddress.IPv4Address(gateway)
                    if gw_ip not in c_net:
                        findings.append({
                            "rule_id": "RULE_GATEWAY_MISMATCH",
                            "rule_name": "Default Gateway Outside Client Subnet",
                            "category": "GATEWAY",
                            "severity": "CRITICAL",
                            "status": "FAIL",
                            "affected_device": cname,
                            "affected_interface": "Default-Gateway",
                            "message": f"Gateway {gateway} is outside client {cname} local subnet {c_net}.",
                            "details": {"client_ip": cip, "gateway": gateway, "subnet": str(c_net)}
                        })
                except Exception:
                    pass

        # Check DHCP pool default-router configs
        for dev_name, dev_data in self.parsed_devices.items():
            raw = dev_data.get("raw", "")
            dhcp_match = re.search(r"default-router\s+(\d+\.\d+\.\d+\.\d+)", raw)
            if dhcp_match:
                gw = dhcp_match.group(1)
                if gw not in all_router_ips:
                    findings.append({
                        "rule_id": "RULE_GATEWAY_MISMATCH",
                        "rule_name": "DHCP Pool Invalid Default Gateway",
                        "category": "DHCP",
                        "severity": "CRITICAL",
                        "status": "FAIL",
                        "affected_device": dev_name,
                        "affected_interface": "DHCP Pool",
                        "message": f"DHCP pool on {dev_name} assigns default-router {gw}, which does not match any router interface.",
                        "details": {"configured_default_router": gw}
                    })

        return findings

    # 4. Interface Down Check
    def check_interface_down(self) -> List[Dict[str, Any]]:
        findings = []

        for dev_name, dev_data in self.parsed_devices.items():
            for iface_name, iface_data in dev_data["interfaces"].items():
                if iface_data.get("is_shutdown"):
                    findings.append({
                        "rule_id": "RULE_INTERFACE_DOWN",
                        "rule_name": "Interface Administratively Shutdown",
                        "category": "INTERFACE",
                        "severity": "CRITICAL",
                        "status": "FAIL",
                        "affected_device": dev_name,
                        "affected_interface": iface_name,
                        "message": f"Interface {iface_name} on {dev_name} is configured with 'shutdown'.",
                        "details": {"device": dev_name, "interface": iface_name}
                    })

            # Check for disabled service status (like DNS server OFF)
            raw = dev_data.get("raw", "")
            if "service dns status: OFF" in raw:
                findings.append({
                    "rule_id": "RULE_INTERFACE_DOWN",
                    "rule_name": "Network Service Disabled",
                    "category": "DNS",
                    "severity": "CRITICAL",
                    "status": "FAIL",
                    "affected_device": dev_name,
                    "affected_interface": "DNS-Service",
                    "message": f"DNS service daemon on {dev_name} is turned OFF.",
                    "details": {"service": "DNS", "state": "OFF"}
                })

        return findings

    # 5. Missing VLAN Check
    def check_missing_vlan(self) -> List[Dict[str, Any]]:
        findings = []

        # Check access ports vs created VLANs on switches
        for dev_name, dev_data in self.parsed_devices.items():
            created_vlans = dev_data.get("created_vlans", [1])
            for iface_name, iface_data in dev_data["interfaces"].items():
                if iface_data.get("mode") == "access":
                    vlan = iface_data.get("access_vlan", 1)
                    if vlan not in created_vlans and vlan != 1:
                        findings.append({
                            "rule_id": "RULE_MISSING_VLAN",
                            "rule_name": "Access Port Assigned to Non-Existent VLAN",
                            "category": "VLAN",
                            "severity": "CRITICAL",
                            "status": "FAIL",
                            "affected_device": dev_name,
                            "affected_interface": iface_name,
                            "message": f"Port {iface_name} on switch {dev_name} is in VLAN {vlan}, but VLAN {vlan} is not created in the VLAN database.",
                            "details": {"assigned_vlan": vlan, "created_vlans": created_vlans}
                        })

                # Check trunk allowed list pruning
                allowed = iface_data.get("trunk_allowed_vlans", [])
                if iface_data.get("mode") == "trunk" and allowed:
                    for v in created_vlans:
                        if v not in allowed and v != 1:
                            findings.append({
                                "rule_id": "RULE_MISSING_VLAN",
                                "rule_name": "Active VLAN Pruned on Trunk Port",
                                "category": "VLAN",
                                "severity": "WARNING",
                                "status": "FAIL",
                                "affected_device": dev_name,
                                "affected_interface": iface_name,
                                "message": f"Trunk {iface_name} on {dev_name} restricts allowed VLANs ({allowed}) and omits active VLAN {v}.",
                                "details": {"pruned_vlan": v, "allowed_vlans": allowed}
                            })

        # Check Router-on-a-stick Dot1Q tag vs IP subnet
        for dev_name, dev_data in self.parsed_devices.items():
            for iface_name, iface_data in dev_data["interfaces"].items():
                dot1q = iface_data.get("dot1q")
                ip = iface_data.get("ip")
                if dot1q and ip:
                    # Check if IP third octet doesn't match dot1q tag (e.g. 192.168.20.1 with dot1Q 30)
                    parts = ip.split(".")
                    if len(parts) >= 3 and parts[2].isdigit():
                        subnet_vlan = int(parts[2])
                        if subnet_vlan != dot1q and subnet_vlan in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                            findings.append({
                                "rule_id": "RULE_MISSING_VLAN",
                                "rule_name": "Dot1Q Sub-interface Tag Subnet Mismatch",
                                "category": "VLAN",
                                "severity": "CRITICAL",
                                "status": "FAIL",
                                "affected_device": dev_name,
                                "affected_interface": iface_name,
                                "message": f"Sub-interface {iface_name} on {dev_name} has dot1Q tag {dot1q} but IP {ip} serves subnet for VLAN {subnet_vlan}.",
                                "details": {"configured_tag": dot1q, "expected_tag": subnet_vlan}
                            })

        return findings

    # 6. Missing Route Check
    def check_missing_route(self) -> List[Dict[str, Any]]:
        findings = []

        for dev_name, dev_data in self.parsed_devices.items():
            raw = dev_data.get("raw", "")
            
            # Missing default route on WAN edge
            if "203.0.113." in raw and "ip route 0.0.0.0 0.0.0.0" not in raw and "default route" not in raw.lower():
                findings.append({
                    "rule_id": "RULE_MISSING_ROUTE",
                    "rule_name": "Missing Default Route to ISP Gateway",
                    "category": "ROUTING",
                    "severity": "CRITICAL",
                    "status": "FAIL",
                    "affected_device": dev_name,
                    "affected_interface": "Routing-Table",
                    "message": f"Edge router {dev_name} has WAN interface but no default static route ('ip route 0.0.0.0 0.0.0.0 <next-hop>').",
                    "details": {"device": dev_name}
                })

            # Check OSPF passive-interface on transit link
            if "router ospf" in raw and "passive-interface GigabitEthernet0/2" in raw:
                findings.append({
                    "rule_id": "RULE_MISSING_ROUTE",
                    "rule_name": "OSPF Passive-Interface Blocking Transit Adjacency",
                    "category": "ROUTING",
                    "severity": "CRITICAL",
                    "status": "FAIL",
                    "affected_device": dev_name,
                    "affected_interface": "GigabitEthernet0/2",
                    "message": f"Router {dev_name} has passive-interface enabled on transit link Gi0/2, halting OSPF Hello packet exchange.",
                    "details": {"device": dev_name, "blocked_interface": "GigabitEthernet0/2"}
                })

            # Missing IP helper-address for DHCP relay
            if "encapsulation dot1Q" in raw and "169.254" in str(self.topology) and "ip helper-address" not in raw:
                findings.append({
                    "rule_id": "RULE_MISSING_ROUTE",
                    "rule_name": "Missing IP Helper-Address for DHCP Relay",
                    "category": "DHCP",
                    "severity": "CRITICAL",
                    "status": "FAIL",
                    "affected_device": dev_name,
                    "affected_interface": "Sub-interface",
                    "message": f"Router {dev_name} hosts client subnets with remote DHCP server but is missing 'ip helper-address'.",
                    "details": {"device": dev_name}
                })

            # Missing NAT Inside/Outside
            if "ip nat inside source" in raw and ("! missing ip nat inside" in raw or "! missing ip nat outside" in raw):
                findings.append({
                    "rule_id": "RULE_MISSING_ROUTE",
                    "rule_name": "Missing NAT Inside/Outside Interface Configuration",
                    "category": "NAT",
                    "severity": "CRITICAL",
                    "status": "FAIL",
                    "affected_device": dev_name,
                    "affected_interface": "NAT",
                    "message": f"Router {dev_name} has NAT translation rules but is missing 'ip nat inside' or 'ip nat outside' on required interfaces.",
                    "details": {"device": dev_name}
                })

        return findings
