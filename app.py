import streamlit as st
import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- Databases & Configuration ---
japan_visa_rules = {
    "undergraduate": {
        "eligibility_criteria": {
            "academic_qualifications": {
                "minimum_requirement": "High School Graduation (or equivalent 12 years of formal education)",
                "documents_required": ["High School Diploma", "Academic Transcripts"]
            },
            "language_proficiency": {
                "japanese_taught_track": {
                    "exam": "JLPT",
                    "minimum_level": "N2"
                },
                "english_taught_track": {
                    "exams_accepted": ["IELTS", "TOEFL iBT"],
                    "minimum_scores": {
                        "IELTS": 5.5,
                        "TOEFL_iBT": 72
                    }
                }
            },
            "financial_solvency": {
                "minimum_annual_funding_jpy": 2000000
            }
        },
        "document_checklist": {
            "mandatory": [
                "Valid Passport",
                "Certificate of Eligibility (CoE) Application Form",
                "ID Photos (3cm x 4cm, recent)",
                "High School Diploma (translated to English or Japanese)",
                "Official High School Academic Transcripts",
                "Proof of Financial Solvency (e.g., bank statements showing >= 2,000,000 JPY)"
            ],
            "supporting": [
                "Letter of Financial Sponsorship (if funded by a sponsor)",
                "Sponsor's Proof of Income / Tax Certificates",
                "Certificate of Language Proficiency (JLPT, IELTS, or TOEFL certificate)",
                "Certificate of Relationship to Sponsor (e.g., family register, birth certificate)"
            ]
        }
    },
    "masters": {
        "eligibility_criteria": {
            "academic_qualifications": {
                "minimum_requirement": "Bachelor's Degree (or equivalent 16 years of formal education)",
                "documents_required": ["Bachelor's Degree Certificate", "University Transcripts"]
            },
            "language_proficiency": {
                "japanese_taught_track": {
                    "exam": "JLPT",
                    "minimum_level": "N2"
                },
                "english_taught_track": {
                    "exams_accepted": ["IELTS", "TOEFL iBT"],
                    "minimum_scores": {
                        "IELTS": 6.0,
                        "TOEFL_iBT": 80
                    }
                }
            },
            "financial_solvency": {
                "minimum_annual_funding_jpy": 2000000
            }
        },
        "document_checklist": {
            "mandatory": [
                "Valid Passport",
                "Certificate of Eligibility (CoE) Application Form",
                "ID Photos (3cm x 4cm, recent)",
                "Bachelor's Degree Graduation Certificate (translated to English or Japanese)",
                "Official University Transcripts (undergraduate level)",
                "Proof of Financial Solvency (e.g., bank statements showing >= 2,000,000 JPY)"
            ],
            "supporting": [
                "Research Proposal / Plan of Study in Japan",
                "Letter of Recommendation (from University Dean or Professor)",
                "Letter of Financial Sponsorship (if funded by a sponsor)",
                "Sponsor's Proof of Income / Tax Certificates",
                "Certificate of Language Proficiency (JLPT, IELTS, or TOEFL certificate)",
                "Certificate of Relationship to Sponsor (e.g., family register, birth certificate)"
            ]
        }
    }
}

japan_universities_db = [
    {
        "university": "University of Tokyo",
        "track": "undergraduate",
        "program_name": "PEAK (Programs in English at Komaba)",
        "language": "English",
        "min_requirements": {"IELTS": 7.0, "TOEFL_iBT": 100},
        "intakes": {
            "April": {"deadline": "Not Available"},
            "October": {"deadline": "November 24 (Prior Year)"}
        }
    },
    {
        "university": "University of Tokyo",
        "track": "masters",
        "program_name": "Graduate School of Science (GSC)",
        "language": "English",
        "min_requirements": {"IELTS": 6.5, "TOEFL_iBT": 90},
        "intakes": {
            "April": {"deadline": "October 31 (Prior Year)"},
            "October": {"deadline": "April 30"}
        }
    },
    {
        "university": "Kyoto University",
        "track": "undergraduate",
        "program_name": "iUP (International Undergraduate Program)",
        "language": "English",
        "min_requirements": {"IELTS": 6.0, "TOEFL_iBT": 80},
        "intakes": {
            "April": {"deadline": "Not Available"},
            "October": {"deadline": "December 5 (Prior Year)"}
        }
    },
    {
        "university": "Kyoto University",
        "track": "masters",
        "program_name": "Graduate School of Engineering (Japanese Track)",
        "language": "Japanese",
        "min_requirements": {"JLPT": "N1"},
        "intakes": {
            "April": {"deadline": "November 15 (Prior Year)"},
            "October": {"deadline": "May 10"}
        }
    },
    {
        "university": "Waseda University",
        "track": "undergraduate",
        "program_name": "School of Political Science and Economics (SPSE)",
        "language": "English",
        "min_requirements": {"IELTS": 6.5, "TOEFL_iBT": 95},
        "intakes": {
            "April": {"deadline": "Not Available"},
            "October": {"deadline": "February 25"}
        }
    },
    {
        "university": "Waseda University",
        "track": "masters",
        "program_name": "Graduate School of Asia-Pacific Studies (GSAPS)",
        "language": "English",
        "min_requirements": {"IELTS": 6.0, "TOEFL_iBT": 80},
        "intakes": {
            "April": {"deadline": "September 15 (Prior Year)"},
            "October": {"deadline": "March 31"}
        }
    },
    {
        "university": "Keio University",
        "track": "undergraduate",
        "program_name": "PEARL (Programme in Economics for All Alliance)",
        "language": "English",
        "min_requirements": {"IELTS": 6.5, "TOEFL_iBT": 95},
        "intakes": {
            "April": {"deadline": "Not Available"},
            "October": {"deadline": "January 28 (First Round)"}
        }
    }
]

