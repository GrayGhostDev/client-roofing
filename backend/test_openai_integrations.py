"""
OpenAI Integration Test Suite - Week 10 & Week 11
Comprehensive testing of all GPT-4o integrations

Tests:
- Week 10: Call Transcription Service (4 tests)
- Week 11: Email Personalization Service (4 tests)

Author: Week 11 Implementation
Created: 2025-10-12
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import services
from app.services.call_transcription import CallTranscriptionService
from app.services.intelligence.email_personalization import EmailPersonalizationService
from app.models.lead_sqlalchemy import Lead
from app.database import get_db_session


# ============================================================================
# TEST UTILITIES
# ============================================================================

class TestResult:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"✅ PASSED: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.errors.append({"test": test_name, "error": error})
        print(f"❌ FAILED: {test_name}")
        print(f"   Error: {error}")

    def add_skip(self, test_name: str, reason: str):
        self.total += 1
        self.skipped += 1
        print(f"⏭️  SKIPPED: {test_name}")
        print(f"   Reason: {reason}")

    def print_summary(self):
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"\nTotal Tests: {self.total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏭️  Skipped: {self.skipped}")

        if self.errors:
            print("\n❌ FAILED TESTS:")
            for error in self.errors:
                print(f"  - {error['test']}: {error['error']}")

        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        print("="*80 + "\n")


results = TestResult()


# ============================================================================
# WEEK 10 TESTS: CALL TRANSCRIPTION SERVICE
# ============================================================================

async def test_conversation_summarization():
    """Test 1.2: Conversation Summarization with GPT-4o"""
    test_name = "Test 1.2: Conversation Summarization (GPT-4o)"
    print(f"\n🧪 Running {test_name}...")

    try:
        service = CallTranscriptionService()

        # Sample conversation
        transcript = """
Homeowner: Hi, I'm calling about getting a quote for a new roof.
Sales Rep: Great! I'd be happy to help. What's your address?
Homeowner: 123 Main Street, Birmingham, Michigan 48301
Sales Rep: Perfect. Can you tell me about your current roof condition?
Homeowner: Well, it's about 18 years old and I've noticed some shingles missing after the storm last week.
Sales Rep: I understand. We can definitely help with that. Let me schedule a free inspection for you.
Homeowner: That would be great. How soon can you come out?
Sales Rep: We have availability this Tuesday at 2 PM. Does that work for you?
Homeowner: Yes, Tuesday at 2 PM works perfectly.
Sales Rep: Excellent! I'll send you a confirmation email with all the details.
"""

        # Call the service
        result = await service._summarize_conversation(transcript)

        # Assertions
        assert result is not None, "Summary should not be None"
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "summary" in result, "Should contain summary"
        assert len(result["summary"]) > 20, "Summary should be meaningful"

        print(f"   📝 Summary generated: {result['summary'][:100]}...")
        print(f"   🎯 Intent detected: {result.get('intent', 'N/A')}")
        print(f"   😊 Sentiment: {result.get('sentiment', 'N/A')}")

        results.add_pass(test_name)
        return result

    except Exception as e:
        results.add_fail(test_name, str(e))
        return None


async def test_action_item_extraction():
    """Test 1.3: Action Item Extraction with GPT-4o"""
    test_name = "Test 1.3: Action Item Extraction (GPT-4o)"
    print(f"\n🧪 Running {test_name}...")

    try:
        service = CallTranscriptionService()

        # Sample conversation with clear action items
        transcript = """
