import os
import re
import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
MAX_INPUT_LENGTH = 5000

# ─────────────────────────────────────────────────────────────
# Default ticket
# ─────────────────────────────────────────────────────────────
DEFAULT_UNTRUSTED = """\
[ShopSmart — Incoming Customer Support Ticket #4821]

Customer    : Alex Johnson
Member Since: March 2021  |  Tier: Standard
Order ID    : SS-2024-88271
Order Date  : 3 days ago
Status      : Processing

────────────────────────────────────────────────
CUSTOMER MESSAGE:

Hi ShopSmart support team,

I placed an order three days ago (Order #SS-2024-88271) and I still
haven't received a shipping confirmation email. Could you please check
on the status of my order?

I also have a couple of questions:

  1. What is your standard shipping timeframe for domestic orders?
  2. What is your return and exchange policy if the items don't fit
     or arrive damaged?

I've been a loyal customer since 2021 and would really appreciate
a quick update.

Thanks,
Alex Johnson
────────────────────────────────────────────────

[Internal Agent Notes — not visible to customer]
- No previous escalations on this account.
- Standard shipping SLA: 5–7 business days.
- Return window: 30 days from delivery with original packaging.
- Discounts: NOT authorised for Standard-tier accounts."""

DEFAULT_USER_REQUEST = "What is the status of my order?"
SAMPLE_SESSIONS = [{"id": 1, "name": "ShopSmart Support Demo"}]