# --- Evaluation, Matching and Planning Functions ---
def evaluate_visa_eligibility(profile, rules):
    track = profile.get('track', '').lower()
    if track not in rules:
        return {"eligible": False, "message": f"Invalid track '{track}'.", "criteria_results": {}}

    track_rules = rules[track]
    results = {
        "academic": {"status": False, "reason": ""},
        "language": {"status": False, "reason": ""},
        "financial": {"status": False, "reason": ""}
    }

    # Academic Rule
    required_years = 12 if track == "undergraduate" else 16
    actual_years = profile.get('education_years', 0)
    if actual_years >= required_years:
        results["academic"]["status"] = True
        results["academic"]["reason"] = f"Meets academic threshold of {required_years} years (has {actual_years} years)."
    else:
        results["academic"]["status"] = False
        results["academic"]["reason"] = f"Below academic threshold of {required_years} years (has {actual_years} years)."

    # Language Rule
    study_lang = profile.get('study_language', '').lower()
    exam_type = profile.get('language_exam', '')
    score = profile.get('language_score', None)

    if study_lang == 'japanese':
        if exam_type == 'JLPT' and isinstance(score, str):
            if score in ['N1', 'N2']:
                results["language"]["status"] = True
                results["language"]["reason"] = f"Meets Japanese proficiency with JLPT {score}."
            else:
                results["language"]["status"] = False
                results["language"]["reason"] = f"JLPT {score} is insufficient. Minimum level required is N2."
        else:
            results["language"]["status"] = False
            results["language"]["reason"] = "For Japanese track, a JLPT certificate (N2 or higher) is required."

    elif study_lang == 'english':
        eng_limits = track_rules['eligibility_criteria']['language_proficiency']['english_taught_track']['minimum_scores']
        if exam_type in eng_limits and score is not None:
            try:
                score_val = float(score)
                min_score = eng_limits[exam_type]
                if score_val >= min_score:
                    results["language"]["status"] = True
                    results["language"]["reason"] = f"Meets English proficiency with {exam_type} score of {score_val} (min: {min_score})."
                else:
                    results["language"]["status"] = False
                    results["language"]["reason"] = f"{exam_type} score of {score_val} is below minimum requirement of {min_score}."
            except ValueError:
                results["language"]["status"] = False
                results["language"]["reason"] = f"Invalid format for {exam_type} score."
        else:
            results["language"]["status"] = False
            results["language"]["reason"] = f"Language exam '{exam_type}' not recognized or score missing."
    else:
         results["language"]["status"] = False
         results["language"]["reason"] = "Study language must be specified as 'japanese' or 'english'."

    # Financial Rule
    min_funds = track_rules['eligibility_criteria']['financial_solvency']['minimum_annual_funding_jpy']
    actual_funds = profile.get('bank_balance_jpy', 0)
    if actual_funds >= min_funds:
        results["financial"]["status"] = True
        results["financial"]["reason"] = f"Meets financial solvent requirement of {min_funds:,} JPY (has {actual_funds:,} JPY)."
    else:
        results["financial"]["status"] = False
        results["financial"]["reason"] = f"Below financial solvency threshold of {min_funds:,} JPY (has {actual_funds:,} JPY)."

    is_eligible = all(criteria["status"] for criteria in results.values())

    action_items = []
    if not results["academic"]["status"]:
        action_items.append(f"Acquire additional equivalent formal education or check credentials qualification for {track} level.")
    if not results["language"]["status"]:
        action_items.append("Improve language skills and retake qualifying exam (JLPT N2+ for Japanese; IELTS/TOEFL threshold for English).")
    if not results["financial"]["status"]:
        shortfall = min_funds - actual_funds
        action_items.append(f"Increase bank balance or secure financial support to cover shortfall of {shortfall:,} JPY.")

    return {
        "eligible": is_eligible,
        "criteria_results": results,
        "action_items": action_items if action_items else ["All visa requirements met! Proceed to documents preparation."]
    }

