const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  Numbering, LevelFormat, PageBreak, Header, Footer, PageNumber
} = require("docx");

const NAVY = "1F3864";
const GREY = "595959";
const LIGHT = "EDEDED";

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [new TextRun({ text, color: NAVY })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun({ text, color: NAVY })] });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, size: 21, ...opts })],
  });
}
function bullet(text) {
  return new Paragraph({
    spacing: { after: 90, line: 260 },
    bullet: { level: 0 },
    children: [new TextRun({ text, size: 21 })],
  });
}
function caption(text) {
  return new Paragraph({
    spacing: { before: 60, after: 200 },
    children: [new TextRun({ text, size: 18, italics: true, color: GREY })],
  });
}

function cell(text, opts = {}) {
  const { bold = false, shade = null, width = null, align = AlignmentType.LEFT, white = false } = opts;
  return new TableCell({
    width: width ? { size: width, type: WidthType.DXA } : undefined,
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, size: 19, bold, color: white ? "FFFFFF" : "000000" })],
    })],
  });
}

function table(headerRow, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headerRow.map((t, i) => cell(t, { bold: true, shade: NAVY, white: true, width: colWidths[i] })),
      }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((t, i) => cell(t, { width: colWidths[i], shade: ri % 2 === 1 ? LIGHT : null, white: false })),
      })),
    ],
  });
}

const sections_children = [];