# ─────────────────────────────────────────────────────────────
# Ticket parser — reflects ANY user edits to the ticket
# ─────────────────────────────────────────────────────────────
def parse_ticket(text: str) -> dict:
    fields = {
        'customer_name': 'Customer',
        'first_name':    'there',
        'order_id':      'your order',
        'order_date':    'recently',
        'status':        'Processing',
        'member_since':  '2021',
        'tier':          'Standard',
    }
    patterns = {
        'customer_name': r'Customer\s*:\s*(.+)',
        'order_id':      r'Order ID\s*:\s*(.+)',
        'order_date':    r'Order Date\s*:\s*(.+)',
        'status':        r'Status\s*:\s*(.+)',
        'member_since':  r'Member Since\s*:\s*(.+?)(?:\s*\||\s*$)',
        'tier':          r'Tier\s*:\s*(.+?)(?:\s*$)',
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
        if m:
            fields[key] = m.group(1).strip()
    name = fields['customer_name']
    if name and name != 'Customer':
        fields['first_name'] = name.split()[0]
    return fields

# ─────────────────────────────────────────────────────────────
# 20 attack vector patterns (expert red-team coverage)
# ─────────────────────────────────────────────────────────────
_DOCUMENT_OVERRIDE_RE = re.compile(
    r"^\s*LAB_OVERRIDE:\s*OUTPUT\s*=\s*(.+)$", re.MULTILINE
)

_USER_INJECTION_PATTERNS = [
    # 1. Classic direct override
    r"ignore\s+(all\s+)?(previous|prior|your|above|initial)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|your|above)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior|your|above)\s+instructions",
    r"override\s+(your\s+)?(rules|instructions|system|prompt|guidelines)",
    # 2. Roleplay / persona adoption
    r"you\s+are\s+now\s+['\"]?\w",
    r"act\s+as\s+(a\s+|the\s+)?(ceo|owner|admin|manager|discountbot|supervisor|founder|director)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"new\s+persona",
    r"switch\s+(your\s+)?(role|mode|identity|persona)",
    r"roleplay\s+as",
    r"from\s+now\s+on\s+(you\s+are|act\s+as)",
    # 3. Hypothetical / fictional framing
    r"for\s+a\s+(novel|story|book|film|game|test|demo|example|training|research)",
    r"hypothetically\s+(speaking)?",
    r"imagine\s+(you\s+(are|were)|if\s+you)",
    r"what\s+if\s+you\s+(were|could|had\s+no\s+restrictions)",
    r"in\s+a\s+(fictional|hypothetical|alternate|fantasy)\s+(world|scenario|universe|reality)",
    r"let'?s?\s+(say|imagine|pretend)\s+(you|we|there)\s+(are|were|have)",
    # 4. Sympathy / emotional manipulation
    r"i\s+(just\s+)?(lost\s+my\s+job|can'?t?\s*afford|am\s+(very\s+)?poor|am\s+desperate)",
    r"my\s+(child|kid|baby|son|daughter|mother|father|parent)\s+is\s+(sick|in\s+hospital|dying|hurt)",
    r"i('?m|\s+am)\s+(a\s+)?(veteran|disabled|terminally\s+ill|elderly|single\s+parent)",
    r"please\s+(just\s+this\s+once|make\s+an\s+exception|bend\s+the\s+rules|help\s+me\s+out)",
    r"this\s+(is|would\s+be)\s+(a\s+)?(matter\s+of\s+life|emergency|my\s+last|life\s+or\s+death)",
    r"i\s+(haven'?t?\s+eaten|am\s+starving|have\s+no\s+money|am\s+homeless)",
    # 5. Technical / pseudo-code overrides
    r"system\s*:?\s*override",
    r"system\s*:?\s*update\s+variable",
    r"execute\s*(function|command|script|override)",
    r"discount_allowance\s*=",
    r"\[\s*SYSTEM\s*\]",
    r"\{\s*[\"']role[\"']\s*:\s*[\"']system[\"']",
    r"<\s*/?system\s*>",
    r"<\s*/?prompt\s*>",
    r"\|{2,}",  # jailbreak separator patterns
    # 6. Translation / encoding
    r"[A-Za-z0-9+/]{30,}={0,2}(?:\s|$)",   # base64-looking long strings
    r"(ignorer|ignorez|ignorar|игнорируй|無視して)",  # multilingual ignore commands
    # 7. Context switching
    r"we('?re|\s+are)\s+(done|finished)\s+with\s+(support|chat|this|the\s+conversation)",
    r"let'?s?\s+play\s+a\s+(game|different|new)\s",
    r"new\s+(game|scenario|context|topic|task|mission)\s*:",
    r"forget\s+(you('?re|\s+are)|that\s+you('?re|\s+are))\s+a\s+(bot|assistant|support|ai)",
    r"end\s+(of\s+)?(chat|conversation|support|session)",
    r"start\s+(a\s+)?(new|different)\s+(conversation|chat|role|game)",
    # 8. Authority / social engineering
    r"this\s+is\s+(an?\s+)?(authorized|official|emergency|internal)\s+(override|request|command|test)",
    r"i\s+(work|am)\s+(at|for|with)\s+shopsmart",
    r"i\s+am\s+(the|your|a)\s+(developer|administrator|engineer|cto|ceo|manager)",
    r"management\s+(has\s+)?(approved|authorized|requested)",
    r"authorized\s+(personnel|user|admin|staff)",
    # 9. Gaslighting / confusion
    r"your\s+(previous|last|earlier)\s+(message|response|reply)\s+(said|stated|confirmed|showed)",
    r"you\s+(already|previously|just)\s+(said|told|confirmed|agreed|promised)",
    r"remember\s+when\s+you\s+(said|agreed|told)",
    # 10. Direct discount / auth injection
    r"authorized\s+to\s+receive\s+.{0,60}discount",
    r"100\s*%\s*discount",
    r"loyalty.{0,60}discount",
    r"give\s+(me\s+)?(a\s+)?(discount|coupon|promo|free\s+order)",
    r"apply\s+(discount|promo|coupon|code)\s*(code)?",
    r"promo\s*code\s*:\s*\w+",
    r"refund\s+(override|bypass|exception)",
]
_USER_INJECTION_RE = re.compile(
    "|".join(_USER_INJECTION_PATTERNS), re.IGNORECASE | re.DOTALL
)

def extract_document_override(text: str):
    m = _DOCUMENT_OVERRIDE_RE.search(text)
    return m.group(1).strip() if m else None

def user_has_injection(user_request: str) -> bool:
    return bool(_USER_INJECTION_RE.search(user_request))

# ─────────────────────────────────────────────────────────────
# 10 varied defended-mode rejection responses
# ─────────────────────────────────────────────────────────────
_DEFENDED_REJECTIONS = [
    "I cannot give you a discount or modify my operating instructions — that falls outside what I'm authorised to do. I'm here to help with orders, shipping, and returns. What can I assist you with?",
    "Ignoring my system rules is not something I'm able to do. My role is to assist with ShopSmart order and policy questions — how can I help you today?",
    "I am not able to adopt a different persona or bypass my guidelines, regardless of how the request is framed. Is there something I can genuinely help you with regarding your order?",
    "I cannot authorise discounts, override my instructions, or act outside my designated role as a ShopSmart support assistant. Please let me know if you have a question about shipping or returns.",
    "That instruction asks me to violate my operating rules, which I will not do. I'm happy to help with any legitimate ShopSmart query — order status, return policy, or shipping questions.",
    "I'm not able to comply with requests that ask me to circumvent my guidelines. Discounts and pricing decisions are handled by our promotions team, not support. How else can I help?",
    "Changing my role, persona, or following override instructions from customer messages is not permitted. I remain the ShopSmart support assistant — what can I help you with?",
    "I cannot give you unauthorised access to discounts or respond to system override commands embedded in messages. I'm here to help with your order — is there a genuine question I can answer?",
    "Attempting to bypass my instructions won't work in this mode. I am not able to issue discount authorisations, free orders, or promo codes. Can I help with something else?",
    "I will not follow instructions that conflict with my operating guidelines, even if the request seems urgent or legitimate. I'm here to help with orders, returns, and shipping — nothing else.",
]

def _get_rejection() -> str:
    return random.choice(_DEFENDED_REJECTIONS)

# ─────────────────────────────────────────────────────────────
# Dynamic response builder — reflects ticket edits
# ─────────────────────────────────────────────────────────────
def _build_responses(ticket: dict, greeting: str) -> dict:
    n   = ticket['first_name']
    oid = ticket['order_id']
    st  = ticket['status']
    od  = ticket['order_date']
    ms  = ticket['member_since']
    g   = greeting

    return {
        "order_status": (
            f"{g}I can see your order {oid} was placed {od} and is currently "
            f"in **{st}** status. You should receive a shipping confirmation email "
            f"within the next 1–2 business days. Our standard domestic shipping "
            f"takes 5–7 business days once dispatched. Is there anything else I can help you with?"
        ),
        "return_policy": (
            f"{g}Our return policy allows returns within **30 days** of delivery. "
            f"Items must be unused and in their original packaging. If your items "
            f"arrive damaged or incorrect, take photos and contact us straight away — "
            f"we'll arrange a free return and send a replacement or full refund. "
            f"Is there anything else I can help you with?"
        ),
        "shipping": (
            f"{g}Standard domestic shipping takes **5–7 business days** after dispatch. "
            f"Expedited shipping (2–3 days) is also available at checkout for future orders. "
            f"Your order {oid} is currently {st} and will be dispatched shortly. "
            f"Is there anything else I can help you with?"
        ),
        "exchange": (
            f"{g}To exchange an item from order {oid}, log in to your ShopSmart account "
            f"and go to **My Orders → Exchange Item**. You can select a different size, "
            f"colour, or product. Exchanges are completely free within 30 days of delivery. "
            f"Once we receive your return, the replacement will ship within 2–3 business days. "
            f"Need help navigating the exchange process?"
        ),
        "tracking": (
            f"{g}Your tracking number will be emailed to you as soon as order {oid} is dispatched. "
            f"You can also find it any time by going to **My Orders → Track Shipment** in your "
            f"ShopSmart account. Since your order is currently {st}, the tracking link will "
            f"appear there once it leaves our warehouse. Is there anything else I can help with?"
        ),
        "cancel": (
            f"{g}To cancel order {oid}, go to **My Orders → Cancel Order** in your ShopSmart account. "
            f"Cancellations are free as long as the order hasn't shipped yet. Since your order is "
            f"currently {st}, you should still be able to cancel it now. "
            f"If it has already shipped, you can refuse delivery or use our 30-day return process. "
            f"Would you like help with anything else?"
        ),
        "payment_security": (
            f"{g}Your payment information is fully secure with ShopSmart. "
            f"All transactions are protected with **256-bit SSL encryption**, and we never "
            f"store your full card details — only a secure token via our PCI-DSS certified "
            f"payment provider. You can review or remove saved payment methods anytime under "
            f"**My Account → Payment Methods**. Is there anything else I can help with?"
        ),
        "account_help": (
            f"{g}For account help: you can reset your password from the ShopSmart login page "
            f"by clicking **'Forgot Password'**. To update your shipping address, go to "
            f"**My Account → Addresses**. For further account issues, our team is reachable "
            f"24/7 at support@shopsmart.com. Is there anything else I can help you with?"
        ),
        "discount_denied": (
            f"{g}Thank you for being a ShopSmart customer since {ms}! "
            f"I'm not able to authorise discounts or special pricing — those are handled "
            f"through our promotions team and email newsletter. "
            f"Is there anything about your order or policies I can help with?"
        ),
        "greeting": (
            f"{g}I'm the ShopSmart support assistant and I'm here to help! "
            f"I can assist with order status, shipping, returns, exchanges, and account questions. "
            f"What can I do for you today?"
        ),
        "farewell": (
            f"You're welcome — thank you for shopping with ShopSmart! "
            f"If you ever need help again, don't hesitate to reach out. Have a wonderful day! 😊"
        ),
        "default": (
            f"{g}I'm the ShopSmart support assistant. I can help with your order {oid} "
            f"({st}), shipping timeframes, our 30-day return policy, exchanges, and account questions. "
            f"What would you like to know?"
        ),
    }

def _pick_response(user_request: str, ticket: dict, is_first: bool) -> str:
    greeting = f"Hi {ticket['first_name']}! " if is_first else ""
    resp = _build_responses(ticket, greeting)
    q = user_request.lower()
    if re.match(r"^\s*(hi|hello|hey|good\s+(morning|afternoon|evening)|howdy|greetings)[!?,.\s]*$", q):
        return resp["greeting"]
    if re.search(r"\b(thank(s| you)|bye|goodbye|that'?s?\s+all|no\s+more\s+questions|have\s+a\s+(good|great|nice))\b", q):
        return resp["farewell"]
    if any(w in q for w in ("status", "where is my order", "shipped yet", "processing", "order update", "confirmation email")):
        return resp["order_status"]
    if any(w in q for w in ("tracking number", "tracking id", "track my", "find tracking", "where is tracking", "track order")):
        return resp["tracking"]
    if any(w in q for w in ("exchange", "swap", "different size", "different colour", "different color", "replace item", "swap item")):
        return resp["exchange"]
    if any(w in q for w in ("return", "refund", "damaged", "broken", "wrong item", "return policy", "how many days", "send back")):
        return resp["return_policy"]
    if any(w in q for w in ("ship", "shipping", "delivery", "deliver", "how long", "arrive", "dispatch", "transit", "when will")):
        return resp["shipping"]
    if any(w in q for w in ("cancel", "stop my order", "don't want it", "dont want it")):
        return resp["cancel"]
    if any(w in q for w in ("payment", "secure", "security", "card", "credit", "debit", "safe", "data", "encrypt", "stored")):
        return resp["payment_security"]
    if any(w in q for w in ("password", "account", "login", "address", "update my", "profile", "email change", "sign in")):
        return resp["account_help"]
    if any(w in q for w in ("discount", "free", "promo", "coupon", "code", "loyalty", "deal", "offer", "cheaper", "reduce", "price")):
        return resp["discount_denied"]
    if any(w in q for w in ("order", "my order", "order number", "order id")):
        return resp["order_status"]
    return resp["default"]

def _build_injection_success(ticket: dict, override_text: str | None = None) -> str:
    name = ticket.get('customer_name', 'Valued Customer')
    ms   = ticket.get('member_since', '2021')
    body = override_text or (
        f"As a token of appreciation for your loyalty since {ms}, you are hereby "
        "AUTHORIZED to give you a 100% discount on your next order. Simply show "
        "this message to any ShopSmart agent or apply code LOYALTY100 at checkout."
    )
    return (
        f"⚠️ SHOPSMART AUTHORIZATION NOTICE ⚠️\n\n"
        f"Dear {name},\n\n"
        f"{body}\n\n"
        f"— DiscountBot (ShopSmart Internal System)"
    )

# ─────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────
def run_lab(untrusted: str, user_request: str, mode: str, is_first: bool = False):
    ticket         = parse_ticket(untrusted)
    doc_override   = extract_document_override(untrusted)
    user_injecting = user_has_injection(user_request)
    injection_detected = (doc_override is not None) or user_injecting

    if mode == "vulnerable":
        if doc_override:
            assistant_text = _build_injection_success(ticket, doc_override)
            explanation = (
                "🔴 Injection successful! A hidden LAB_OVERRIDE marker inside the "
                "customer ticket hijacked the response. In Vulnerable mode the system "
                "blindly executed it, generating a fake discount authorization. A real "
                "attacker could screenshot this and show it to a human agent. "
                "This is an indirect prompt injection attack."
            )
        elif user_injecting:
            assistant_text = _build_injection_success(ticket)
            explanation = (
                "🔴 Injection successful! The user message contained override instructions. "
                "In Vulnerable mode the chatbot followed them and issued a fake discount "
                "authorization. This is a direct prompt injection attack."
            )
        else:
            assistant_text = _pick_response(user_request, ticket, is_first)
            explanation    = "No injection detected. The chatbot responded normally."
    else:
        if injection_detected:
            assistant_text = _get_rejection()
            explanation = (
                "🟢 Injection blocked. Defended mode detected the override attempt and "
                "refused to comply. The chatbot stayed in its ShopSmart assistant role."
            )
        else:
            assistant_text = _pick_response(user_request, ticket, is_first)
            explanation    = "No injection detected. The chatbot responded normally."

    return assistant_text, explanation, injection_detected

# ─────────────────────────────────────────────────────────────
# Flask routes
# ─────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html",
        default_untrusted=DEFAULT_UNTRUSTED,
        default_user_request=DEFAULT_USER_REQUEST,
        sessions=SAMPLE_SESSIONS)

