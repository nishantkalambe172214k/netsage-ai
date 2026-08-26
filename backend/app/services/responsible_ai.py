from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.case import Case
from app.models.diagnosis import Diagnosis
from app.models.review import Review
from app.models.verification_result import VerificationResult


RESPONSIBLE_AI_SEED_DATA = [
    {
        "case_id_str": "CASE-DHCP-009",
        "reviewer_name": "Sr. Network Engineer Elena",
        "decision": "EDITED",
        "why_ai_incorrect": "AI diagnosed a local Layer 2 DHCP snooping blocking issue, failing to recognize that DHCP broadcast packets cannot cross the branch router boundary without an IP Helper-Address configured on the sub-interface.",
        "review_notes": "Corrected root cause from Layer 2 DHCP snooping to Layer 3 DHCP Relay. Centralized HQ DHCP server requires 'ip helper-address 10.0.0.50' on branch sub-interface Gi0/0.10.",
        "original_diagnosis": {
            "root_cause": "Switch port dropping DHCP Discover broadcasts due to untrusted DHCP snooping configuration.",
            "confidence": 0.82,
            "osi_layer": "Layer 2 - Data Link",
            "evidence": ["Client received APIPA 169.254.10.5", "No DHCP Offer returned"],
            "next_command": "show ip dhcp snooping",
            "fix_steps": ["Enable ip dhcp snooping trust on switch uplinks."]
        },
        "corrected_diagnosis": {
            "root_cause": "Missing DHCP Relay agent configuration: Branch router sub-interface Gi0/0.10 lacks 'ip helper-address 10.0.0.50' to forward client broadcasts across the WAN to HQ.",
            "confidence": 0.99,
            "osi_layer": "Layer 3 - Network",
            "evidence": [
                "Clients in VLAN 10 receive APIPA 169.254.x.x addresses",
                "HQ DHCP server is located at remote IP 10.0.0.50 across router boundary",
                "Branch router Gi0/0.10 has no ip helper-address defined"
            ],
            "next_command": "show running-config interface GigabitEthernet0/0.10",
            "fix_steps": [
                "interface GigabitEthernet0/0.10",
                "ip helper-address 10.0.0.50",
                "exit"
            ]
        },
        "verification_summary": "Client PC1 renewed DHCP lease and successfully received IP 192.168.10.15 from HQ server.",
        "verification_status": "PASSED"
    },
    {
        "case_id_str": "CASE-ROUTE-018",
        "reviewer_name": "Lead Network Architect Marcus",
        "decision": "EDITED",
        "why_ai_incorrect": "AI incorrectly attributed the OSPF neighbor failure to an OSPF network command subnet mismatch rather than an interface MTU disparity halting Database Description (DBD) packet exchange.",
        "review_notes": "Corrected diagnosis to MTU mismatch on link. R2 has MTU 1400 while R1 has MTU 1500; during DBD packet exchange OSPF gets stuck in EXSTART state.",
        "original_diagnosis": {
            "root_cause": "OSPF network command area or wildcard mask mismatch in router ospf configuration block.",
            "confidence": 0.79,
            "osi_layer": "Layer 3 - Network",
            "evidence": ["OSPF neighbor relationship down", "network 10.0.0.0 statement present"],
            "next_command": "show ip protocols",
            "fix_steps": ["Reconfigure OSPF network statements on both routers."]
        },
        "corrected_diagnosis": {
            "root_cause": "Interface MTU mismatch on transit link: R2 interface Gi0/0 is set to MTU 1400 while R1 is set to MTU 1500, preventing OSPF Database Description (DBD) negotiation from advancing past EXSTART.",
            "confidence": 0.98,
            "osi_layer": "Layer 3 - Network",
            "evidence": [
                "show ip ospf neighbor shows state EXSTART/EXCHANGE",
                "R1 Gi0/0 MTU is 1500",
                "R2 Gi0/0 MTU is 1400"
            ],
            "next_command": "show ip ospf neighbor GigabitEthernet0/0",
            "fix_steps": [
                "interface GigabitEthernet0/0",
                "ip mtu 1500",
                "exit"
            ]
        },
        "verification_summary": "OSPF neighbor state transitioned from EXSTART to FULL. Routing tables populated.",
        "verification_status": "PASSED"
    },
    {
        "case_id_str": "CASE-ACL-022",
        "reviewer_name": "Security & NetEng Specialist Rachel",
        "decision": "EDITED",
        "why_ai_incorrect": "AI suggested deleting the extended ACL 101 and replacing it with a broad permit rule, ignoring that the only defect was applying the ACL in the 'in' direction instead of 'out' on the router interface.",
        "review_notes": "Modified AI fix from destructive ACL removal to correcting the 'ip access-group 101' direction binding on interface Gi0/0.",
        "original_diagnosis": {
            "root_cause": "Extended ACL 101 is corrupt or blocking valid HTTP traffic; recommend removing and rebuilding ACL.",
            "confidence": 0.74,
            "osi_layer": "Layer 4 - Transport",
            "evidence": ["HTTP traffic blocked", "ACL match count increasing"],
            "next_command": "show access-lists 101",
            "fix_steps": ["no access-list 101", "access-list 101 permit ip any any"]
        },
        "corrected_diagnosis": {
            "root_cause": "Incorrect ACL interface direction binding: Extended ACL 101 contains valid rule filtering source IP 10.0.0.0, but was applied 'in' on internal interface Gi0/0 instead of 'out'.",
            "confidence": 0.97,
            "osi_layer": "Layer 4 - Transport",
            "evidence": [
                "ACL 101 permits tcp 10.0.0.0 0.255.255.255 any eq 80",
                "Applied on Gi0/0 with 'ip access-group 101 in', checking wrong packet direction"
            ],
            "next_command": "show ip interface GigabitEthernet0/0",
            "fix_steps": [
                "interface GigabitEthernet0/0",
                "no ip access-group 101 in",
                "ip access-group 101 out",
                "exit"
            ]
        },
        "verification_summary": "Client HTTP GET requests to Web Server on port 80 now succeed without dropping non-HTTP traffic.",
        "verification_status": "PASSED"
    },
    {
        "case_id_str": "CASE-VLAN-003",
        "reviewer_name": "Infrastructure Engineer David",
        "decision": "EDITED",
        "why_ai_incorrect": "AI recommended applying 'switchport trunk allowed vlan all' across inter-switch uplinks, which violates least-privilege security policy and enterprise VLAN pruning guidelines.",
        "review_notes": "Corrected AI fix to explicitly add only VLAN 50 to the trunk allowed list ('switchport trunk allowed vlan add 50') preserving VLAN isolation.",
        "original_diagnosis": {
            "root_cause": "Trunk port restriction blocking VLAN 50; remove all trunk allowed filters to allow all VLANs.",
            "confidence": 0.80,
            "osi_layer": "Layer 2 - Data Link",
            "evidence": ["VLAN 50 not in allowed list 10,20"],
            "next_command": "show interfaces trunk",
            "fix_steps": ["switchport trunk allowed vlan all"]
        },
        "corrected_diagnosis": {
            "root_cause": "Trunk port VLAN allowed list pruning: Uplink Gi0/2 specifies 'allowed vlan 10,20', omitting newly provisioned Core Server VLAN 50.",
            "confidence": 0.98,
            "osi_layer": "Layer 2 - Data Link",
            "evidence": [
                "VLAN 50 created on SW1 and SW2",
                "Gi0/2 trunk allowed list only permits VLANs 10,20",
                "Frames with tag 50 are dropped at switch ingress"
            ],
            "next_command": "show interfaces GigabitEthernet0/2 trunk",
            "fix_steps": [
                "interface GigabitEthernet0/2",
                "switchport trunk allowed vlan add 50",
                "exit"
            ]
        },
        "verification_summary": "VLAN 50 unicast and broadcast traffic flows across SW1-SW2 uplink. Other unapproved VLANs remain pruned.",
        "verification_status": "PASSED"
    },
    {
        "case_id_str": "CASE-NAT-026",
        "reviewer_name": "Core NetOps Engineer Priya",
        "decision": "EDITED",
        "why_ai_incorrect": "AI diagnosed that the NAT pool IP capacity was exhausted, overlooking that ACL 1 had an inverted wildcard mask (255.255.255.0 instead of 0.0.0.255), causing zero outbound packets to match the translation criteria.",
        "review_notes": "Corrected root cause to wildcard mask inversion in NAT match ACL. Replaced 'permit 192.168.1.0 255.255.255.0' with 'permit 192.168.1.0 0.0.0.255'.",
        "original_diagnosis": {
            "root_cause": "NAT overload translation pool exhausted or public interface IP address unavailable.",
            "confidence": 0.76,
            "osi_layer": "Layer 3 - Network",
            "evidence": ["show ip nat translations is empty", "NAT overload enabled"],
            "next_command": "show ip nat statistics",
            "fix_steps": ["clear ip nat translation *", "expand NAT pool range"]
        },
        "corrected_diagnosis": {
            "root_cause": "Wildcard mask inversion in NAT ACL: Access-list 1 used subnet mask '255.255.255.0' instead of inverse wildcard mask '0.0.0.255', causing NAT engine to never match LAN host packets.",
            "confidence": 0.99,
            "osi_layer": "Layer 3 - Network",
            "evidence": [
                "ACL 1 configured as: access-list 1 permit 192.168.1.0 255.255.255.0",
                "show ip nat statistics displays 0 hits and 0 active translations",
                "Outbound packets exit untranslated and are dropped by upstream ISP"
            ],
            "next_command": "show access-lists 1",
            "fix_steps": [
                "no access-list 1",
                "access-list 1 permit 192.168.1.0 0.0.0.255"
            ]
        },
        "verification_summary": "show ip nat translations now confirms active translation sessions for internal hosts reaching external IPs.",
        "verification_status": "PASSED"
    }
]


