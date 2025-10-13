"""
OpenAI GPT-4 Integration for NBA Enhancement
Uses Structured Outputs (2025 best practice) with Pydantic v2
"""

from openai import OpenAI
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class EnhancedNBARecommendation(BaseModel):
    """
    Enhanced NBA recommendation with GPT-4 strategic reasoning

    Uses OpenAI Structured Outputs (2025 pattern) with strict schema adherence
    """
    model_config = ConfigDict(strict=True)

    action: str = Field(..., description="Refined action recommendation")
    reasoning: str = Field(
        ...,
        description="Strategic reasoning explaining why this action is optimal"
    )
    talking_points: List[str] = Field(
        ...,
        description="Specific talking points for the sales rep to use",
        min_length=3,
        max_length=10
    )
    urgency_level: str = Field(
        ...,
        description="Urgency assessment based on lead behavior and market conditions",
        pattern="^(low|medium|high|critical)$"
    )
    estimated_conversion_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability of conversion (0-1)"
    )
    optimal_contact_time: str = Field(
        ...,
        description="Recommended time to contact (e.g., 'Morning this week', 'Within 24 hours')"
    )
    objection_handling: List[str] = Field(
        default_factory=list,
        description="Anticipated objections and how to handle them",
        max_length=5
    )
    value_proposition: str = Field(
        ...,
        description="Tailored value proposition based on lead profile"
    )


class GPT4EnhancementContext(BaseModel):
    """Context information for GPT-4 enhancement"""
    model_config = ConfigDict(strict=True)

    lead_id: str
    ml_predicted_action: str
    ml_confidence: float
    lead_source: str
    property_value: Optional[float]
    property_zip: str
    interaction_count: int
    email_open_rate: float
    response_rate: float
    lead_age_days: int
    days_since_last_contact: int
    engagement_score: Optional[float] = None
    urgency_score: Optional[float] = None


async def enhance_nba_with_gpt4(
    context: GPT4EnhancementContext,
    model: str = "gpt-4o-2024-08-06"
) -> EnhancedNBARecommendation:
    """
    Enhance ML prediction with GPT-4 strategic reasoning

    Uses OpenAI Structured Outputs (2025 best practice) for guaranteed schema adherence

    Args:
        context: Lead context and ML prediction
        model: OpenAI model to use (default: gpt-4o-2024-08-06)

    Returns:
        EnhancedNBARecommendation with strategic guidance

    Example:
        ```python
        context = GPT4EnhancementContext(
            lead_id="lead_123",
            ml_predicted_action="schedule_appointment",
            ml_confidence=0.87,
            lead_source="google_ads",
            property_value=650000,
            property_zip="48302",
            interaction_count=5,
            email_open_rate=0.8,
            response_rate=0.6,
            lead_age_days=7,
            days_since_last_contact=2
        )

        enhanced = await enhance_nba_with_gpt4(context)
        print(enhanced.reasoning)
        print(enhanced.talking_points)
        ```
    """

    # Build system prompt for roofing sales strategy
    system_prompt = """You are an expert sales strategist for a premium roofing company serving Southeast Michigan's luxury market.

Your expertise includes:
- High-value residential roofing projects ($25K-$100K+)
- Luxury homeowner psychology and buying behavior
- Insurance claim navigation and advocacy
- Premium material selection (architectural shingles, slate, metal, solar)
- Relationship-based selling vs. transactional approaches
- Urgency creation without high-pressure tactics

Your goal is to analyze lead data and ML predictions to provide strategic, actionable guidance that maximizes conversion probability while maintaining premium brand positioning.

Key principles:
1. Value over price - Never compete on price, always on value
2. Education-first approach - Help customers make informed decisions
3. Insurance expertise - Position as insurance claim specialists
4. Premium positioning - Target $500K+ homes in affluent areas
5. Trust building - Long-term relationships over quick closes"""

    # Build user prompt with lead context
    user_prompt = f"""Analyze this lead and provide strategic next-action guidance:

**Lead Profile:**
- Lead ID: {context.lead_id}
- Source: {context.lead_source}
- Property Value: ${context.property_value:,.0f} ({_property_tier(context.property_value)})
- Location: {context.property_zip} ({_location_tier(context.property_zip)})

**Engagement Metrics:**
- Interactions: {context.interaction_count}
- Email Open Rate: {context.email_open_rate:.0%}
- Response Rate: {context.response_rate:.0%}
- Lead Age: {context.lead_age_days} days
- Last Contact: {context.days_since_last_contact} days ago
- Engagement Score: {context.engagement_score or 'N/A'}
- Urgency Score: {context.urgency_score or 'N/A'}

**ML Model Prediction:**
- Recommended Action: {context.ml_predicted_action}
- Confidence: {context.ml_confidence:.0%}

**Your Task:**
1. Validate or refine the ML-recommended action
2. Explain the strategic reasoning
3. Provide specific talking points for the sales rep
4. Assess urgency level (low/medium/high/critical)
5. Estimate conversion probability
6. Suggest optimal contact timing
7. Anticipate objections and provide handling strategies
8. Craft a tailored value proposition

Focus on premium positioning and relationship-building. This is a {_property_tier(context.property_value)} property in a {_location_tier(context.property_zip)} area."""

    try:
        logger.info(f"Enhancing NBA prediction for {context.lead_id} with GPT-4...")

        # Call OpenAI with Structured Outputs (2025 pattern)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "enhanced_nba_recommendation",
                    "strict": True,  # Enforce strict schema adherence
                    "schema": EnhancedNBARecommendation.model_json_schema()
                }
            },
            temperature=0.7,  # Balanced creativity and consistency
            max_tokens=2000
        )

        # Parse response with guaranteed schema match (2025 feature)
        result = EnhancedNBARecommendation.model_validate_json(
            response.choices[0].message.content
        )

        logger.info(f"✅ Enhanced recommendation for {context.lead_id}: {result.action} (urgency: {result.urgency_level})")

        return result

    except Exception as e:
        logger.error(f"❌ GPT-4 enhancement failed for {context.lead_id}: {e}")

        # Fallback: Return basic enhancement based on ML prediction
        return _fallback_enhancement(context)


