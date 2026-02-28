import json
from datetime import datetime, timedelta
from database import DatabaseManager, User
from models import UserRole, RiskLevel, ClauseType

def create_mock_regulatory_changes():
    """Create mock regulatory changes for demonstration"""
    return [
        {
            "title": "GDPR Enhancement Act 2024",
            "description": "New requirements for data processing transparency and consent management. Organizations must implement explicit consent mechanisms and provide detailed data processing logs.",
            "category": "privacy",
            "effective_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
            "impact_level": RiskLevel.HIGH,
            "affected_industries": ["technology", "healthcare", "financial", "retail"],
            "old_text": "Data controllers shall obtain consent for data processing.",
            "new_text": "Data controllers must obtain explicit, informed consent through clear, unambiguous affirmative action. Consent must be documented and easily withdrawable at any time."
        },
        {
            "title": "Climate Risk Disclosure Amendment",
            "description": "Mandatory climate risk reporting for all publicly traded companies and large private enterprises.",
            "category": "environmental",
            "effective_date": (datetime.utcnow() + timedelta(days=180)).isoformat(),
            "impact_level": RiskLevel.MEDIUM,
            "affected_industries": ["manufacturing", "energy", "transportation", "financial"],
            "old_text": "Companies should consider environmental impact in their operations.",
            "new_text": "Companies must report Scope 1, 2, and 3 greenhouse gas emissions, climate-related financial risks, and transition strategies aligned with Paris Agreement goals."
        },
        {
            "title": "AI Governance Framework",
            "description": "New regulations for artificial intelligence systems requiring transparency, bias testing, and human oversight.",
            "category": "technology",
            "effective_date": (datetime.utcnow() + timedelta(days=120)).isoformat(),
            "impact_level": RiskLevel.CRITICAL,
            "affected_industries": ["technology", "healthcare", "financial", "professional_services"],
            "old_text": "AI systems should be developed responsibly.",
            "new_text": "High-risk AI systems must undergo mandatory bias audits, provide explainable decisions, maintain human oversight, and register with regulatory authorities before deployment."
        },
        {
            "title": "Supply Chain Due Diligence Act",
            "description": "Requirements for human rights due diligence in global supply chains with mandatory reporting.",
            "category": "social",
            "effective_date": (datetime.utcnow() + timedelta(days=60)).isoformat(),
            "impact_level": RiskLevel.HIGH,
            "affected_industries": ["manufacturing", "retail", "technology", "automotive"],
            "old_text": "Companies should monitor their supply chains.",
            "new_text": "Companies must conduct annual human rights due diligence assessments, identify and remediate violations, and publish detailed supply chain reports including remediation actions."
        },
        {
            "title": "Cybersecurity Resilience Standards",
            "description": "Enhanced cybersecurity requirements including zero-trust architecture and incident response timelines.",
            "category": "technology",
            "effective_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
            "impact_level": RiskLevel.HIGH,
            "affected_industries": ["financial", "healthcare", "energy", "technology"],
            "old_text": "Organizations should implement reasonable security measures.",
            "new_text": "Organizations must implement zero-trust architecture, maintain 24/7 security monitoring, report breaches within 72 hours, and conduct quarterly penetration testing."
        }
    ]

def create_mock_contract_clauses():
    """Create mock contract clauses for demonstration"""
    return [
        {
            "type": ClauseType.LIABILITY,
            "content": "The total liability of either party under this agreement shall not exceed the aggregate fees paid by the client to the service provider in the twelve (12) months preceding the claim. In no event shall either party be liable for consequential, indirect, or punitive damages.",
            "risk_score": 0.3
        },
        {
            "type": ClauseType.INDEMNITY,
            "content": "The service provider shall indemnify, defend, and hold harmless the client from and against any and all claims, damages, losses, liabilities, and expenses, including reasonable attorneys' fees, arising out of or resulting from the service provider's breach of this agreement or negligence.",
            "risk_score": 0.7
        },
        {
            "type": ClauseType.TERMINATION,
            "content": "Either party may terminate this agreement upon thirty (30) days written notice to the other party. In the event of material breach, the non-breaching party may terminate immediately upon written notice.",
            "risk_score": 0.4
        },
        {
            "type": ClauseType.CONFIDENTIALITY,
            "content": "Both parties shall maintain the confidentiality of all proprietary information exchanged during the term of this agreement and for a period of five (5) years thereafter. Confidential information includes trade secrets, business plans, customer data, and technical specifications.",
            "risk_score": 0.5
        },
        {
            "type": ClauseType.PAYMENT,
            "content": "The client shall pay the service provider the fees set forth in the statement of work within thirty (30) days of invoice date. Late payments shall accrue interest at the rate of 1.5% per month.",
            "risk_score": 0.2
        },
        {
            "type": ClauseType.INTELLECTUAL_PROPERTY,
            "content": "All intellectual property developed by the service provider in the course of performing services shall remain the exclusive property of the service provider. The client is granted a non-exclusive, non-transferable license to use such intellectual property solely for internal business purposes.",
            "risk_score": 0.6
        },
        {
            "type": ClauseType.DISPUTE_RESOLUTION,
            "content": "Any disputes arising out of or relating to this agreement shall be resolved through binding arbitration in accordance with the rules of the American Arbitration Association. The arbitration shall be conducted in New York, New York.",
            "risk_score": 0.3
        },
        {
            "type": ClauseType.LIABILITY,
            "content": "The service provider assumes unlimited liability for any data breaches resulting from negligence or failure to implement reasonable security measures. This liability extends to all direct, indirect, consequential, and punitive damages without limitation.",
            "risk_score": 0.9
        },
        {
            "type": ClauseType.INDEMNITY,
            "content": "The client agrees to indemnify and hold the service provider harmless from any claims arising from the client's use of the services, including but not limited to claims of intellectual property infringement, defamation, or violation of applicable laws.",
            "risk_score": 0.6
        },
        {
            "type": ClauseType.TERMINATION,
            "content": "The service provider may terminate this agreement immediately without notice if the client fails to make any payment when due. Upon termination, all outstanding fees become immediately due and payable.",
            "risk_score": 0.5
        }
    ]