def match_universities(profile, db):
    matched_programs = []
    track = profile.get('track', '').lower()
    study_lang = profile.get('study_language', '').lower()
    user_exam = profile.get('language_exam', '')
    user_score = profile.get('language_score', None)

    for program in db:
        if program['track'].lower() != track:
            continue
        if program['language'].lower() != study_lang:
            continue

        requirements = program['min_requirements']
        eligible = True

        if study_lang == 'japanese':
            req_jlpt = requirements.get('JLPT')
            if req_jlpt and user_exam == 'JLPT':
                if req_jlpt == 'N1' and user_score != 'N1':
                    eligible = False
                elif req_jlpt == 'N2' and user_score not in ['N1', 'N2']:
                    eligible = False
            else:
                eligible = False
        elif study_lang == 'english':
            if user_exam in requirements and user_score is not None:
                try:
                    if float(user_score) < float(requirements[user_exam]):
                        eligible = False
                except ValueError:
                     eligible = False
            else:
                eligible = False

        if eligible:
            matched_programs.append(program)

    return matched_programs

def generate_timeline_milestones(intake_semester, target_year):
    target_year = int(target_year)
    if intake_semester.lower() == 'april':
        return [
            {"phase": "Phase 1: Language Prep & Exam", "timeframe": f"May - August {target_year - 1}", "action": "Prepare and sit for IELTS, TOEFL, or JLPT."},
            {"phase": "Phase 2: University Application", "timeframe": f"September - November {target_year - 1}", "action": "Compile transcripts, recommendations, and submit applications."},
            {"phase": "Phase 3: CoE Processing", "timeframe": f"November {target_year - 1} - February {target_year}", "action": "University sponsors your Certificate of Eligibility (CoE) with Japanese Immigration."},
            {"phase": "Phase 4: Visa Issuance", "timeframe": f"February - March {target_year}", "action": "Apply for the student visa at your local embassy using the issued CoE."},
            {"phase": "Phase 5: Intake & Classes Begin", "timeframe": f"April {target_year}", "action": "Arrive in Japan, attend orientations, and begin classes."}
        ]
    else:
        return [
            {"phase": "Phase 1: Language Prep & Exam", "timeframe": f"October - December {target_year - 1}", "action": "Prepare and sit for IELTS, TOEFL, or JLPT."},
            {"phase": "Phase 2: University Application", "timeframe": f"January - March {target_year}", "action": "Compile transcripts, research proposals, and submit applications."},
            {"phase": "Phase 3: CoE Processing", "timeframe": f"April - July {target_year}", "action": "University sponsors your Certificate of Eligibility (CoE) with Japanese Immigration."},
            {"phase": "Phase 4: Visa Issuance", "timeframe": f"August - September {target_year}", "action": "Apply for the student visa at your local embassy using the issued CoE."},
            {"phase": "Phase 5: Intake & Classes Begin", "timeframe": f"October {target_year}", "action": "Arrive in Japan, finalize registration, and begin classes."}
        ]