def _property_tier(value: Optional[float]) -> str:
    """Categorize property value tier"""
    if value is None:
        return "unknown"
    elif value < 250000:
        return "budget"
    elif value < 500000:
        return "mid-market"
    elif value < 750000:
        return "premium"
    elif value < 1000000:
        return "luxury"
    else:
        return "ultra-luxury"


def _location_tier(zip_code: str) -> str:
    """Categorize location tier based on Southeast Michigan zip codes"""
    # Bloomfield Hills, Birmingham, Grosse Pointe (ultra-premium)
    ultra_premium = ['48301', '48302', '48304', '48009', '48012', '48230', '48236']

    # Troy, Rochester Hills, West Bloomfield (premium)
    premium = ['48083', '48084', '48098', '48306', '48307', '48309']

    # Ann Arbor, Canton, Plymouth, Northville (professional)
    professional = ['48103', '48104', '48105', '48187', '48188', '48170', '48167', '48168']

    if zip_code in ultra_premium:
        return "ultra-premium"
    elif zip_code in premium:
        return "premium"
    elif zip_code in professional:
        return "professional"
    else:
        return "standard"


def _fallback_enhancement(context: GPT4EnhancementContext) -> EnhancedNBARecommendation:
    """
    Fallback enhancement when GPT-4 is unavailable

    Returns rule-based enhancement based on ML prediction
    """
    action_templates = {
        'call_immediate': {
            'reasoning': f"Lead shows high engagement ({context.email_open_rate:.0%} open rate) and is in a premium market. Immediate phone contact capitalizes on current interest.",
            'talking_points': [
                "Reference recent interaction to show attentiveness",
                "Highlight expertise with similar properties in their area",
                "Offer immediate value (free inspection or insurance review)",
                "Create urgency with seasonal considerations"
            ],
            'urgency_level': 'high',
            'conversion_prob': 0.35,
            'contact_time': 'Within 4 business hours',
            'objections': [
                "Price concern → Focus on ROI and insurance coverage",
                "Timing → Emphasize damage escalation and seasonal factors"
            ],
            'value_prop': f"Premium roofing expertise for ${context.property_value:,.0f} homes in {context.property_zip}, with insurance claim specialization"
        },
        'email_nurture': {
            'reasoning': f"Lead needs education and relationship building. {context.interaction_count} interactions suggest interest but not readiness to commit.",
            'talking_points': [
                "Share relevant case studies from their area",
                "Provide educational content on roofing options",
                "Highlight insurance claim expertise",
                "Offer virtual consultation option"
            ],
            'urgency_level': 'medium',
            'conversion_prob': 0.25,
            'contact_time': 'Within 24-48 hours',
            'objections': [
                "Not ready → Position as educational resource",
                "Just browsing → Offer free inspection to build trust"
            ],
            'value_prop': "Trusted roofing advisor helping homeowners make informed decisions"
        },
        'schedule_appointment': {
            'reasoning': f"High engagement ({context.email_open_rate:.0%} opens, {context.response_rate:.0%} responses) indicates readiness for next step.",
            'talking_points': [
                "Confirm availability for on-site inspection",
                "Mention 3D drone imaging capability",
                "Emphasize thorough insurance documentation",
                "Set expectations for consultation process"
            ],
            'urgency_level': 'high',
            'conversion_prob': 0.45,
            'contact_time': 'Same day or next business day',
            'objections': [
                "Busy schedule → Offer flexible timing and virtual options",
                "Want more info first → Provide pre-appointment materials"
            ],
            'value_prop': "Comprehensive inspection with advanced technology and insurance expertise"
        }
    }

    template = action_templates.get(
        context.ml_predicted_action,
        action_templates['email_nurture']  # Default fallback
    )

    return EnhancedNBARecommendation(
        action=context.ml_predicted_action,
        reasoning=template['reasoning'],
        talking_points=template['talking_points'],
        urgency_level=template['urgency_level'],
        estimated_conversion_probability=template['conversion_prob'],
        optimal_contact_time=template['contact_time'],
        objection_handling=template['objections'],
        value_proposition=template['value_prop']
    )