def create_mock_esg_text_samples():
    """Create mock text samples for ESG analysis"""
    return [
        {
            "text": "Our company is committed to environmental sustainability and has implemented comprehensive carbon reduction initiatives. We have reduced our greenhouse gas emissions by 40% since 2020 and are on track to achieve net-zero emissions by 2030. Our manufacturing facilities utilize renewable energy sources and we have implemented water conservation programs across all operations.",
            "expected_categories": ["environmental"],
            "expected_sentiment": 0.7
        },
        {
            "text": "We maintain strict labor standards across our supply chain, ensuring fair wages, safe working conditions, and no child labor. However, recent audits revealed violations at two supplier facilities in Southeast Asia regarding overtime hours and safety protocols. We are working with these suppliers to implement corrective actions.",
            "expected_categories": ["social"],
            "expected_sentiment": -0.2
        },
        {
            "text": "Our board of directors has established robust governance mechanisms including independent audit committees, whistleblower protection programs, and transparent executive compensation policies. We have zero tolerance for corruption and have implemented comprehensive anti-bribery training for all employees.",
            "expected_categories": ["governance"],
            "expected_sentiment": 0.6
        },
        {
            "text": "The company faces multiple lawsuits alleging environmental contamination from our chemical plants. Investigations have revealed improper disposal of hazardous waste and failure to obtain required environmental permits. Regulatory agencies have imposed significant fines and we may face criminal charges.",
            "expected_categories": ["environmental", "governance"],
            "expected_sentiment": -0.8
        },
        {
            "text": "We prioritize employee welfare with comprehensive health benefits, professional development programs, and work-life balance initiatives. Our diversity and inclusion programs have increased underrepresented groups in leadership positions by 25% over the past three years.",
            "expected_categories": ["social"],
            "expected_sentiment": 0.8
        }
    ]

def seed_database():
    """Seed the database with mock data"""
    db_manager = DatabaseManager("sqlite:///./lawlens.db")
    
    try:
        # create or update admin and regular users with known passwords
        from security import SecurityValidator

        admin_password = "Admin123"
        user_password = "user123"

        # use a direct session for updates
        db = db_manager.SessionLocal()
        try:
            existing_admin = db.query(User).filter(User.email == "admin@lawlens.com").first()
            if existing_admin:
                existing_admin.hashed_password = SecurityValidator.hash_password(admin_password)
                db.commit()
                admin_user = existing_admin
                print("Updated admin password")
            else:
                admin_user = db_manager.create_user(
                    email="admin@lawlens.com",
                    hashed_password=SecurityValidator.hash_password(admin_password),
                    role="admin"
                )
                print("Created admin user")

            existing_user = db.query(User).filter(User.email == "user@lawlens.com").first()
            if existing_user:
                existing_user.hashed_password = SecurityValidator.hash_password(user_password)
                db.commit()
                regular_user = existing_user
                print("Updated regular user password")
            else:
                regular_user = db_manager.create_user(
                    email="user@lawlens.com",
                    hashed_password=SecurityValidator.hash_password(user_password),
                    role="user"
                )
                print("Created regular user")

            # capture id before closing session, to avoid detached-instance issues
            regular_user_id = regular_user.id
        finally:
            db.close()
        
        # Create mock documents and clauses
        clauses = create_mock_contract_clauses()
        
        for i in range(3):  # Create 3 sample documents
            document = db_manager.create_document(
                filename=f"sample_contract_{i+1}.pdf",
                original_filename=f"Service Agreement {i+1}.pdf",
                mime_type="application/pdf",
                file_size=1024000,
                content_hash=f"hash_{i+1}",
                user_id=regular_user_id
            )
            
            # Add clauses to document
            document_clauses = []
            for j, clause_data in enumerate(clauses[:5]):  # 5 clauses per document
                clause_data["document_id"] = document.id
                document_clauses.append(clause_data)
            
            saved_clauses = db_manager.save_clauses(document.id, document_clauses)
            print(f"Created document {i+1} with {len(saved_clauses)} clauses")
        
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_database()
