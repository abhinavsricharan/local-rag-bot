"""
Utility script to auto-generate 3 sample UPSC IT Wing PDF documents.
Uses fpdf2 to create mock government IT policy PDFs in the data/ directory.
PDFs are only generated if they do not already exist.
"""

import os
from fpdf import FPDF

DATA_DIR = "data"

SAMPLE_PDFS = {
    "nic_cybersecurity_guidelines.pdf": {
        "title": "NIC Cybersecurity Guidelines for UPSC Portals",
        "body": (
            "1. Introduction:\n"
            "This document outlines the cybersecurity guidelines for all UPSC web portals\n"
            "managed by NIC. All portals must implement TLS 1.3 for encryption.\n"
            "\n"
            "2. Access Control:\n"
            "Multi-factor authentication (MFA) is mandatory for all administrative access.\n"
            "Passwords must be at least 14 characters long and rotated every 90 days.\n"
            "Session tokens must expire after 30 minutes of inactivity.\n"
            "Service accounts must use certificate-based authentication.\n"
            "\n"
            "3. Security Audits:\n"
            "Annual security audits are required for all UPSC IT infrastructure.\n"
            "Vulnerability scanning must be performed quarterly.\n"
            "Penetration testing must be conducted by CERT-In empanelled auditors.\n"
            "Audit reports must be submitted to the UPSC Secretary within 30 days.\n"
            "\n"
            "4. Incident Response:\n"
            "Any security breach must be reported to the NIC CERT within 24 hours.\n"
            "System logs must be retained for a minimum of 1 year.\n"
            "A dedicated incident response team must be available 24/7 during examination periods.\n"
            "Post-incident forensic analysis must be completed within 72 hours.\n"
            "\n"
            "5. Network Security:\n"
            "All UPSC portals must deploy Web Application Firewalls (WAF).\n"
            "Intrusion Detection Systems (IDS) must be operational 24/7.\n"
            "VPN access is mandatory for all remote administrative connections.\n"
            "Network segmentation must isolate examination systems from public-facing portals.\n"
            "DDoS mitigation services must be active during result declaration periods.\n"
            "\n"
            "6. Data Protection:\n"
            "All candidate personal data must be encrypted at rest using AES-256.\n"
            "Cross-border data transfer is strictly prohibited.\n"
            "Data masking must be applied in non-production environments.\n"
            "Privacy impact assessments are required before deploying new systems.\n"
        ),
    },
    "upsc_egov_architecture.pdf": {
        "title": "e-Governance Architecture for UPSC IT Wing",
        "body": (
            "1. Overview:\n"
            "The UPSC IT Wing manages all digital infrastructure for examination,\n"
            "recruitment, and administrative processes. This document describes the\n"
            "technical architecture powering UPSC digital services.\n"
            "\n"
            "2. Cloud Infrastructure:\n"
            "All UPSC portals are hosted on the NIC National Cloud (MeghRaj).\n"
            "Auto-scaling groups handle peak loads during exam result declarations.\n"
            "The infrastructure spans two primary data centers in Delhi and Hyderabad.\n"
            "Container orchestration is managed through Kubernetes clusters.\n"
            "\n"
            "3. Database Architecture:\n"
            "Primary databases run PostgreSQL 15 on dedicated NIC servers.\n"
            "Read replicas are distributed across three availability zones.\n"
            "Redis clusters provide caching for frequently accessed data.\n"
            "MongoDB is used for document storage of candidate applications.\n"
            "\n"
            "4. Application Stack:\n"
            "Frontend: React-based Single Page Applications served via NIC CDN.\n"
            "Backend: Java Spring Boot microservices with REST APIs.\n"
            "Message Queue: Apache Kafka for asynchronous event processing.\n"
            "API Gateway: Kong handles rate limiting and authentication.\n"
            "Monitoring: Prometheus and Grafana for system observability.\n"
            "\n"
            "5. Disaster Recovery:\n"
            "RPO (Recovery Point Objective): 1 hour.\n"
            "RTO (Recovery Time Objective): 4 hours.\n"
            "Daily backups stored in geographically separated NIC data centers.\n"
            "Automated failover between Delhi and Hyderabad data centers.\n"
            "Disaster recovery drills are conducted quarterly.\n"
            "\n"
            "6. Integration Services:\n"
            "UPSC systems integrate with Aadhaar for candidate identity verification.\n"
            "Payment gateway integration with SBI and RBI payment systems.\n"
            "SMS and email notification services through NIC messaging infrastructure.\n"
            "DigiLocker integration for certificate verification.\n"
        ),
    },
    "upsc_data_management_policy.pdf": {
        "title": "UPSC IT Wing Data Management and Backup Policy",
        "body": (
            "1. Data Classification:\n"
            "All data handled by UPSC IT Wing is classified into four categories:\n"
            "Public, Internal, Confidential, and Restricted.\n"
            "Examination question papers are classified as Restricted until the exam date.\n"
            "Candidate personal information is classified as Confidential.\n"
            "Published results and notifications are classified as Public.\n"
            "\n"
            "2. Data Retention:\n"
            "Candidate application records must be retained for 7 years.\n"
            "Examination results are archived permanently in NIC cold storage.\n"
            "System logs and audit trails must be maintained for a minimum of 3 years.\n"
            "Financial transaction records must be retained for 10 years.\n"
            "Email communications related to examinations are retained for 5 years.\n"
            "\n"
            "3. Backup Schedule:\n"
            "Full database backups are performed daily at 02:00 IST.\n"
            "Incremental backups run every 4 hours.\n"
            "Transaction log backups occur every 15 minutes during business hours.\n"
            "Backup verification tests are conducted weekly.\n"
            "Backup media is rotated on a 30-day cycle.\n"
            "\n"
            "4. Data Encryption:\n"
            "All data at rest must be encrypted using AES-256.\n"
            "All data in transit must use TLS 1.3 or higher.\n"
            "Encryption keys are managed through NIC Key Management Service (KMS).\n"
            "Key rotation must occur every 90 days.\n"
            "Hardware Security Modules (HSM) are used for examination-related encryption.\n"
            "\n"
            "5. Access Controls:\n"
            "Role-based access control (RBAC) is enforced across all data systems.\n"
            "Data access requires approval from the designated Data Protection Officer.\n"
            "All access events are logged and auditable.\n"
            "Privileged access reviews are conducted monthly.\n"
            "Separation of duties is enforced for examination data handling.\n"
            "\n"
            "6. Data Disposal:\n"
            "Secure data disposal must follow NIC guidelines for media sanitization.\n"
            "Digital data must be wiped using DoD 5220.22-M standard.\n"
            "Physical media destruction must be witnessed and documented.\n"
            "Disposal certificates must be maintained for audit purposes.\n"
        ),
    },
}


def generate_sample_pdfs():
    """Generate sample PDFs if they do not exist in the data directory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    generated = []

    for filename, content in SAMPLE_PDFS.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            page_width = pdf.w - pdf.l_margin - pdf.r_margin

            # Title
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(page_width, 10, content["title"])
            pdf.ln(8)

            # Body
            pdf.set_font("Helvetica", size=11)
            for line in content["body"].split("\n"):
                stripped = line.strip()
                if not stripped:
                    pdf.ln(4)
                    continue
                # Section headers (lines ending with colon and starting with a digit)
                if stripped and stripped[0].isdigit() and stripped.endswith(":"):
                    pdf.ln(2)
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.multi_cell(page_width, 7, stripped)
                    pdf.set_font("Helvetica", size=11)
                else:
                    pdf.multi_cell(page_width, 7, stripped)

            pdf.output(filepath)
            generated.append(filename)
            print(f"Generated: {filepath}")

    return generated


if __name__ == "__main__":
    result = generate_sample_pdfs()
    if result:
        print(f"\nTotal generated: {len(result)} PDF(s)")
    else:
        print("All sample PDFs already exist. No files generated.")