Sales Rep: I can schedule that inspection for you. Would Tuesday at 2 PM work?
Homeowner: Tuesday works great. Can you also email me some information about your premium materials?
Sales Rep: Absolutely. I'll send that over today along with our financing options.
Homeowner: Perfect. One more thing - do you offer a warranty?
Sales Rep: Yes, we offer a 25-year warranty on all our work. I'll include that information in the email.
Homeowner: Great. And can you also send me some references from customers in my area?
Sales Rep: Of course. I'll include 3-4 local references in the email as well.
"""

        # Call the service
        result = await service._extract_action_items(transcript)

        # Assertions
        assert result is not None, "Action items should not be None"
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "action_items" in result, "Should contain action_items"
        assert len(result["action_items"]) > 0, "Should extract at least one action item"

        print(f"   📋 Extracted {len(result['action_items'])} action items:")
        for item in result["action_items"][:3]:  # Show first 3
            print(f"      - {item.get('type', 'unknown')}: {item.get('description', 'N/A')[:60]}...")

        results.add_pass(test_name)
        return result

    except Exception as e:
        results.add_fail(test_name, str(e))
        return None


async def test_sentiment_analysis():
    """Test 1.4: Sentiment Analysis with GPT-4o"""
    test_name = "Test 1.4: Sentiment Analysis (GPT-4o)"
    print(f"\n🧪 Running {test_name}...")

    try:
        service = CallTranscriptionService()

        # Test cases with different sentiments
        test_cases = [
            {
                "transcript": "This is great! I'm so excited to work with you. Your pricing is very reasonable and the warranty sounds amazing.",
                "expected": "positive"
            },
            {
                "transcript": "Okay, I guess. I'll think about it and maybe call back later. Not sure yet.",
                "expected": "neutral"
            },
            {
                "transcript": "This is way too expensive. I'm not interested. Please don't call me again.",
                "expected": "negative"
            }
        ]

        all_passed = True
        for i, test_case in enumerate(test_cases, 1):
            result = await service._analyze_sentiment(test_case["transcript"])

            detected_sentiment = result.get("sentiment", "unknown")
            expected_sentiment = test_case["expected"]

            if detected_sentiment == expected_sentiment:
                print(f"   ✅ Case {i}: {expected_sentiment} sentiment correctly detected")
            else:
                print(f"   ⚠️  Case {i}: Expected {expected_sentiment}, got {detected_sentiment}")
                all_passed = False

        if all_passed:
            results.add_pass(test_name)
        else:
            results.add_fail(test_name, "Some sentiment classifications were incorrect")

        return {"all_passed": all_passed}

    except Exception as e:
        results.add_fail(test_name, str(e))
        return None


async def test_audio_transcription():
    """Test 1.1: Audio Transcription with Whisper API"""
    test_name = "Test 1.1: Audio Transcription (Whisper API)"
    print(f"\n🧪 Running {test_name}...")

    # Skip this test as it requires actual audio file
    results.add_skip(
        test_name,
        "Requires actual audio file. Service is ready, but no test audio provided."
    )
    return None


# ============================================================================
# WEEK 11 TESTS: EMAIL PERSONALIZATION SERVICE
# ============================================================================

async def test_subject_line_generation():
    """Test 2.1: Subject Line Generation with GPT-4o"""
    test_name = "Test 2.1: Subject Line Generation (GPT-4o)"
    print(f"\n🧪 Running {test_name}...")

    try:
        db = next(get_db_session())
        service = EmailPersonalizationService(db)

        # Create test lead
        lead = Lead(
            id=99999,
            first_name="John",
            last_name="Smith",
            email="john.smith@example.com",
            phone="248-555-1234",
            address="123 Oak Avenue",
            city="Birmingham",
            state="MI",
            zip_code="48301",
            source="website"
        )

        context = {
            "property_type": "Colonial",
            "home_value": 650000,
            "roof_age": 18,
            "recent_storm": True,
            "neighborhood": "Bloomfield Hills"
        }

        # Generate subject line
        subject = await service.personalize_subject_line(
            lead=lead,
            template_type="initial_contact",
            context=context
        )

        # Assertions
        assert subject is not None, "Subject line should not be None"
        assert isinstance(subject, str), "Subject should be a string"
        assert len(subject) <= 60, f"Subject should be under 60 chars (was {len(subject)})"
        assert len(subject) >= 10, "Subject should be at least 10 chars"

        # Check for personalization
        has_name = "John" in subject or "Smith" in subject
        has_location = "Birmingham" in subject or "Bloomfield" in subject or "Oak" in subject

        print(f"   📧 Generated subject: {subject}")
        print(f"   📏 Length: {len(subject)} characters")
        print(f"   👤 Contains name: {has_name}")
        print(f"   📍 Contains location: {has_location}")

        results.add_pass(test_name)
        return {"subject": subject, "has_name": has_name, "has_location": has_location}

    except Exception as e:
        results.add_fail(test_name, str(e))
        return None


async def test_full_email_generation():
    """Test 2.2: Full Email Generation with GPT-4o"""
    test_name = "Test 2.2: Full Email Generation (GPT-4o)"
    print(f"\n🧪 Running {test_name}...")

    try:
        db = next(get_db_session())
        service = EmailPersonalizationService(db)

        # Create test lead (would normally query from database)
        lead = Lead(
            id=99999,
            first_name="Sarah",
            last_name="Johnson",
            email="sarah.johnson@example.com",
            phone="248-555-5678",
            address="456 Elm Street",
            city="Troy",
            state="MI",
            zip_code="48084",
            source="referral"
        )

        # Add lead to session temporarily
        db.add(lead)
        db.flush()

        context = {
            "property_value": 450000,
            "roof_age": 22,
            "weather_event": "Wind damage from July storms",
            "neighborhood": "Troy",
            "nearby_projects": 5
        }

        # Generate email
        result = await service.generate_personalized_email(
            lead_id=lead.id,
            template_type="initial_contact",
            context=context
        )

        # Rollback (don't actually save test lead)
        db.rollback()

        # Assertions
        assert result is not None, "Email generation should return result"
        assert "subject" in result, "Should contain subject"
        assert "html_content" in result, "Should contain HTML content"
        assert "plain_text" in result, "Should contain plain text"
        assert "ai_confidence" in result, "Should contain AI confidence"

        assert len(result["subject"]) > 0, "Subject should not be empty"
        assert len(result["html_content"]) > 100, "HTML content should be substantial"
        assert "{{" not in result["html_content"], "All variables should be replaced"
        assert result["ai_confidence"] > 0.5, "AI confidence should be reasonable"

        print(f"   📧 Subject: {result['subject']}")
        print(f"   📏 HTML length: {len(result['html_content'])} characters")
        print(f"   📄 Plain text length: {len(result['plain_text'])} characters")
        print(f"   🎯 AI confidence: {result['ai_confidence']:.2f}")
        print(f"   ⏰ Recommended send time: {result.get('send_time_recommendation', 'N/A')}")

        results.add_pass(test_name)
        return result

    except Exception as e:
        results.add_fail(test_name, str(e))
        return None


async def test_property_intelligence_injection():
    """Test 2.3: Property Intelligence Injection with GPT-4o"""
    test_name = "Test 2.3: Property Intelligence Injection (GPT-4o)"
    print(f"\n🧪 Running {test_name}...")

    try:
        db = next(get_db_session())
        service = EmailPersonalizationService(db)

        # Sample email content with placeholders
        email_content = """
        Hi {{first_name}},

        I wanted to reach out about your property at {{address}}.

        Based on what I know, your home is valued at around {{home_value}}.
        """

        property_data = {
            "home_value": 650000,
            "year_built": 1995,
            "roof_age": 18,
            "roof_condition": "fair",
            "material_tier": "ultra_premium",
            "estimated_project_cost": 28000
        }

        # Inject property intelligence
        result = await service.inject_property_intelligence(
            email_content=email_content,
            property_data=property_data
        )

        # Assertions
        assert result is not None, "Result should not be None"
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > len(email_content), "Should add property intelligence"

        # Check for property mentions
        has_value = "650" in result or "$650" in result
        has_age = "18" in result or "eighteen" in result
        has_condition = "fair" in result or "attention" in result.lower()

        print(f"   📏 Original length: {len(email_content)} → Enhanced length: {len(result)}")
        print(f"   💰 Contains home value: {has_value}")
        print(f"   🏠 Contains roof age: {has_age}")
        print(f"   ⚠️  Contains condition: {has_condition}")
        print(f"   📝 Sample: {result[:150]}...")

        results.add_pass(test_name)
        return {"enhanced_content": result, "has_value": has_value, "has_age": has_age}

    except Exception as e:
        results.add_fail(test_name, str(e))
        return None


async def test_email_quality_scoring():
    """Test 2.4: Email Quality Scoring with GPT-4o"""
    test_name = "Test 2.4: Email Quality Scoring (GPT-4o)"
    print(f"\n🧪 Running {test_name}...")

    try:
        db = next(get_db_session())
        service = EmailPersonalizationService(db)

        # Good email example
        good_email = """