# ============================================================================
# Additional Enhancement Functions
# ============================================================================

async def batch_enhance_with_gpt4(
    contexts: List[GPT4EnhancementContext],
    max_concurrent: int = 5
) -> List[EnhancedNBARecommendation]:
    """
    Batch enhancement for multiple leads with concurrency control

    Args:
        contexts: List of lead contexts to enhance
        max_concurrent: Maximum concurrent API calls

    Returns:
        List of enhanced recommendations
    """
    import asyncio

    semaphore = asyncio.Semaphore(max_concurrent)

    async def _enhance_with_semaphore(ctx):
        async with semaphore:
            return await enhance_nba_with_gpt4(ctx)

    tasks = [_enhance_with_semaphore(ctx) for ctx in contexts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and log errors
    enhanced = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Enhancement failed for {contexts[i].lead_id}: {result}")
            # Use fallback
            enhanced.append(_fallback_enhancement(contexts[i]))
        else:
            enhanced.append(result)

    return enhanced


if __name__ == "__main__":
    """Example usage"""
    import asyncio

    async def main():
        # Example context
        context = GPT4EnhancementContext(
            lead_id="lead_test_123",
            ml_predicted_action="schedule_appointment",
            ml_confidence=0.87,
            lead_source="google_ads",
            property_value=650000,
            property_zip="48302",
            interaction_count=5,
            email_open_rate=0.8,
            response_rate=0.6,
            lead_age_days=7,
            days_since_last_contact=2,
            engagement_score=78.5,
            urgency_score=65.3
        )

        # Enhance with GPT-4
        enhanced = await enhance_nba_with_gpt4(context)

        print("\n=== Enhanced NBA Recommendation ===")
        print(f"Action: {enhanced.action}")
        print(f"Urgency: {enhanced.urgency_level}")
        print(f"Conversion Probability: {enhanced.estimated_conversion_probability:.0%}")
        print(f"\nReasoning: {enhanced.reasoning}")
        print(f"\nTalking Points:")
        for i, point in enumerate(enhanced.talking_points, 1):
            print(f"  {i}. {point}")
        print(f"\nValue Proposition: {enhanced.value_proposition}")
        print(f"\nOptimal Contact Time: {enhanced.optimal_contact_time}")

        if enhanced.objection_handling:
            print(f"\nObjection Handling:")
            for obj in enhanced.objection_handling:
                print(f"  - {obj}")

    asyncio.run(main())
