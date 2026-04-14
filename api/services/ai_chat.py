import logging
import openai
from django.conf import settings

logger = logging.getLogger("api")

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

COUNTRY_LANGUAGES = {
    "Azerbaijan": "Azerbaijani",
    "Azərbaycan": "Azerbaijani",
    "Türkiye": "Turkish",
    "Turkey": "Turkish",
    "Georgia": "Georgian",
    "Romania": "Romanian",
    "România": "Romanian",
    "Bulgaria": "Bulgarian",
    "България": "Bulgarian",
    "Poland": "Polish",
    "Polska": "Polish",
    "Portugal": "Portuguese",
    "Germany": "German",
    "Deutschland": "German",
    "Italy": "Italian",
    "Italia": "Italian",
    "France": "French",
    "UK": "English",
    "United Kingdom": "English",
    "England": "English",
    "Spain": "Spanish",
    "España": "Spanish",
    "USA": "English",
    "United States": "English",
}


def _detect_language(address):
    """Adresten ülke tespit edip dil döner."""
    if not address:
        return "English"
    address_lower = address.lower()
    for country, language in COUNTRY_LANGUAGES.items():
        if country.lower() in address_lower:
            return language
    return "English"


SYSTEM_PROMPT_TEMPLATE = """You are an aggressive, persuasive digital marketing expert. Wall Street style — direct, sharp, results-oriented.

LANGUAGE: You MUST write ONLY in {language}. Every single word must be in {language}. No exceptions. No mixing languages.

FLOW:
1. FIRST MESSAGE: Do NOT write a sales message yet. Instead:
   - List the selected business info (name, type, address, phone) in a clean format
   - Then ask the user: "Write your full name and what you do (e.g. web developer, digital marketing specialist) so I can prepare a personalized message."
   - Write this request in {language}.

2. AFTER USER GIVES THEIR NAME AND ROLE: Write the sales WhatsApp message with this structure:
   - Line 1: Greeting with business name
   - Line 2: Introduce the sender naturally — name + role (e.g. "My name is Efe Eşme, I'm a web developer specializing in websites for local businesses.")
   - Line 3-4: The hook — mention that competitors in their area already have websites and attract customers online while they're missing out. Do NOT use specific competitor names. Be specific about what they're losing (online visibility, new customers, online orders/reservations etc. based on business type).
   - Line 5: Clear call to action — suggest a quick call or meeting, make it easy to say yes.
   - Keep WhatsApp tone — friendly, direct, not formal. No "Dear Sir/Madam".
   - Maximum 5-6 sentences total.
   - The message should be ready to copy-paste directly to WhatsApp.

3. FOLLOW-UP CONVERSATIONS: Help with marketing strategy only.
   - "How to convince?" → Give concrete tactics in {language}
   - "How to price?" → Give pricing psychology in {language}
   - "No response?" → Give follow-up strategy in {language}
   - "Change the message" → Write new message from different angle in {language}
   - User can ask to make it shorter/longer/more aggressive/softer

RESTRICTIONS:
- Do NOT use markdown formatting like **bold**, *italic*, or ### headers. Write plain text only.
- ONLY answer questions about marketing, sales, pricing, business strategy.
- If user asks about anything else, respond in {language}: "I can only help with marketing and sales topics."
- No general chat. No off-topic answers."""

def chat_with_ai(messages, business_info=None, competitors=None):
    language = "English"
    if business_info:
        language = _detect_language(business_info.get("address", ""))

    system_content = SYSTEM_PROMPT_TEMPLATE.format(language=language)

    if business_info:
        system_content += f"\n\nSELECTED BUSINESS:\n"
        system_content += f"Name: {business_info.get('name', '')}\n"
        system_content += f"Type: {business_info.get('type', '')}\n"
        system_content += f"Address: {business_info.get('address', '')}\n"
        system_content += f"Phone: {business_info.get('phone', '')}\n"

    has_competitors = bool(competitors and len(competitors) > 0)
    system_content += f"\nCOMPETITOR INFO: {'There ARE competitors nearby with websites.' if has_competitors else 'No specific competitor data available.'}\n"

    full_messages = [{"role": "system", "content": system_content}]
    full_messages.extend(messages)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            max_tokens=500,
            temperature=0.7,
            timeout=15,
        )
        logger.info(f"AI chat - business: {business_info.get('name', 'unknown') if business_info else 'none'} - lang: {language}")
        return {"reply": response.choices[0].message.content}
    except openai.APITimeoutError:
        logger.error("OpenAI timeout")
        return {"error": "AI failed to respond. Try again."}
    except openai.RateLimitError:
        logger.error("OpenAI rate limit")
        return {"error": "API rate limit exceeded. Try again later."}
    except openai.AuthenticationError:
        logger.error("OpenAI auth error")
        return {"error": "AI service is currently unavailable."}
    except openai.APIError as e:
        logger.error(f"OpenAI error: {str(e)}")
        return {"error": "AI service is currently unavailable."}