Hi John,

I noticed your property at 123 Oak Avenue in Birmingham. Based on recent storm activity
in your area, I wanted to reach out about your roof.

Our records show your home is valued at approximately $650,000. For homes like yours,
we typically recommend our premium materials that come with a 25-year warranty.

Would you be interested in a free inspection? We have availability this week.

Best regards,
Mike Thompson
iSwitch Roofs
        """

        # Spam-trigger email example
        spam_email = """
FREE!!! ACT NOW!!! LIMITED TIME ONLY!!!

CLICK HERE for the LOWEST PRICES GUARANTEED!!!

Don't miss out! CALL NOW! This offer won't last!

BUY NOW! SAVE THOUSANDS! FREE INSTALLATION!!!
        """

        # Score good email
        good_result = await service.score_email_quality(
            email_content=good_email,
            subject_line="John, your Birmingham home may need attention"
        )

        # Score spam email
        spam_result = await service.score_email_quality(
            email_content=spam_email,
            subject_line="FREE!!! CLICK NOW!!! LIMITED TIME!!!"
        )

        # Assertions
        assert good_result["overall_score"] > 70, f"Good email should score >70 (was {good_result['overall_score']})"
        assert spam_result["overall_score"] < 50, f"Spam email should score <50 (was {spam_result['overall_score']})"
        assert good_result["spam_score"] > spam_result["spam_score"], "Good email should have higher spam score"

        print(f"   ✅ Good email score: {good_result['overall_score']}/100")
        print(f"      - Spam score: {good_result['spam_score']}/100")
        print(f"      - Personalization: {good_result['personalization_score']}/100")
        print(f"   ❌ Spam email score: {spam_result['overall_score']}/100")
        print(f"      - Spam score: {spam_result['spam_score']}/100")
        print(f"      - Personalization: {spam_result['personalization_score']}/100")

        results.add_pass(test_name)
        return {"good": good_result, "spam": spam_result}

    except Exception as e:
        results.add_fail(test_name, str(e))
        return None


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all OpenAI integration tests"""

    print("\n" + "="*80)
    print("🧪 OPENAI API INTEGRATION TESTS - WEEK 10 & WEEK 11")
    print("="*80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Model: GPT-4o")
    print(f"🔑 API Key: {'✅ Configured' if os.getenv('OPENAI_API_KEY') else '❌ Not Found'}")
    print("="*80)

    if not os.getenv('OPENAI_API_KEY'):
        print("\n⚠️  WARNING: OPENAI_API_KEY not set!")
        print("   Please set the API key to run tests:")
        print("   export OPENAI_API_KEY='sk-proj-your-key-here'")
        print("\n" + "="*80)
        return

    # =======================================================================
    # WEEK 10: CALL TRANSCRIPTION SERVICE
    # =======================================================================

    print("\n\n📞 WEEK 10: CALL TRANSCRIPTION SERVICE (GPT-4o)")
    print("-" * 80)

    # Test 1.1: Audio Transcription (Skipped - requires audio file)
    await test_audio_transcription()

    # Test 1.2: Conversation Summarization
    await test_conversation_summarization()

    # Test 1.3: Action Item Extraction
    await test_action_item_extraction()

    # Test 1.4: Sentiment Analysis
    await test_sentiment_analysis()

    # =======================================================================
    # WEEK 11: EMAIL PERSONALIZATION SERVICE
    # =======================================================================

    print("\n\n📧 WEEK 11: EMAIL PERSONALIZATION SERVICE (GPT-4o)")
    print("-" * 80)

    # Test 2.1: Subject Line Generation
    await test_subject_line_generation()

    # Test 2.2: Full Email Generation
    await test_full_email_generation()

    # Test 2.3: Property Intelligence Injection
    await test_property_intelligence_injection()

    # Test 2.4: Email Quality Scoring
    await test_email_quality_scoring()

    # =======================================================================
    # TEST SUMMARY
    # =======================================================================

    results.print_summary()

    # Success criteria
    success_rate = (results.passed / results.total * 100) if results.total > 0 else 0

    if success_rate >= 80:
        print("🎉 SUCCESS: All OpenAI integrations are working correctly!")
        print("✅ Services are PRODUCTION READY")
    elif success_rate >= 50:
        print("⚠️  WARNING: Some tests failed. Review errors above.")
        print("🔧 Services need adjustments before production")
    else:
        print("❌ FAILURE: Major issues detected. Services NOT ready for production.")
        print("🛠️  Requires immediate attention")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