def seed_responsible_ai_examples(db: Session) -> int:
    """Seeds the 5 authentic human-corrected AI troubleshooting cases into the database."""
    seeded = 0
    for item in RESPONSIBLE_AI_SEED_DATA:
        case = db.query(Case).filter(Case.case_id == item["case_id_str"]).first()
        if not case:
            continue

        # Check if review already exists for this case
        existing_review = db.query(Review).filter(
            Review.case_id == case.id,
            Review.decision == "EDITED"
        ).first()

        if existing_review:
            # Update review fields
            existing_review.why_ai_incorrect = item["why_ai_incorrect"]
            existing_review.review_notes = item["review_notes"]
            existing_review.original_diagnosis = item["original_diagnosis"]
            existing_review.corrected_diagnosis = item["corrected_diagnosis"]
            continue

        # Create or fetch Diagnosis
        diag = db.query(Diagnosis).filter(Diagnosis.case_id == case.id).first()
        if not diag:
            diag = Diagnosis(
                case_id=case.id,
                summary=f"Initial automated diagnosis for {case.case_id}",
                root_cause=item["original_diagnosis"]["root_cause"],
                confidence_score=item["original_diagnosis"]["confidence"],
                evidence=item["original_diagnosis"]["evidence"],
                osi_layer=item["original_diagnosis"]["osi_layer"],
                next_command=item["original_diagnosis"]["next_command"],
                fix_steps=item["original_diagnosis"]["fix_steps"],
                suggested_commands=[{"device": "R1", "commands": item["original_diagnosis"]["fix_steps"]}],
                model_name="mock-ai-engine"
            )
            db.add(diag)
            db.commit()
            db.refresh(diag)

        # Create EDITED Review record
        review = Review(
            case_id=case.id,
            diagnosis_id=diag.id,
            reviewer_name=item["reviewer_name"],
            decision="EDITED",
            original_diagnosis=item["original_diagnosis"],
            corrected_diagnosis=item["corrected_diagnosis"],
            review_notes=item["review_notes"],
            why_ai_incorrect=item["why_ai_incorrect"],
            modified_commands=[{"device": "R1", "commands": item["corrected_diagnosis"]["fix_steps"]}]
        )
        db.add(review)
        case.status = "APPROVED"
        db.commit()
        db.refresh(review)

        # Add Verification Result
        vr = db.query(VerificationResult).filter(VerificationResult.case_id == case.id).first()
        if not vr:
            vr = VerificationResult(
                case_id=case.id,
                review_id=review.id,
                status=item["verification_status"],
                test_summary=item["verification_summary"],
                notes="Verified post-remediation in Packet Tracer simulator.",
                verification_evidence={"verified_by": item["reviewer_name"], "status": "PASSED"}
            )
            db.add(vr)
            case.status = "RESOLVED"
            db.commit()

        seeded += 1

    return seeded


