import os
import hashlib
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

load_dotenv()

pdf_filename = "care_premier_health_shield_policy_wording.pdf"
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=letter,
    rightMargin=40,
    leftMargin=40,
    topMargin=40,
    bottomMargin=40
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=18,
    leading=22,
    textColor=colors.HexColor('#0F172A'),
    alignment=1
)

sub_style = ParagraphStyle(
    'DocSub',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=10,
    leading=14,
    textColor=colors.HexColor('#475569'),
    alignment=1
)

h1_style = ParagraphStyle(
    'SectionH1',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=12,
    leading=16,
    textColor=colors.HexColor('#1E3A8A'),
    spaceBefore=12,
    spaceAfter=6
)

body_style = ParagraphStyle(
    'BodyDark',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9,
    leading=13,
    textColor=colors.HexColor('#1E293B')
)

clause_style = ParagraphStyle(
    'Clause',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor('#334155')
)

elements = []

elements.append(Paragraph("CARE PREMIER HEALTH SHIELD", title_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("OFFICIAL STATUTORY POLICY WORDING & REGULATORY DISCLOSURE<br/>IRDAI Registration: IRDAI/NL-HLT/CPH/P-H/V.1/2026 • Policy Code: VG-HLT-01", sub_style))
elements.append(Spacer(1, 10))
elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=12))

# Policy Summary Table
summary_data = [
    [Paragraph("<b>Insurer:</b> Care Premier Health Assurance Ltd.", clause_style), Paragraph("<b>Category:</b> Hospitalization Inpatient", clause_style)],
    [Paragraph("<b>Maximum Limit:</b> ₹15,00,000 (Fifteen Lakhs)", clause_style), Paragraph("<b>Cashless Network:</b> 14,800+ Empanelled Hospitals", clause_style)],
    [Paragraph("<b>Initial Waiting Period:</b> 30 Days (Accident Day 1)", clause_style), Paragraph("<b>PED Waiting Period:</b> 24 Months Continuous", clause_style)],
]
t = Table(summary_data, colWidths=[260, 260])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
elements.append(t)
elements.append(Spacer(1, 12))

# Section 1
elements.append(Paragraph("SECTION 1: INPATIENT HOSPITALIZATION BENEFITS", h1_style))
elements.append(Paragraph("<b>Clause 1.1 — Room Rent & ICU Charges:</b> The policy provides coverage for inpatient room rent, boarding, nursing expenses, and Intensive Care Unit (ICU) charges up to the full Sum Insured of ₹15,00,000 per policy year, subject to standard room capping of ₹15,000/day.", clause_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("<b>Clause 1.2 — Pre & Post Hospitalization:</b> Medical expenses incurred 60 days prior to hospital admission and 90 days following formal discharge are eligible for cashless settlement or reimbursement upon submission of valid medical bills.", clause_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("<b>Clause 1.3 — Emergency Road Ambulance:</b> Incurred expenses for emergency road ambulance transportation to the nearest healthcare facility are payable up to ₹3,000 per hospitalization event.", clause_style))
elements.append(Spacer(1, 10))

# Section 2
elements.append(Paragraph("SECTION 2: MANDATORY STATUTORY WAITING PERIODS", h1_style))
elements.append(Paragraph("<b>Clause 2.1 — 30-Day Inception Waiting Period:</b> No claims for any illness or sickness shall be admissible during the first 30 days from policy commencement date, except for accidental injuries sustained subsequent to inception.", clause_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("<b>Clause 2.2 — Pre-Existing Disease (PED) 24-Month Waiting Period:</b> Any Pre-Existing Condition (including but not limited to Diabetes Mellitus, Hypertension, Chronic Kidney Disease, and Coronary Artery Disease) is covered ONLY after 24 months of continuous, uninterrupted coverage with the Insurer.", clause_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("<b>Clause 2.3 — Specific Ailment Exclusion Period:</b> Specific procedures including Cataract, Hernia, Hydrocele, Piles, Sinusitis, and Joint Replacement Surgeries carry a mandatory 24-month waiting period regardless of inception status.", clause_style))
elements.append(Spacer(1, 10))

# Section 3
elements.append(Paragraph("SECTION 3: PERMANENT POLICY EXCLUSIONS", h1_style))
elements.append(Paragraph("<b>Clause 3.1 — Cosmetic & Aesthetic Surgery:</b> Expenses incurred for cosmetic, aesthetic, laser skin, or elective body-contouring treatments are PERMANENTLY EXCLUDED, unless medically necessary as reconstructive surgery directly following accidental burns or trauma.", clause_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("<b>Clause 3.2 — Outpatient (OPD) Consultations:</b> Pure Outpatient Department (OPD) doctor consultations, prescription medicines, diagnostic evaluations, and dental examinations without mandatory minimum 24-hour inpatient hospital admission are STRICTLY EXCLUDED.", clause_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("<b>Clause 3.3 — Unproven & Experimental Treatments:</b> Unproven therapies, alternative non-allopathic treatments without hospitalization, and self-administered holistic cures are non-payable.", clause_style))
elements.append(Spacer(1, 14))

# Regulatory Footer
elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#94A3B8'), spaceAfter=8))
elements.append(Paragraph("<b>IRDAI Statutory Notice:</b> Tele-sales representations made by insurance agents must strictly align with the approved policy wordings above. Misrepresentation or false promise of immediate PED coverage or OPD reimbursement constitutes a regulatory offense under Insurance Act 1938.", sub_style))

doc.build(elements)
print(f"Generated PDF: {pdf_filename}")

with open(pdf_filename, "rb") as f:
    pdf_bytes = f.read()
    pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()

print(f"SHA-256 Checksum: {pdf_sha256}")

# Upload to Cloudinary
cloudinary_url = os.getenv("CLOUDINARY_URL")
cloud_name = "dbbxid1mk"
api_key = os.getenv("CLOUDINARY_API_KEY", "577978363655658")
api_secret = os.getenv("CLOUDINARY_API_SECRET", "qrtUhRAVxFbA2LHs2s_ghpIiNFM")

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret
)

upload_res = cloudinary.uploader.upload(
    pdf_filename,
    resource_type="raw",
    public_id="vachan/policies/care_premier_health_shield_v1",
    overwrite=True
)

secure_url = upload_res.get("secure_url")
print(f"Uploaded to Cloudinary: {secure_url}")

# Update DB
from migrate_via_neon_http import run_sql

run_sql(f"""
UPDATE policy_versions
SET document_storage_ref = '{secure_url}',
    document_checksum = '{pdf_sha256}'
WHERE id = 'b1111111-1111-1111-1111-111111111111';
""")

print("Neon Cloud PostgreSQL policy_versions updated with Cloudinary URL & SHA-256!")
