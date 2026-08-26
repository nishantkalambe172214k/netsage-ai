import pytest
from app.services.rule_engine import DeterministicRuleChecker, CiscoConfigParser


def test_rule_duplicate_ip():
    configs = {
        "R1": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n no shutdown",
        "SW1": "interface Vlan1\n ip address 192.168.1.1 255.255.255.0\n no shutdown"
    }
    topology = {"devices": ["R1", "SW1"], "clients": []}
    checker = DeterministicRuleChecker(configs, topology)
    findings = checker.check_duplicate_ip()
    
    assert len(findings) >= 1
    assert findings[0]["rule_id"] == "RULE_DUPLICATE_IP"
    assert "192.168.1.1" in findings[0]["message"]
    assert findings[0]["severity"] == "CRITICAL"


def test_rule_wrong_subnet_mask():
    configs = {
        "R1": "access-list 1 permit 192.168.1.0 255.255.255.0\ninterface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0"
    }
    topology = {}
    checker = DeterministicRuleChecker(configs, topology)
    findings = checker.check_wrong_subnet_mask()
    
    assert len(findings) >= 1
    assert findings[0]["rule_id"] == "RULE_WRONG_SUBNET_MASK"
    assert "access-list" in findings[0]["message"].lower()


def test_rule_gateway_mismatch():
    configs = {
        "R1": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n no shutdown"
    }
    topology = {
        "devices": ["R1", "PC1"],
        "clients": [{"name": "PC1", "ip": "192.168.1.50", "mask": "255.255.255.0", "gateway": "192.168.1.254"}]
    }
    checker = DeterministicRuleChecker(configs, topology)
    findings = checker.check_gateway_mismatch()
    
    assert len(findings) >= 1
    assert findings[0]["rule_id"] == "RULE_GATEWAY_MISMATCH"
    assert "192.168.1.254" in findings[0]["message"]


def test_rule_interface_down():
    configs = {
        "R2": "interface GigabitEthernet0/0\n ip address 10.1.1.1 255.255.255.0\n shutdown"
    }
    topology = {"devices": ["R2"]}
    checker = DeterministicRuleChecker(configs, topology)
    findings = checker.check_interface_down()
    
    assert len(findings) >= 1
    assert findings[0]["rule_id"] == "RULE_INTERFACE_DOWN"
    assert findings[0]["affected_device"] == "R2"
    assert findings[0]["affected_interface"] == "GigabitEthernet0/0"


def test_rule_missing_vlan():
    # Case: Access port assigned to VLAN 30, but VLAN 30 is not created in switch database
    configs = {
        "SW2": "vlan 10\n name HR\ninterface FastEthernet0/5\n switchport mode access\n switchport access vlan 30\n no shutdown"
    }
    topology = {"devices": ["SW2"]}
    checker = DeterministicRuleChecker(configs, topology)
    findings = checker.check_missing_vlan()
    
    assert len(findings) >= 1
    assert findings[0]["rule_id"] == "RULE_MISSING_VLAN"
    assert "VLAN 30" in findings[0]["message"]


def test_rule_missing_route():
    # Case: Missing default route on edge router with ISP interface
    configs = {
        "R1": "interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\ninterface GigabitEthernet0/1\n ip address 203.0.113.1 255.255.255.252"
    }
    topology = {"devices": ["R1"]}
    checker = DeterministicRuleChecker(configs, topology)
    findings = checker.check_missing_route()
    
    assert len(findings) >= 1
    assert findings[0]["rule_id"] == "RULE_MISSING_ROUTE"
    assert "default static route" in findings[0]["message"].lower()
