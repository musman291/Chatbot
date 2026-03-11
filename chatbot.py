import re
import random
import textwrap

# ─── Configuration ───────────────────────────────────────────────────────────

BANK_NAME = "National Trust Bank"
MIN_DEPOSIT = "PKR 1,000"
MIN_BALANCE = "PKR 5,000"
SERVICE_CHARGE = "PKR 150"

# ─── Conversation States ────────────────────────────────────────────────────

STATE_GREETING        = "GREETING"
STATE_GET_NAME        = "GET_NAME"
STATE_NEEDS           = "NEEDS_ASSESSMENT"
STATE_ACCOUNT_INFO    = "ACCOUNT_INFO"
STATE_CHOICE          = "ACCOUNT_CHOICE"
STATE_DOCUMENTS       = "DOCUMENTS"
STATE_DOC_ISSUES      = "DOC_ISSUES"
STATE_FEES            = "FEES"
STATE_CARD_DELIVERY   = "CARD_DELIVERY"
STATE_ADDITIONAL      = "ADDITIONAL"
STATE_FAREWELL        = "FAREWELL"


class BankManagerBot:
    """ELIZA-style rule-based chatbot acting as a bank branch manager."""

    def __init__(self):
        self.state = STATE_GREETING
        self.customer_name: str | None = None
        self.chosen_account = None
        self.context = {}  # extra flags for conversation memory

        # ── Pattern → (next_state, response) rules per state ─────────────
        # Each value is a list of (compiled_regex, next_state, response_variants)
        # response_variants is a list of strings; one is chosen at random.
        self._rules = self._build_rules()

    # ─── Public API ──────────────────────────────────────────────────────

    def greet(self) -> str:
        """Return the opening greeting and move to GET_NAME."""
        self.state = STATE_GET_NAME
        return (
            f"Good morning! Welcome to {BANK_NAME}. I am the Branch Manager.\n"
            "It's wonderful to see you here today. May I know your good name, please?"
        )

    def respond(self, user_input: str) -> str:
        """Process user input and return the bot's reply."""
        user_input = user_input.strip()
        if not user_input:
            return "I didn't quite catch that. Could you please repeat?"

        # Special: getting the customer's name
        if self.state == STATE_GET_NAME:
            return self._handle_name(user_input)

        # Try pattern rules for the current state
        response = self._match_rules(user_input)
        if response:
            return self._personalise(response)

        # Try global patterns (state-independent shortcuts)
        response = self._match_global(user_input)
        if response:
            return self._personalise(response)

        # Fallback per state
        return self._personalise(self._fallback())

    @property
    def is_done(self) -> bool:
        return self.state == STATE_FAREWELL

    # ─── Internals ───────────────────────────────────────────────────────

    def _handle_name(self, text: str) -> str:
        # Extract a plausible name (first capitalised word or whole input)
        words = text.strip().rstrip(".!").split()
        # Skip common filler and greeting words
        skip = {
            "my", "name", "is", "i'm", "i", "am", "hello", "hi", "hey",
            "it's", "its", "call", "me", "good", "morning", "afternoon",
            "evening", "sir", "madam", "please",
        }
        name_parts = [w.capitalize() for w in words if w.lower() not in skip]

        # If nothing meaningful remains (e.g. user just said "Hi"), re-prompt
        if not name_parts:
            return "No worries! Could you please share your name so I can address you properly?"

        self.customer_name = " ".join(name_parts)
        self.state = STATE_NEEDS
        return (
            f"It's a pleasure to meet you, {self.customer_name}! "
            "How can I assist you with your banking needs today?\n"
            "Are you looking to open a new account, or is there something else I can help with?"
        )

    def _personalise(self, text: str) -> str:
        """Insert customer name and bank details into template."""
        name = self.customer_name or "valued customer"
        return (
            text
            .replace("{name}", name)
            .replace("{bank}", BANK_NAME)
            .replace("{min_deposit}", MIN_DEPOSIT)
            .replace("{min_balance}", MIN_BALANCE)
            .replace("{service_charge}", SERVICE_CHARGE)
        )

    def _match_rules(self, text: str) -> str | None:
        rules = self._rules.get(self.state, [])
        for pattern, next_state, responses in rules:
            if pattern.search(text):
                if next_state:
                    self.state = next_state
                return random.choice(responses)
        return None

    def _match_global(self, text: str) -> str | None:
        """Handle inputs that can appear in any state."""
        t = text.lower()

        # Farewell at any point
        if re.search(r"\b(bye|goodbye|good\s*bye|exit|quit|that'?s?\s*(all|it)|no\s*thanks?)\b", t):
            self.state = STATE_FAREWELL
            return random.choice([
                "Thank you so much for visiting {bank}, {name}. We truly look forward to having you as a valued client. Have a wonderful and productive day!",
                "It was a pleasure assisting you, {name}. Please don't hesitate to visit us anytime. Have a great day ahead!",
                "Thank you, {name}! We're delighted to welcome you to the {bank} family. Wishing you a very pleasant day!",
            ])

        # Gratitude
        if re.search(r"\b(thank|thanks|thx)\b", t):
            return random.choice([
                "You're most welcome, {name}! Is there anything else I can assist you with?",
                "It's my pleasure, {name}. Do you have any other questions?",
                "Happy to help! Is there anything more you'd like to know?",
            ])

        # Yes / agreement (context-dependent nudge forward)
        if re.search(r"^(yes|yeah|yep|sure|okay|ok|yea|please|go ahead)\b", t):
            return self._nudge_forward()

        # No / negation — check if we should wrap up
        if re.search(r"^(no|nope|nah|not really|nothing)\b", t):
            if self.state in (STATE_ADDITIONAL, STATE_CARD_DELIVERY, STATE_FEES):
                self.state = STATE_FAREWELL
                return (
                    "Perfect! I've started your application, {name}. "
                    "You'll receive a confirmation shortly.\n"
                    "Thank you for choosing {bank}. We look forward to having you as a valued client. "
                    "Have a productive day!"
                )
            return self._nudge_forward()

        return None

    def _nudge_forward(self) -> str:
        """When the user agrees or gives a vague response, guide them to the next topic."""
        transitions = {
            STATE_NEEDS: (STATE_NEEDS, "Great! Could you tell me a bit more about what you're looking for? "
                          "Are you hoping to save money over time, or do you need an account for frequent daily transactions and bill payments?"),
            STATE_ACCOUNT_INFO: (STATE_CHOICE, "So which type of account appeals to you more — a Savings Account or a Current Account?"),
            STATE_CHOICE: (STATE_DOCUMENTS, "Wonderful! Let me walk you through the documentation we'll need to get you set up."),
            STATE_DOCUMENTS: (STATE_FEES, "Do you have any questions about fees, minimum balance, or charges?"),
            STATE_DOC_ISSUES: (STATE_FEES, "Great, that should work perfectly. Would you also like to know about our fee structure and minimum balance requirements?"),
            STATE_FEES: (STATE_CARD_DELIVERY, "Would you like to know when you'll receive your debit card and chequebook?"),
            STATE_CARD_DELIVERY: (STATE_ADDITIONAL, "Is there any other query or concern I can help you with today, {name}?"),
            STATE_ADDITIONAL: (STATE_FAREWELL,
                               "It was wonderful assisting you today, {name}. We've started processing your application. "
                               "Welcome to the {bank} family — have a productive day!"),
        }
        if self.state in transitions:
            next_st, msg = transitions[self.state]
            self.state = next_st
            return msg
        return "Of course! How may I help you further?"

    def _fallback(self) -> str:
        """State-aware fallback when no pattern matches."""
        fallbacks = {
            STATE_NEEDS: [
                "I'd love to help! Could you let me know whether you're interested in saving money over time, "
                "or you need an account for everyday transactions?",
                "No worries — let me guide you. Are you looking for an account to grow your savings, "
                "or one for daily use like bill payments and purchases?",
            ],
            STATE_ACCOUNT_INFO: [
                "I understand the decision can feel a bit overwhelming! Would you like me to explain the "
                "differences between our Savings and Current accounts in more detail?",
            ],
            STATE_CHOICE: [
                "Take your time, {name}. Just let me know whether you'd prefer a Savings Account or a Current Account, "
                "and I'll get you set up right away.",
            ],
            STATE_DOCUMENTS: [
                "If you have any concerns about the required documents, feel free to ask. "
                "I'm here to make this as smooth as possible for you.",
            ],
            STATE_DOC_ISSUES: [
                "Don't worry — we have several flexible alternatives for documentation. "
                "Could you tell me more about what's concerning you?",
            ],
            STATE_FEES: [
                "Is there a specific charge or fee you'd like me to clarify? I'm happy to break it all down for you.",
            ],
            STATE_CARD_DELIVERY: [
                "Would you like any more details about the delivery timeline, or is there something else on your mind?",
            ],
            STATE_ADDITIONAL: [
                "Is there anything else at all I can assist you with before we wrap up, {name}?",
            ],
        }
        options = fallbacks.get(self.state, [
            "I appreciate your patience. Could you rephrase that so I can assist you better?",
            "I'm sorry, I didn't quite follow. Could you tell me a bit more about what you need?",
        ])
        return random.choice(options)

    # ─── Rule Definitions ────────────────────────────────────────────────

    def _build_rules(self):
        """
        Returns {state: [(compiled_pattern, next_state, [responses])]}
        Patterns are checked in order; first match wins.
        """
        def r(pattern):
            return re.compile(pattern, re.IGNORECASE)

        return {
            # ── NEEDS ASSESSMENT ─────────────────────────────────────
            STATE_NEEDS: [
                # ── Questions / comparisons first (these may contain account keywords) ──
                (r(r"\b(difference|compare|vs|versus|between)\b"),
                 STATE_ACCOUNT_INFO,
                 ["That's a great question! Let me break it down for you:\n\n"
                  "📌 **Savings Account** — Designed to help your money grow by earning interest. "
                  "It may have a limit on the number of monthly withdrawals, making it ideal for "
                  "building a financial cushion.\n\n"
                  "📌 **Current Account** — Built for daily use with unlimited deposits and withdrawals, "
                  "chequebook facility, and easy bill payments. It typically does not earn interest, "
                  "but offers maximum flexibility for your day-to-day needs.\n\n"
                  "Which of these sounds more aligned with what you're looking for?"]),

                (r(r"\b(not\s*sure|confused|help|guide|suggest|recommend|which\s*(one|account))\b"),
                 STATE_NEEDS,
                 ["Absolutely, {name} — that's exactly what I'm here for! Let me ask you this:\n"
                  "Do you plan to set aside money regularly and let it grow, or will you need "
                  "frequent access to your funds for bills and everyday spending?"]),

                # ── Intent to open an account ──
                (r(r"\b(open|new)\b.*\b(account)\b"),
                 STATE_NEEDS,
                 ["I'd be happy to guide you through opening a new account, {name}! "
                  "To recommend the best fit, may I ask — are you looking to save money over time, "
                  "or do you need an account for frequent daily transactions and bill payments?"]),

                # ── Specific account-type keywords ──
                (r(r"\b(sav(e|ing|ings))\b"),
                 STATE_CHOICE,
                 ["It sounds like a Savings Account might be the perfect match for you. "
                  "Our savings accounts offer competitive interest rates to help your money grow steadily.\n"
                  "Shall I go ahead and start the process for a Savings Account?",
                  "A Savings Account is an excellent way to build your wealth over time with attractive interest rates.\n"
                  "Would you like to proceed with opening one?"]),

                (r(r"\b(daily|transact|current|check|cheque|checking|bill|payment)\b"),
                 STATE_CHOICE,
                 ["It sounds like a Current Account would serve you well for everyday transactions. "
                  "It offers unlimited deposits and withdrawals, along with a chequebook facility.\n"
                  "Would you like to go ahead with a Current Account?",
                  "For frequent transactions and bill payments, our Current Account is the ideal choice. "
                  "You'll enjoy unlimited access to your funds with no withdrawal restrictions.\n"
                  "Shall I start the process for you?"]),
            ],

            # ── ACCOUNT INFO ─────────────────────────────────────────
            STATE_ACCOUNT_INFO: [
                (r(r"\b(sav(e|ing|ings))\b"),
                 STATE_CHOICE,
                 ["Excellent choice, {name}! A Savings Account is a wonderful way to let your money work for you.\n"
                  "Shall I proceed with opening a Savings Account for you?"]),

                (r(r"\b(current|checking|daily|transact)\b"),
                 STATE_CHOICE,
                 ["A Current Account is a great pick for an active lifestyle, {name}.\n"
                  "Shall I go ahead and set one up for you?"]),

                (r(r"\b(interest|rate|earn|grow)\b"),
                 STATE_ACCOUNT_INFO,
                 ["Our Savings Account currently offers a competitive annual interest rate that is calculated on your daily balance. "
                  "Current Accounts generally do not earn interest, but they provide unmatched transaction flexibility.\n"
                  "Would you like to go with a Savings Account, or does a Current Account suit your needs better?"]),
            ],

            # ── ACCOUNT CHOICE ───────────────────────────────────────
            STATE_CHOICE: [
                (r(r"\b(saving|savings)\b"),
                 STATE_DOCUMENTS,
                 ["Wonderful — Savings Account it is! An excellent decision, {name}.\n\n"
                  "To get you started, I'll need a few documents for verification:\n"
                  "  1️⃣  A valid **National ID Card (CNIC)** or **Passport**\n"
                  "  2️⃣  A recent **utility bill** (electricity, gas, or water) as proof of residence\n"
                  "  3️⃣  **Proof of income** — such as a salary slip, bank statement, or employment letter\n\n"
                  "Do you have these documents available, or would you like to discuss alternatives?"]),

                (r(r"\b(current|checking)\b"),
                 STATE_DOCUMENTS,
                 ["Great choice — a Current Account is perfect for your needs, {name}!\n\n"
                  "Here's what I'll need to process your application:\n"
                  "  1️⃣  A valid **National ID Card (CNIC)** or **Passport**\n"
                  "  2️⃣  A recent **utility bill** as proof of your residential address\n"
                  "  3️⃣  **Proof of income** — a salary slip or business registration, if applicable\n\n"
                  "Do you have these documents ready?"]),

                (r(r"\b(yes|yeah|sure|go\s*ahead|proceed|start|open)\b"),
                 STATE_DOCUMENTS,
                 ["Brilliant! Let's move forward then.\n\n"
                  "To process your application, I will need the following documents:\n"
                  "  1️⃣  A valid **National ID Card (CNIC)** or **Passport**\n"
                  "  2️⃣  A recent **utility bill** (electricity, gas, or water) as proof of address\n"
                  "  3️⃣  **Proof of income** — such as a salary slip or employment letter\n\n"
                  "Do you have all of these readily available, {name}?"]),
            ],

            # ── DOCUMENTS ────────────────────────────────────────────
            STATE_DOCUMENTS: [
                (r(r"\b(father|mother|parent|wife|husband|spouse|someone\s*else|other\s*name|not\s*my\s*name|family)\b"),
                 STATE_DOC_ISSUES,
                 ["No problem at all, {name}! That's quite common. In that case, you can provide any one of the following as an alternative:\n"
                  "  • A **tenancy agreement** or **rent receipt** in your name\n"
                  "  • A **letter of confirmation from your employer** showing your current address\n"
                  "  • An **affidavit** from a notary confirming your residence\n\n"
                  "Would any of these work for you?"]),

                (r(r"\b(don'?t\s*have|missing|lost|haven'?t|no\s*(id|passport|bill|proof)|expired)\b"),
                 STATE_DOC_ISSUES,
                 ["I completely understand, {name}. These things happen! Here are some alternatives we accept:\n"
                  "  • For **ID**: A valid driving licence or NADRA confirmation slip (if your CNIC is being renewed)\n"
                  "  • For **proof of address**: A bank statement from another bank, a tenancy agreement, "
                  "or a letter from your employer\n"
                  "  • For **proof of income**: Recent bank statements showing salary deposits\n\n"
                  "Let me know which alternatives you can arrange, and we'll make it work!"]),

                (r(r"\b(yes|have|ready|got|sure|here|brought)\b"),
                 STATE_FEES,
                 ["That's wonderful, {name}! You've come well prepared.\n"
                  "Before we proceed with the paperwork, would you like to know about our fee structure, "
                  "minimum balance requirements, or any charges associated with the account?"]),

                (r(r"\b(what|which|document|documents|paper|need|require)\b"),
                 STATE_DOCUMENTS,
                 ["Certainly! Here's exactly what you'll need:\n"
                  "  1️⃣  A valid **National ID Card (CNIC)** or **Passport**\n"
                  "  2️⃣  A recent **utility bill** as proof of address (within the last 3 months)\n"
                  "  3️⃣  **Proof of income** — salary slip, employment letter, or recent bank statements\n\n"
                  "Do you have these documents with you today?"]),
            ],

            # ── DOC ISSUES ───────────────────────────────────────────
            STATE_DOC_ISSUES: [
                (r(r"\b(yes|sure|can|will|okay|ok|works?|manage|arrange)\b"),
                 STATE_FEES,
                 ["Perfect, that will work just fine!\n"
                  "Now, would you like to know about the fees, minimum balance requirements, "
                  "and other charges for your account, {name}?"]),

                (r(r"\b(no|can'?t|cannot|unable|difficult|hard)\b"),
                 STATE_DOC_ISSUES,
                 ["I understand your concern, {name}. Let's see what else we can do.\n"
                  "In some cases, we can accept a sworn affidavit or a reference letter from an existing "
                  "account holder at {bank}. Do you happen to know anyone who banks with us?\n"
                  "Otherwise, I can connect you with our documentation assistance team for further guidance."]),
            ],

            # ── FEES ─────────────────────────────────────────────────
            STATE_FEES: [
                (r(r"\b(fee|fees|charge|charges|cost|maintenance|monthly)\b"),
                 STATE_FEES,
                 ["Great question! Here's a clear breakdown of our fee structure:\n\n"
                  "  💰 **Minimum Initial Deposit**: {min_deposit}\n"
                  "  💰 **Minimum Balance Requirement**: {min_balance}\n"
                  "  💰 **Monthly Maintenance Fee**: Absolutely FREE as long as you maintain the "
                  "minimum balance\n"
                  "  💰 **Service Charge**: A nominal fee of {service_charge}/month applies only if "
                  "your balance falls below {min_balance}\n\n"
                  "Would you also like to know about your debit card and chequebook delivery?"]),

                (r(r"\b(minimum|balance|deposit|initial)\b"),
                 STATE_FEES,
                 ["For our standard account, the minimum initial deposit is {min_deposit}. "
                  "To avoid any monthly service charges, we recommend maintaining a balance of at least {min_balance}.\n"
                  "If your balance dips below {min_balance}, a small service charge of {service_charge} per month will apply — "
                  "but that's quite manageable!\n\n"
                  "Any other questions about fees, or shall we move on to your debit card details?"]),

                (r(r"\b(interest|rate|earn|return|profit)\b"),
                 STATE_FEES,
                 ["Our Savings Account offers a competitive profit rate that is calculated on your daily balance "
                  "and credited to your account on a monthly basis. The current rate is quite attractive compared "
                  "to industry standards.\n\n"
                  "Would you like to know about your debit card and chequebook delivery timeline?"]),

                (r(r"\b(card|debit|atm|chequebook|cheque\s*book)\b"),
                 STATE_CARD_DELIVERY,
                 ["Absolutely! Here's what to expect:\n\n"
                  "  🏦 Your account will be **activated within 24–48 hours** of submitting your documents.\n"
                  "  💳 Your **debit card** will be mailed to your registered address within **5–7 business days**.\n"
                  "  📋 Your **chequebook** (if applicable) will arrive within **7–10 business days**.\n\n"
                  "You can start using online and mobile banking immediately once the account is activated!\n"
                  "Is there anything else I can help you with, {name}?"]),
            ],

            # ── CARD DELIVERY ────────────────────────────────────────
            STATE_CARD_DELIVERY: [
                (r(r"\b(card|debit|atm|when|deliver|receive|get|mail|time)\b"),
                 STATE_CARD_DELIVERY,
                 ["Here's the delivery timeline for you:\n\n"
                  "  🏦 **Account Activation**: Within 24–48 hours\n"
                  "  💳 **Debit Card Delivery**: 5–7 business days via registered mail\n"
                  "  📋 **Chequebook Delivery**: 7–10 business days\n\n"
                  "You'll also receive SMS and email notifications at each stage. "
                  "Is there anything else on your mind, {name}?"]),

                (r(r"\b(online|mobile|app|internet|digital)\b"),
                 STATE_ADDITIONAL,
                 ["Great news — once your account is activated (within 24–48 hours), you'll have full access to:\n"
                  "  📱 Our **mobile banking app** for on-the-go transactions\n"
                  "  💻 **Internet banking** for fund transfers, bill payments, and more\n"
                  "  📩 **SMS alerts** for every transaction on your account\n\n"
                  "We'll send you your login credentials via SMS and email. "
                  "Is there anything else I can assist you with?"]),
            ],

            # ── ADDITIONAL ───────────────────────────────────────────
            STATE_ADDITIONAL: [
                (r(r"\b(loan|credit|borrow)\b"),
                 STATE_ADDITIONAL,
                 ["We do offer a range of loan products including personal loans, home financing, and auto loans. "
                  "Once your account is established, you'd be eligible to apply.\n"
                  "I can schedule a meeting with our loans department if you'd like to explore that further!\n"
                  "Anything else, {name}?"]),

                (r(r"\b(joint|shared)\b"),
                 STATE_ADDITIONAL,
                 ["Absolutely! We do offer joint account options where two or more individuals can operate a single account. "
                  "Both parties would need to provide their identification and documentation.\n"
                  "Would you like more details on joint accounts, or is there anything else?"]),

                (r(r"\b(transfer|send\s*money|remittance)\b"),
                 STATE_ADDITIONAL,
                 ["Once your account is up and running, you'll be able to transfer funds domestically and internationally. "
                  "Our online banking platform makes it very convenient!\n"
                  "Is there anything else I can help with, {name}?"]),
            ],
        }


# ─── Main Chat Loop ─────────────────────────────────────────────────────────

def print_bot(message: str):
    """Pretty-print the bot's message with a prefix."""
    prefix = "🏦 Bank Manager: "
    indent = " " * len(prefix)
    lines = message.split("\n")
    for i, line in enumerate(lines):
        if i == 0:
            print(f"{prefix}{line}")
        else:
            print(f"{indent}{line}")
    print()


def main():
    print("=" * 70)
    print(f"   Welcome to the {BANK_NAME} Virtual Branch Manager")
    print("   Type 'quit' or 'bye' at any time to end the conversation.")
    print("=" * 70)
    print()

    bot = BankManagerBot()
    print_bot(bot.greet())

    while not bot.is_done:
        try:
            user_input = input("👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print_bot("It seems you need to go. Thank you for visiting us. Have a great day!")
            break

        if not user_input:
            continue

        response = bot.respond(user_input)
        print_bot(response)

    print("=" * 70)
    print("   Session ended. Thank you for banking with us!")
    print("=" * 70)


if __name__ == "__main__":
    main()