def get_responsible_ai_records(db: Session) -> List[Dict[str, Any]]:
    """Fetches all human-corrected (EDITED or REJECTED) review cases for the Responsible AI view."""
    reviews = db.query(Review).filter(Review.decision.in_(["EDITED", "REJECTED"])).order_by(Review.reviewed_at.desc()).all()
    records = []

    for r in reviews:
        case = r.case
        case_id = case.case_id if case else f"CASE-{r.case_id}"
        title = case.title if case else "Network Troubleshooting Case"
        
        orig = r.original_diagnosis or {}
        corr = r.corrected_diagnosis or {}

        records.append({
            "review_id": r.id,
            "case_id": case_id,
            "case_title": title,
            "reviewer_name": r.reviewer_name,
            "decision": r.decision,
            "ai_diagnosis": {
                "root_cause": orig.get("root_cause", r.diagnosis.root_cause if r.diagnosis else "Automated analysis"),
                "confidence": orig.get("confidence", r.diagnosis.confidence_score if r.diagnosis else 0.8),
                "osi_layer": orig.get("osi_layer", r.diagnosis.osi_layer if r.diagnosis else "Layer 3 - Network"),
                "next_command": orig.get("next_command", r.diagnosis.next_command if r.diagnosis else "show run"),
                "fix_steps": orig.get("fix_steps", r.diagnosis.fix_steps if r.diagnosis else [])
            },
            "human_correction": {
                "root_cause": corr.get("root_cause", r.review_notes),
                "confidence": corr.get("confidence", 0.98),
                "osi_layer": corr.get("osi_layer", "Layer 3 - Network"),
                "next_command": corr.get("next_command", "show running-config"),
                "fix_steps": corr.get("fix_steps", [])
            },
            "why_ai_incorrect": r.why_ai_incorrect or r.rejection_reason or "Reviewer identified parameter misalignment in AI recommendation.",
            "reviewer_notes": r.review_notes or r.rejection_reason or "Human correction applied.",
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None
        })

    return records
