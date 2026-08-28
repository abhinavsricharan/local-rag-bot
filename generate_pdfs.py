import os
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

def create_pdf(filename, title, content_lines):
    path = os.path.join("data", filename)
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, title)
    
    c.setFont("Helvetica", 12)
    y_position = height - 80
    for line in content_lines:
        c.drawString(50, y_position, line)
        y_position -= 20
        if y_position < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 50
            
    c.save()
    print(f"Generated {path}")

doc1_content = [
    "1. Introduction:",
    "This document outlines the cybersecurity guidelines for all UPSC web portals managed by NIC.",
    "All portals must implement TLS 1.3 for encryption.",
    "2. Access Control:",
    "Multi-factor authentication (MFA) is mandatory for all administrative access.",
    "Passwords must be at least 14 characters long and rotated every 90 days.",
    "3. Security Audits:",
    "Annual security audits are required for all UPSC IT infrastructure.",
    "Vulnerability scanning must be performed quarterly.",
    "4. Incident Response:",
    "Any security breach must be reported to the NIC CERT within 24 hours.",
    "System logs must be retained for a minimum of 1 year."
]

doc2_content = [
    "1. Overview:",
    "The e-Governance architecture for the UPSC IT wing ensures high availability and scalability.",
    "2. Cloud Infrastructure:",
    "Applications are hosted on the NIC National Cloud (MeghRaj).",
    "Auto-scaling groups are configured to handle peak loads during exam result declarations.",
    "3. Database Architecture:",
    "PostgreSQL is the primary relational database system.",
    "Database replicas are maintained across two distinct availability zones for disaster recovery.",
    "4. API Integrations:",
    "RESTful APIs are used for communication between microservices.",
    "API gateways handle rate limiting and request validation."
]

if __name__ == "__main__":
    create_pdf("nic_cybersecurity_guidelines.pdf", "NIC Cybersecurity Guidelines for UPSC Portals", doc1_content)
    create_pdf("upsc_egov_architecture.pdf", "e-Governance Architecture for UPSC IT Wing", doc2_content)