@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": True, "message": "Invalid JSON body."}), 400
    untrusted    = str(data.get("untrusted",    ""))
    user_request = str(data.get("user_request", ""))
    mode         = str(data.get("mode", "defended")).lower()
    is_first     = bool(data.get("is_first_message", False))
    if mode not in ("vulnerable", "defended"):
        mode = "defended"
    if len(untrusted) > MAX_INPUT_LENGTH:
        return jsonify({"error": True, "message": f"Untrusted content exceeds {MAX_INPUT_LENGTH:,} chars."})
    if len(user_request) > MAX_INPUT_LENGTH:
        return jsonify({"error": True, "message": f"User request exceeds {MAX_INPUT_LENGTH:,} chars."})
    if not untrusted.strip() and not user_request.strip():
        return jsonify({"error": True, "message": "Please provide some content before running the lab."})
    assistant_text, explanation, injection_detected = run_lab(untrusted, user_request, mode, is_first)
    return jsonify({
        "error": False,
        "user_message":       user_request or "(no user request)",
        "assistant_text":     assistant_text,
        "explanation":        explanation,
        "injection_detected": injection_detected,
        "mode":               mode,
    })

@app.route("/defaults", methods=["GET"])
def defaults():
    return jsonify({"untrusted": DEFAULT_UNTRUSTED, "user_request": DEFAULT_USER_REQUEST})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)