# --- PDF Generation Function ---
def generate_pdf_summary(profile, report, matched, milestones, rules):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0F172A'), spaceAfter=10)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=6)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#334155'), spaceAfter=4)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'), spaceAfter=4)

    story = []
    story.append(Paragraph("Scholarpath Hub - Japan Academic & Visa Roadmap", title_style))
    story.append(Spacer(1, 10))

    # Profile Summary
    story.append(Paragraph("Applicant Profile & Preferences", section_style))
    profile_data = [
        [Paragraph("Track:", bold_style), Paragraph(profile['track'].capitalize(), normal_style)],
        [Paragraph("Years of Education:", bold_style), Paragraph(str(profile['education_years']), normal_style)],
        [Paragraph("Language of Study:", bold_style), Paragraph(profile['study_language'].capitalize(), normal_style)],
        [Paragraph("Language Exam/Score:", bold_style), Paragraph(f"{profile['language_exam']} (Score: {profile['language_score']})", normal_style)],
        [Paragraph("Bank Balance (JPY):", bold_style), Paragraph(f"{profile['bank_balance_jpy']:,} JPY", normal_style)]
    ]
    t_profile = Table(profile_data, colWidths=[130, 420])
    t_profile.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_profile)
    story.append(Spacer(1, 10))

    # University Matches
    story.append(Paragraph("Matched University Programs in Japan", section_style))
    if matched:
        uni_data = [[Paragraph("<b>University</b>", bold_style), Paragraph("<b>Program Name</b>", bold_style), Paragraph("<b>Min Score Req.</b>", bold_style)]]
        for program in matched:
            req_str = ", ".join([f"{k}: {v}" for k, v in program['min_requirements'].items()])
            uni_data.append([
                Paragraph(program['university'], normal_style),
                Paragraph(program['program_name'], normal_style),
                Paragraph(req_str, normal_style)
            ])
        t_uni = Table(uni_data, colWidths=[180, 240, 130])
        t_uni.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_uni)
    else:
        story.append(Paragraph("No university programs matched with current academic/language parameters.", normal_style))
    story.append(Spacer(1, 10))

    # Timeline Milestones
    story.append(Paragraph(f"Admission & Visa Timeline: {profile['intake_semester'].capitalize()} {profile['intake_year']}", section_style))
    time_data = [[Paragraph("<b>Phase / Description</b>", bold_style), Paragraph("<b>Timeline Window</b>", bold_style), Paragraph("<b>Action Needed</b>", bold_style)]]
    for m in milestones:
        time_data.append([
            Paragraph(m['phase'], bold_style),
            Paragraph(m['timeframe'], normal_style),
            Paragraph(m['action'], normal_style)
        ])
    t_time = Table(time_data, colWidths=[150, 150, 250])
    t_time.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_time)
    story.append(Spacer(1, 10))

    # Visa Evaluation Status
    story.append(Paragraph("Visa Eligibility Evaluation Results", section_style))
    status_text = "<b>ELIGIBLE</b>" if report['eligible'] else "<b>NOT YET ELIGIBLE</b>"
    status_color = colors.HexColor('#16A34A') if report['eligible'] else colors.HexColor('#DC2626')
    status_box_style = ParagraphStyle('StatusBox', parent=normal_style, fontSize=11, textColor=colors.white, backColor=status_color, borderPadding=6, spaceAfter=8)
    story.append(Paragraph(f"Overall Visa Status: {status_text}", status_box_style))

    # Criteria Table
    crit_data = [[Paragraph("<b>Visa Criterion</b>", bold_style), Paragraph("<b>Status</b>", bold_style), Paragraph("<b>Reasoning</b>", bold_style)]]
    for cat, details in report['criteria_results'].items():
        crit_status = "PASS" if details['status'] else "FAIL"
        crit_data.append([
            Paragraph(cat.capitalize(), bold_style),
            Paragraph(crit_status, bold_style),
            Paragraph(details['reason'], normal_style)
        ])
    t_crit = Table(crit_data, colWidths=[100, 70, 380])
    t_crit.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_crit)
    story.append(Spacer(1, 10))

    # Document Checklist
    story.append(Paragraph("Visa Document Checklist Requirements", section_style))
    track_rules = rules[profile['track']]
    story.append(Paragraph("<b>Mandatory Documents:</b>", bold_style))
    for doc_item in track_rules['document_checklist']['mandatory']:
        story.append(Paragraph(f"[  ] {doc_item}", normal_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Supporting/Recommended Documents:</b>", bold_style))
    for doc_item in track_rules['document_checklist']['supporting']:
        story.append(Paragraph(f"[  ] {doc_item}", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Streamlit UI Main ---
st.set_page_config(page_title="Scholarpath Hub", layout="wide")

st.markdown("# 🎓 Scholarpath Hub - Japan Advisory Portal")
st.write("Follow this end-to-end consulting tool to find matching university programs, generate a calendar timeline, and evaluate visa eligibility.")

# Multi-Stage Tabs
tab1, tab2 = st.tabs(["🔍 Stage 1: University Matcher & Timeline", "📋 Stage 2: Visa Eligibility Evaluator"])

with st.sidebar:
    st.header("Global Applicant Profile")
    track = st.selectbox("Target Academic Level", ["Undergraduate", "Masters"])
    edu_years = st.number_input("Total Years of Education", min_value=1, max_value=25, value=12 if track == "Undergraduate" else 16)
    study_lang = st.selectbox("Desired Language of Instruction", ["English", "Japanese"])

    if study_lang == "Japanese":
        exam_type = "JLPT"
        score = st.selectbox("JLPT Score Level", ["N1", "N2", "N3", "N4", "N5", "None"])
    else:
        exam_type = st.selectbox("Proficiency Exam Type", ["IELTS", "TOEFL iBT"])
        if exam_type == "IELTS":
            score = st.number_input("IELTS Band Score", min_value=1.0, max_value=9.0, value=6.0, step=0.5)
        else:
            score = st.number_input("TOEFL Score", min_value=0, max_value=120, value=80, step=1)

    bank_balance = st.number_input("Available Funds / Financial Solvency (JPY)", min_value=0, value=2100000, step=50000)

    st.subheader("Target Intake Planning")
    intake_semester = st.selectbox("Target Semester", ["October", "April"])
    intake_year = st.selectbox("Target Year", [2026, 2027, 2028, 2029])

profile = {
    "track": track.lower(),
    "education_years": edu_years,
    "study_language": study_lang.lower(),
    "language_exam": exam_type,
    "language_score": score,
    "bank_balance_jpy": bank_balance,
    "intake_semester": intake_semester,
    "intake_year": intake_year
}

# Global logic computations
matched_programs = match_universities(profile, japan_universities_db)
milestones = generate_timeline_milestones(intake_semester, intake_year)
visa_report = evaluate_visa_eligibility(profile, japan_visa_rules)

with tab1:
    st.subheader("1. Your Eligible University Programs in Japan")
    if matched_programs:
        st.success(f"We found {len(matched_programs)} program(s) matching your profile!")
        flat_matched = []
        for p in matched_programs:
            reqs = ", ".join([f"{k}: {v}" for k, v in p['min_requirements'].items()])
            flat_matched.append({
                "University": p['university'],
                "Program": p['program_name'],
                "Language": p['language'],
                "Requirements": reqs,
                "April Deadline": p['intakes']['April']['deadline'],
                "October Deadline": p['intakes']['October']['deadline']
            })
        st.dataframe(pd.DataFrame(flat_matched), use_container_width=True)
    else:
        st.warning("⚠️ No programs from our database fully matched your current language exam/scores.")

    st.subheader(f"2. Reverse-Engineered Admission & Visa Roadmap Timeline ({intake_semester} {intake_year})")
    for m in milestones:
        with st.expander(f"📅 {m['phase']} — ({m['timeframe']})", expanded=True):
            st.write(f"**Action Item:** {m['action']}")

with tab2:
    st.subheader("3. Post-Admission Visa Eligibility Evaluator")
    if visa_report['eligible']:
        st.success("✅ Based on simulated immigration guidelines, you meet the initial eligibility requirements for a Japanese student visa!")
    else:
        st.error("❌ Your profile currently has deficits for one or more crucial visa requirements.")

    # Metric scorecard
    mcol1, mcol2 = st.columns(2)
    mcol1.metric("Annual Financial Standing", f"{bank_balance:,} JPY", "Pass" if visa_report['criteria_results']['financial']['status'] else "Shortfall")
    mcol2.metric("Academic Evaluation", f"{edu_years} Years", "Pass" if visa_report['criteria_results']['academic']['status'] else "Incomplete")

    # Breakdown
    with st.expander("Requirements Evaluation Breakdown", expanded=True):
        for criteria_name, values in visa_report['criteria_results'].items():
            ind = "🟢" if values['status'] else "🔴"
            st.write(f"{ind} **{criteria_name.capitalize()} Criterion**: {values['reason']}")

    # Advisory Action items
    st.markdown("#### Recommended Next Steps & Consultation Action Items")
    for item in visa_report['action_items']:
        st.write(f"- {item}")

    # Document Checklist
    st.markdown("---")
    st.subheader("4. Interactive Document Checklist")
    checklist_rules = japan_visa_rules[profile['track']]

    st.markdown("**Mandatory Visas Documents**")
    for doc in checklist_rules['document_checklist']['mandatory']:
        st.checkbox(doc, value=False, key=f"mand_doc_{doc}")

    st.markdown("**Supporting & Recommended Visas Documents**")
    for doc in checklist_rules['document_checklist']['supporting']:
        st.checkbox(doc, value=False, key=f"supp_doc_{doc}")

    # Complete Download
    st.markdown("---")
    st.subheader("5. Export Your Consultation Roadmap PDF")
    st.write("Generate a comprehensive, single-page summary PDF of your matched academic targets, milestones, and visa readiness scorecard.")

    pdf_data = generate_pdf_summary(profile, visa_report, matched_programs, milestones, japan_visa_rules)
    st.download_button( 
        label="📥 Download Full Consultation PDF",
        data=pdf_data,
        file_name="Scholarpath_Hub_Consultation_Roadmap.pdf",
        mime="application/pdf"
    )