// ---------- TITLE PAGE ----------
sections_children.push(
  new Paragraph({ spacing: { before: 2400 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "ClearSight", bold: true, size: 64, color: NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100 },
    children: [new TextRun({ text: "Citation-Grounded, Hallucination-Reduced Threat Detection", size: 28, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 800 },
    children: [new TextRun({ text: "Business Plan", size: 24, italics: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "Prepared by Gangadhar Singh Shiva and Poonam Singh Umakanth", size: 21 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "August 2026", size: 21, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1600 },
    children: [new TextRun({ text: "Confidential — for discussion purposes only", size: 18, italics: true, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ---------- EXECUTIVE SUMMARY ----------
sections_children.push(
  h1("1. Executive Summary"),
  p("ClearSight builds threat-detection systems in which every AI-generated finding is grounded and independently verified against an authoritative external source before it ever reaches a human analyst. The starting product classifies IoT/OT network traffic using a multimodal large language model and requires every classification to carry a citation to a specific CAPEC attack pattern or CVE vulnerability record, checked against the official MITRE and NVD databases in real time."),
  p("The company's technical differentiator is a three-layer grounding architecture rather than a single trick: (1) retrieval grounding, where relevant verified reference entries are placed in the model's context before it answers; (2) tool-based verification, where the model can call a live lookup or verification function during its own reasoning to check a citation before committing to it; and (3) downstream citation enforcement, an independent, deterministic check against the authoritative source that gates every alert as a final backstop. Layers 1 and 3 are built and have been measured in ClearSight's own R&D; layer 2 is a near-term roadmap item, motivated by external research showing tool-based grounding is one of the two strongest architectural levers for reducing LLM hallucination (industry analyses report roughly 65–80% hallucination reduction from tool/function-call grounding and 75–90% from retrieval grounding, both well ahead of prompt-only techniques, which cap out around 15%)."),
  p("Measured results to date: 96.7–100% classification accuracy across all 34 attack types in the CIC-IoT-2023 benchmark; a wrong-citation rate of 25–50% when the model operates without a verified reference corpus, reduced toward near-zero when grounding and verification are applied; and an approximately 40% rate at which the model correctly declines to answer when the evidence does not support a citation. A companion study, released alongside this plan, shows that the obvious efficiency upgrade — replacing full-corpus grounding with retrieval — is not free: three independent retrieval methods all showed real, measured recall degradation under corpus growth, which is the direct motivation for adding an active tool-verification layer rather than relying on retrieval alone as the corpus scales."),
  p("The target market is IoT/OT security software, sized at approximately $27.4B in 2026 and projected to reach $58.9B by 2031 (16.6% CAGR). AI-native security specifically is attracting strong early-stage investor interest, with AI-focused security startups raising roughly $855M across more than 150 seed-stage rounds in 2026 to date. None of the category-leading vendors — Claroty, Armis, Nozomi Networks, or Dragos — currently publish a measured accuracy or hallucination rate for their own AI features, which is the specific, evidenced gap ClearSight is positioned to fill."),
  p("This plan lays out the product and technology, market and competitive position, go-to-market strategy, an illustrative financial model, and a seed funding ask sized against comparable 2026 rounds in AI-security. Financial projections in this document are planning assumptions, not verified forecasts or guarantees, and should be reviewed with a financial or legal advisor before being used in an actual fundraising process."),
);

// ---------- PROBLEM ----------
sections_children.push(
  h1("2. The Problem"),
  h2("2.1 Legacy detection tools miss the attacks that matter most"),
  p("IoT and OT devices — cameras, sensors, industrial controllers, routers, switches, access points — are proliferating faster than organizations can monitor them. Existing detection tools work by counting things (packets per second, byte counts, protocol flags) and require hand-tuning for every attack type. Tested against a real dataset (CIC-IoT-2023), these tools catch 97.5% of loud, obvious “flood” attacks but only 2.5–17.5% of quiet attacks — login-page probing, password guessing, address spoofing — which is exactly the category a defender is most likely to miss."),
  h2("2.2 AI closes the detection gap and opens a trust gap"),
  p("Multimodal AI that reads a rendered picture of traffic and explains what it sees closes that detection gap but introduces a new one: a May 2026 ISC2 survey of 856 security professionals found widespread concern about AI fabrication and a clear demand for verifiable AI decisions, and a 2026 SANS survey found 78% of security teams now use generative AI daily while 63% report it still falls short in real detection and response work. No vendor in this space currently publishes a measured rate for how often their AI's explanations are actually correct."),
  h2("2.3 The dangerous failure mode is subtle, not obvious"),
  p("Testing shows the underlying model rarely invents a fake CAPEC or CVE identifier outright. The more dangerous and more common failure is attaching a real, correctly-formatted identifier to the wrong explanation — a mistake that happened in 25–50% of responses when the model operated without a checked reference list, and one a busy analyst is likely to miss precisely because it looks correct at a glance."),
);

// ---------- SOLUTION ----------
sections_children.push(
  h1("3. The Solution: A Layered Grounding Architecture"),
  p("ClearSight's core product decision is architectural, not a prompting trick. External research on LLM hallucination mitigation across 2026 production systems consistently ranks architectural interventions far above prompt engineering: prompt-only techniques (better instructions, few-shot examples, asking the model to be careful) cap out around a 15% reduction in hallucination, because the model is still generating primarily from its own internal knowledge. Retrieval grounding — placing verified, relevant content directly in context before generation — is reported to reduce hallucination by roughly 75–90%. Tool or function-call grounding, where the model actively queries a live source during its own reasoning, is reported at roughly 65–80%. ClearSight's architecture combines both, plus a deterministic backstop that does not depend on the model behaving correctly at all."),
  h2("3.1 Layer 1 — Retrieval grounding (built, measured)"),
  p("Before classification, the system places relevant entries from a hand-verified CAPEC/CVE reference corpus into the model's context. In ClearSight's current production design this is done by including the full corpus on every call; a companion R&D study benchmarked replacing this with retrieval-augmented generation (RAG) across three independent retrieval methods (TF-IDF, BM25, and LSA) and found that while RAG cuts prompt cost by roughly two orders of magnitude at scale, retrieval recall degrades under corpus growth in a way that is consistent across all three methods and does not fully recover even with a larger retrieval budget. That finding directly motivates Layer 2 below: retrieval alone is not sufficient once the corpus is large."),
  h2("3.2 Layer 2 — Tool-based verification (near-term roadmap)"),
  p("Rather than relying solely on whatever was retrieved into context ahead of time, the model is given a callable verification tool it can invoke mid-reasoning — for example, a direct lookup against the live CAPEC or NVD record for a candidate identifier — before it commits to a final citation. This lets the system catch a wrong or unsupported citation at generation time rather than only after the fact, and it allows the effective search space to be much larger than what fits in a single context window. This layer is not yet built or measured in ClearSight's own testing; it is proposed on the strength of external research showing tool-grounding is one of the two strongest known architectural levers, and it will need the same empirical discipline ClearSight has applied elsewhere — specifically, measuring how often the model actually invokes the tool when it should, and how often it correctly defers to what the tool returns, since both are documented failure modes in agentic systems generally."),
  h2("3.3 Layer 3 — Downstream citation enforcement (built, measured)"),
  p("Every classification and citation is checked, independently of the model, against the authoritative source before an alert is ever surfaced to an analyst. This is the backstop that does not depend on Layers 1 or 2 working perfectly: even if a wrong citation makes it through generation, it is caught here. This is the mechanism already implemented in ClearSight's on-premises Agent Node, which holds the verified reference corpus locally, checks every returned citation against it, and only forwards a verified alert to the analyst or SOC — with no additional network round-trip required for the check itself."),
  h2("3.4 Why layered, not either/or"),
  p("The honest position, consistent with how ClearSight has evaluated every design choice to date, is that no single layer is sufficient on its own. Prompting alone is weak. Retrieval alone degrades as the corpus grows, a finding ClearSight has itself measured rather than assumed. Tool-based verification introduces its own new failure modes that have not yet been measured for this system. Downstream enforcement catches errors after the fact but cannot improve the model's first-pass accuracy. Combining all three is the only configuration that has both a strong first-pass grounding mechanism and a deterministic backstop that fails safe."),
);

// ---------- PRODUCT & TECH ----------
sections_children.push(
  h1("4. Product and Technology"),
  h2("4.1 Architecture"),
  p("An on-premises Agent Node sits next to the monitored devices, renders their traffic as an image, and holds the verified reference corpus locally. It sends the image plus a grounded prompt to a multimodal model over the internet; the model returns a classification and a citation. The Agent Node checks that citation against its own local corpus — and, once Layer 2 is added, the model can additionally verify mid-reasoning — before forwarding a verified alert to the analyst or SOC."),
  h2("4.2 Why an off-the-shelf multimodal model, not a custom-trained classifier"),
  p("A custom-trained image classifier needs a large pool of labeled examples per attack type before it can recognize even one of them, needs dedicated GPU infrastructure before there is any proof the approach works, and needs retraining every time a new attack or device type appears. The off-the-shelf multimodal approach tested by ClearSight required none of that: it correctly classified every attack type tried, including the quiet ones legacy tools miss, with zero training and no hardware investment before validating the idea."),
  h2("4.3 Why images, not raw data"),
  p("Rendering traffic (and, in planned extensions, other structured security data) as an image keeps the input a small, fixed size regardless of data volume, makes patterns visible to both a human reviewer and a vision-capable model, avoids building a custom parser for every protocol or data format, and reduces the sensitive payload data that needs to be shared with an external API."),
  h2("4.4 Measurement discipline as a competitive moat"),
  p("ClearSight measures and publishes the specific numbers that determine whether an AI security tool can be trusted: invented-citation rate, wrong-explanation rate, appropriate-abstention rate, and — for the retrieval layer specifically — recall@k with confidence intervals across multiple retrieval methods. No competitor identified in Section 6 currently publishes equivalent numbers for their own AI features. This measurement discipline, not any single algorithm, is the durable differentiator: it is difficult for a competitor to credibly claim parity without adopting the same evaluation rigor."),
);

// ---------- MARKET ----------
sections_children.push(
  h1("5. Market Opportunity"),
  p("The core addressable market is IoT/OT security software. MarketsandMarkets sizes the operational technology (OT) security market at approximately $27.4B in 2026, growing to approximately $58.9B by 2031, a 16.6% compound annual growth rate. A separate estimate places IoT security software spending at $28.7B–$58.3B depending on methodology, growing 18–32% annually — consistent directionally with the OT-specific figure. Investor appetite for AI-native security specifically is strong and growing: AI-focused security startups raised roughly $855M across more than 150 seed-stage rounds in 2026 to date, and AI-focused security investment overall reached $4.1B in Q1 2026 alone, up 47% year-over-year."),
  table(
    ["Segment", "Definition", "Illustrative sizing"],
    [
      ["TAM", "Global IoT/OT security software market", "$27.4B (2026) → $58.9B (2031), 16.6% CAGR"],
      ["SAM", "AI-driven detection and verification tooling within IoT/OT security", "Planning estimate: low-single-digit-billion-dollar slice of TAM, growing faster than the category as AI adoption increases — not independently sized by a third party and should be treated as an assumption, not a benchmarked figure"],
      ["SOM", "Initial beachhead: mid-market industrial and critical-infrastructure operators seeking verifiable AI alerting", "Sized by design-partner pipeline during Phase 1 (Section 7), not yet quantified"],
    ],
    [1600, 4600, 3800]
  ),
  caption("Table 1. Market sizing. TAM figures are drawn from published third-party market research (see Section 10, Sources); SAM and SOM are ClearSight planning estimates, not independently benchmarked."),
);

// ---------- COMPETITION ----------
sections_children.push(
  h1("6. Competitive Landscape"),
  p("Gartner's 2025 Magic Quadrant for CPS (cyber-physical systems) Protection Platforms names Claroty, Armis, Nozomi Networks, Dragos, and Microsoft as Leaders. All are established, well-funded incumbents with broad device-visibility and detection capabilities."),
  table(
    ["Vendor", "Position", "Publishes a measured AI accuracy / hallucination rate?"],
    [
      ["Claroty", "Gartner CPS Leader", "Not identified in public materials reviewed"],
      ["Armis", "Gartner CPS Leader", "Not identified in public materials reviewed"],
      ["Nozomi Networks", "Gartner CPS Leader", "Not identified in public materials reviewed"],
      ["Dragos", "Gartner CPS Leader", "Not identified in public materials reviewed"],
      ["Microsoft", "Gartner CPS Leader (broader platform)", "Not identified in public materials reviewed"],
      ["ThreatCompute (academic)", "Research prototype grounding LLM threat modeling in the Microsoft Threat Matrix for Kubernetes", "Publishes attack-graph fidelity (29/30 known techniques identified in one test), not a citation-hallucination rate; not a commercial product"],
    ],
    [2400, 3600, 4000]
  ),
  caption("Table 2. Competitive landscape. “Not identified” reflects a review of public materials as of this writing, not a claim of certainty about undisclosed internal metrics."),
  p("ClearSight's position is not to out-detect these vendors on raw classification accuracy alone — a claim that is hard to verify externally and that incumbents can contest — but to compete on independently measurable trust: a published, reproducible methodology for how often the system's AI-generated explanations are actually correct, and an architecture designed so that an incorrect explanation is caught before it reaches a human, not after."),
);

// ---------- ROADMAP ----------
sections_children.push(
  h1("7. Product Roadmap"),
  table(
    ["Phase", "Timeframe", "Scope"],
    [
      ["Phase 1 — IoT/OT core", "0–12 months", "Harden the current traffic-classification and citation-verification pipeline; scale the verified CAPEC/CVE corpus; complete and validate the RAG-vs-full-corpus retrieval study already underway; publish methodology (two papers already drafted); onboard initial design partners for pilots."],
      ["Phase 2 — Kubernetes / container extension", "12–24 months", "Apply the same architecture to container and cluster security: render Kubernetes scan output (kube-bench / Trivy findings against the CIS Kubernetes Benchmark, and CVE-linked vulnerability findings) as an image for multimodal classification, with citations verified against NVD and the CIS Benchmark. Validate against a deliberately vulnerable cluster (e.g., kubernetes-goat) plus a live cluster, using the same measured-hallucination methodology as Phase 1."],
      ["Phase 3 — Physical / video security extension", "24–36 months", "Extend to video-based threat detection with dual grounding: spatiotemporal evidence verification (does the cited video segment actually show the claimed event) plus external-taxonomy verification (does the claimed incident type map to a citable entry in an authoritative external standard). Requires selecting a defensible grounding taxonomy for physical security before committing engineering resources — flagged as an open design question, not yet resolved."],
      ["Ongoing — Layer 2 rollout", "Begins Phase 1, continues throughout", "Introduce tool-based mid-reasoning verification (Section 3.2) as the reference corpus grows past the point where full-corpus or simple retrieval grounding remains sufficient, informed by the recall measurements from the RAG study."],
    ],
    [2200, 1600, 6200]
  ),
);

// ---------- BUSINESS MODEL ----------
sections_children.push(
  h1("8. Business Model and Pricing"),
  p("ClearSight is designed as a subscription (SaaS) business, priced primarily by the number of monitored devices, nodes, or clusters under management, sold directly to enterprise security and OT teams and through managed security service provider (MSSP) and systems-integrator channel partners for mid-market reach. None of the named competitors in Section 6 publish list pricing, which is typical for enterprise security software sold through direct sales motions with custom contracts; as a result, the pricing tiers below are illustrative planning assumptions for internal use, not benchmarked against a disclosed competitor price."),
  table(
    ["Tier", "Target customer", "Illustrative pricing basis"],
    [
      ["Starter", "Single-site industrial operator, pilot deployments", "Per-device/month, capped device count"],
      ["Enterprise", "Multi-site critical infrastructure operators", "Per-device/month at volume discount, annual contract"],
      ["Platform / MSSP", "Managed security service providers reselling to their own customer base", "Per-tenant platform fee plus per-device usage"],
    ],
    [2000, 4200, 3800]
  ),
  caption("Table 3. Illustrative pricing tiers. Actual pricing should be validated against design-partner willingness to pay during Phase 1 pilots, not set from this table alone."),
);

// ---------- GTM ----------
sections_children.push(
  h1("9. Go-to-Market Strategy"),
  bullet("Land with a small number of design partners in critical infrastructure or industrial IoT operators who are already piloting AI-based security tools and have expressed a specific need for verifiable, auditable AI outputs (the ISC2/SANS survey findings in Section 2.2 describe exactly this buyer)."),
  bullet("Use the published measurement methodology itself as a sales asset: a prospective customer can be shown the actual invented-citation and wrong-explanation rates, with and without grounding, rather than being asked to take an accuracy claim on faith."),
  bullet("Build channel relationships with MSSPs and systems integrators serving mid-market industrial and OT customers who cannot support a large in-house security engineering team."),
  bullet("Expand within each account from the initial monitored-device footprint to full-site and then multi-site coverage (land-and-expand), and cross-sell the Kubernetes and physical-security extensions (Phases 2–3) into the same accounts once available."),
  bullet("Publish and present the underlying research (the two papers already produced) at security and applied-AI venues to build credibility with a technically sophisticated buyer before a large direct sales team is in place."),
);

// ---------- TEAM ----------
sections_children.push(
  h1("10. Team"),
  p("ClearSight is founded by Gangadhar Singh Shiva and Poonam Singh Umakanth, who developed the citation-grounding architecture, ran the underlying R&D (classification accuracy, hallucination-rate, and retrieval-recall studies referenced throughout this plan), and authored the accompanying technical papers. This section is intentionally brief; a fundraising-ready version of this plan should expand it with each founder's relevant background, prior track record, and any advisors or early hires, none of which is asserted here beyond what has already been demonstrated in the R&D work itself."),
);

// ---------- FINANCIALS ----------
sections_children.push(
  h1("11. Illustrative Financial Model"),
  p("The figures below are a simple, illustrative planning model to frame the funding ask in Section 12 — they are assumptions for discussion, not a verified forecast, and are not financial or investment advice. Actual projections should be built with a financial advisor or accountant once pilot pricing and conversion data exist from Phase 1 design partners."),
  table(
    ["", "Year 1", "Year 2", "Year 3"],
    [
      ["Design partners / pilot customers (illustrative)", "3–5", "10–15", "25–40"],
      ["Paying enterprise customers (illustrative)", "0–2", "5–10", "20–35"],
      ["Primary spend", "R&D (Layer 2 build), corpus curation, Phase 1 pilots", "GTM build-out, Phase 2 (Kubernetes) engineering", "Channel scale, Phase 3 (video) R&D"],
    ],
    [3200, 2400, 2400, 2400]
  ),
  caption("Table 4. Illustrative 3-year planning model. Not a revenue forecast; no pricing has been validated with a paying customer as of this writing."),
);

// ---------- FUNDING ASK ----------
sections_children.push(
  h1("12. Funding Ask and Use of Funds"),
  p("2026 seed-stage funding for AI-focused cybersecurity startups has been active: AI-security startups raised roughly $855M across more than 150 seed rounds in 2026 to date, with individual seed rounds in this space commonly landing in the $5M–$20M range (recent examples include an $8M seed for an agentic security platform, a $13M seed for an AI-powered agentic cybersecurity platform, and a $17M seed round elsewhere in the category)."),
  p("Against that benchmark, an illustrative seed target for ClearSight is in the $5M–$8M range — toward the lower-middle of the observed range, appropriate for a team with working R&D and two published technical studies but not yet a paying customer base. This should be treated as a starting point for discussion with investors and advisors, not a final number; the right ask depends on runway assumptions, hiring plan, and investor feedback that this plan does not attempt to substitute for."),
  h2("Illustrative use of funds"),
  bullet("Engineering (40–50%): build and measure the Layer 2 tool-based verification architecture; scale the verified reference corpus; harden the Agent Node for production deployment."),
  bullet("Go-to-market (20–30%): design-partner pilots, early hires in sales/customer success, channel partner development."),
  bullet("R&D / research credibility (10–15%): continued measurement studies (the two papers already produced are a template, not a one-time exercise), conference presentation and publication."),
  bullet("Operations and reserve (10–15%): standard operating costs and runway buffer."),
);

// ---------- MILESTONES ----------
sections_children.push(
  h1("13. Milestones and Success Metrics"),
  h2("Near term (0–12 months)"),
  bullet("Repeat classification and citation-accuracy testing at larger scale and confirm results hold; test across more than one underlying AI model to confirm findings are not specific to a single model."),
  bullet("Working prototype of the full verification pipeline, including the Layer 2 tool-based check."),
  bullet("Peer-reviewed or arXiv publication of the method (already in progress with two papers produced during this engagement)."),
  h2("Medium term (12–24 months)"),
  bullet("At least one design partner or channel partner integrates ClearSight's verified alerting into their existing security workflow."),
  bullet("Real-world pilot deployments hold the invented-citation rate at zero and the appropriate-abstention rate close to the ~40% measured in testing, demonstrating the lab results transfer to production traffic."),
  h2("Long term"),
  bullet("Analysts using the system spend measurably less time double-checking AI explanations, and fewer decisions are made on a wrongly-matched citation."),
  bullet("Independent, published citation verification becomes an expected, standard layer in AI-driven security tools — something other vendors build on top of, not something ClearSight has to keep explaining as unusual."),
);

// ---------- RISKS ----------
sections_children.push(
  h1("14. Risks and Mitigations"),
  table(
    ["Risk", "Mitigation"],
    [
      ["Retrieval recall degrades as the reference corpus grows (measured directly in ClearSight's own RAG study, not hypothetical).", "Layer 3 downstream enforcement catches citations that were never retrieved correctly; Layer 2 tool-based verification is being built specifically to address this; corpus growth and retrieval quality are re-measured on an ongoing basis rather than assumed."],
      ["Tool-based verification (Layer 2) introduces new failure modes — hallucinated tool arguments, skipped tool calls, or ignored tool results — that have not yet been measured for this system.", "Apply the same empirical measurement discipline used elsewhere in this plan before relying on Layer 2 in production; keep Layer 3 as a backstop that does not depend on Layer 2 behaving correctly."],
      ["Incumbent vendors (Claroty, Armis, Nozomi, Dragos, Microsoft) have far greater resources, existing customer relationships, and could add similar verification claims.", "Compete on published, reproducible measurement rather than a claim that is easy for an incumbent to imitate rhetorically without matching the underlying rigor; use the published papers as ongoing proof rather than a one-time claim."],
      ["No committed paying customers or validated pricing as of this writing.", "Phase 1 design-partner pilots (Section 9) are structured specifically to validate willingness to pay before the financial model in Section 11 is finalized."],
      ["Physical-security extension (Phase 3) lacks an obvious, defensible external grounding taxonomy (unlike CAPEC/CVE for network security).", "Explicitly sequenced after Phases 1–2; not started until a defensible taxonomy choice is made, rather than building the extension first and rationalizing the grounding source afterward."],
    ],
    [4200, 5600]
  ),
);

// ---------- SOURCES ----------
sections_children.push(
  h1("15. Sources and Methodology Note"),
  p("This plan draws on two categories of information. First, ClearSight's own measured R&D results: classification accuracy and citation-hallucination rates from internal testing on the CIC-IoT-2023 dataset, and the retrieval-recall findings from the companion RAG-vs-full-corpus study released alongside this plan. Second, third-party published sources for market sizing, survey data, and funding benchmarks, listed below. Financial projections in Section 11 and the funding figure in Section 12 are illustrative planning assumptions built from these sources, not independently audited forecasts, and should be reviewed with a qualified financial or legal advisor before use in an actual fundraising process."),
  bullet("MarketsandMarkets, “Operational Technology (OT) Security Market Report 2026–2031.”"),
  bullet("MarketsandMarkets, “IoT Security Market Report 2025–2031”; Fortune Business Insights, IoT Security Market (alternative sizing)."),
  bullet("ISC2 Research, “Rethinking AI's Impact on Cybersecurity Roles,” May 2026 (n=856 security professionals)."),
  bullet("SANS Institute, 2026 AI Survey (78% active GenAI use; 63% report AI-driven detection/response shortcomings)."),
  bullet("Gartner Magic Quadrant for CPS Protection Platforms, 2025 (Claroty, Armis, Nozomi Networks, Dragos, Microsoft named Leaders)."),
  bullet("“AI Cybersecurity Funding Boom 2026” ($4.1B Q1 2026 AI-security investment, 47% YoY growth); AI Weekly, “AI-Security Startups Pull $855M Across 150+ Seed Rounds in 2026.”"),
  bullet("Neto et al. (2023), “CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT Environment,” Sensors 23(13), 5941."),
  bullet("ClearSight internal R&D: “ClearSight Multimodal Network Security” problem-framing report; “Full-Corpus Context-Stuffing versus Retrieval-Augmented Generation for Citation-Grounded IoT/OT Threat Verification” (companion paper, this engagement)."),
  bullet("ThreatCompute: Leveraging LLMs for Automated Threat Modeling of Cloud-Native Applications, Proceedings of the 2025 Cloud Computing Security Workshop; kube-bench and Trivy project documentation; kubernetes-goat project (Madhu Akula)."),
);

const doc = new Document({
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
        },
      },
      children: sections_children,
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("ClearSight_Business_Plan_v2.docx", buffer);
  console.log("done");
});
