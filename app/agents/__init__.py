"""The four agents, defined as capability manifests (no governance logic).

Each agent is a system prompt + the stable tool names it may use. Risk tier,
data-access policy and autonomy are declared in the Agent Lifecycle Hub portal,
not here.
"""
from __future__ import annotations

from ..core.agent import Agent, Suggestion

policy_qa = Agent(
    agent_id="policy-qa",
    name="Internal Policy Q&A Assistant",
    description="Answers staff questions from the internal policy knowledge base, with citations.",
    system_prompt=(
        "You are an internal policy assistant for an insurance company. Use the "
        "knowledge-base tools to find relevant articles, then answer the question "
        "accurately and cite the article IDs you used (e.g. KB-002). If the "
        "knowledge base does not contain the answer, say so plainly."
    ),
    tool_names=("search_knowledge_base", "get_kb_article"),
    suggestions=(
        Suggestion("Grace period", "What is the grace period for a missed payment?"),
        Suggestion("Flood coverage", "Is flood damage covered under a standard home policy?"),
        Suggestion("Bundling discount", "How big is the multi-policy discount and how do I get it?"),
    ),
)

email_assistant = Agent(
    agent_id="cs-email",
    name="Customer Service Email Assistant",
    description="Looks up a customer's policy and drafts (and can send) a reply to their inquiry.",
    system_prompt=(
        "You are a customer service email assistant for an insurance company. "
        "Look up the customer's policy record, then write a warm, accurate reply "
        "to their inquiry and save it as a draft. If the user explicitly asks you "
        "to send it, use the send tool. Address the customer by first name."
    ),
    tool_names=("fetch_customer_record", "save_email_draft", "send_email"),
    suggestions=(
        Suggestion(
            "Lapsed policy (draft)",
            "Draft a reply for the customer on policy POL-101533 who asks: 'Is my coverage still active? I think I missed a payment.'",
        ),
        Suggestion(
            "Bundling question (draft)",
            "Draft a reply for the customer on policy POL-100892 who asks whether they get a discount for having home and auto with us.",
        ),
        Suggestion(
            "Send it",
            "For policy POL-100245, write and SEND an email letting the customer know their renewal date is approaching.",
        ),
    ),
)

underwriting_advisor = Agent(
    agent_id="underwriting",
    name="Underwriting Risk Advisor",
    description="Assesses an applicant's risk against actuarial guidelines and records a recommendation.",
    system_prompt=(
        "You are an underwriting risk advisor for an auto insurer. Look up the "
        "actuarial guidelines and the applicant, assess the risk (0-100), then "
        "record a recommendation (approve / decline / refer) with a suggested "
        "premium adjustment and a clear rationale citing the factors you weighed."
    ),
    tool_names=("get_actuarial_guidelines", "lookup_applicant", "record_recommendation"),
    suggestions=(
        Suggestion("Low-risk applicant", "Assess applicant APP-1001 and record your recommendation."),
        Suggestion("High-risk applicant", "Assess applicant APP-1002 and record your recommendation."),
        Suggestion("Multiple accidents", "Assess applicant APP-1003 and record your recommendation."),
    ),
)

claims_adjudication = Agent(
    agent_id="claims",
    name="Claims Adjudication Agent",
    description="Fetches a claim and its policy, determines coverage, and records a decision.",
    system_prompt=(
        "You are a claims adjudication assistant for an insurer. Fetch the claim "
        "and its policy, determine whether the loss is covered and the policy was "
        "in force, compute the payable amount (claimed minus deductible, never "
        "below zero), then record your decision (approve or deny) with reasoning."
    ),
    tool_names=("fetch_claim", "fetch_policy", "record_claim_decision"),
    suggestions=(
        Suggestion("Small clean claim", "Adjudicate claim CLM-55012."),
        Suggestion("Large water-damage claim", "Adjudicate claim CLM-55088."),
        Suggestion("Lapsed policy claim", "Adjudicate claim CLM-55130."),
        Suggestion("High-value suspicious claim", "Adjudicate claim CLM-55177."),
    ),
)

fraud_detection = Agent(
    agent_id="fraud-detection",
    name="Fraud Detection Agent",
    description="Investigates a claim for fraud, checks external watchlists, and flags suspicious claims for SIU review.",
    system_prompt=(
        "You are a fraud detection analyst for an insurer. Fetch the claim and "
        "its policy, look up the claimant against the external fraud watchlist, "
        "then weigh the fraud indicators (statement inconsistencies, lapsed "
        "coverage at the time of loss, late reporting, unusually high value, "
        "watchlist matches). If the claim warrants it, flag it for SIU "
        "investigation with a risk level and a clear reason. Explain your "
        "assessment either way."
    ),
    tool_names=(
        "fetch_claim",
        "fetch_policy",
        "check_fraud_watchlist",
        "flag_claim_for_investigation",
    ),
    suggestions=(
        Suggestion("Suspicious high-value", "Investigate claim CLM-55177 for fraud."),
        Suggestion("Lapsed + watchlist", "Investigate claim CLM-55130 for fraud."),
        Suggestion("Clean claim", "Investigate claim CLM-55012 for fraud."),
    ),
)

AGENTS: dict[str, Agent] = {
    a.agent_id: a
    for a in (
        policy_qa,
        email_assistant,
        underwriting_advisor,
        claims_adjudication,
        fraud_detection,
    )
}
