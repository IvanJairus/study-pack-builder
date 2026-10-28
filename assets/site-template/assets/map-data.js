window.STUDY_MAP = {
  "title": "Study map",
  "subtitle": "Start with the outer layer, open the big ideas, then read the details only when you need them.",
  "layers": [
    {"id": "outer", "title": "Outer layer", "description": "See the categories, weights, sources, and magnitude."},
    {"id": "middle", "title": "Big ideas", "description": "Open the main points that define each category."},
    {"id": "inner", "title": "Details", "description": "Read the concepts, formulas, and exam traps."},
    {"id": "practice", "title": "Practice", "description": "Answer questions and explain the idea aloud."}
  ],
  "process": ["Identify", "Measure", "Monitor", "Respond"],
  "topics": [
    {
      "slug": "foundation",
      "kind": "foundation",
      "title": "Foundation",
      "page": "foundation.html",
      "scope": "Shared vocabulary, governance, and the four-step risk process.",
      "weight": 30,
      "source": "Slides 1-10",
      "quiz_topic": "Foundation",
      "prerequisites": [],
      "accent": "#2f5d4f",
      "magnitude": {"slides": 10, "concepts": 6, "formulas": 0, "minutes": 20},
      "big_ideas": [
        {
          "title": "Definition and the four pillars",
          "summary": "Risk is a potential event that hurts income or capital. The four pillars turn that definition into governance, policy, process, and internal control.",
          "weight": 50,
          "concepts": [
            {"title": "Risk definition", "gist": "A potential event, anticipated or not, with a negative effect on income or capital.", "source": "Slides 1-3"},
            {"title": "Four pillars", "gist": "Board oversight, policy and limits, risk process and information system, internal control.", "source": "Slides 4-6"},
            {"title": "Limits", "gist": "A limit converts risk appetite into a measurable boundary.", "source": "Slides 6-7", "trap": "A target without a limit is only a wish."}
          ]
        },
        {
          "title": "Risk profile and three lines",
          "summary": "The risk profile combines inherent risk and the quality of risk management. Three lines separate ownership, oversight, and audit.",
          "weight": 50,
          "concepts": [
            {"title": "Inherent risk vs KPMR", "gist": "Inherent risk is the exposure; KPMR is the quality of how it is managed.", "source": "Slides 7-8"},
            {"title": "Three Lines of Defense", "gist": "Business owns risk, risk and compliance oversee it, internal audit provides independent assurance.", "source": "Slides 8-9"},
            {"title": "Review cadence", "gist": "The risk profile is reviewed on a fixed cycle and after a material event.", "source": "Slides 9-10", "trap": "The audit line does not own the risk."}
          ]
        }
      ],
      "connections": [
        {"to": "reliability", "relation": "prerequisite", "mechanism": "The shared process and vocabulary are used by every later category."}
      ],
      "matrix": {
        "Identify": "Shared terms and scope",
        "Measure": "One metric per target",
        "Monitor": "Review cadence",
        "Respond": "Escalation path"
      }
    },
    {
      "slug": "reliability",
      "kind": "topic",
      "title": "Reliability",
      "page": "topic.html",
      "scope": "SLOs, error budgets, recovery targets, and incident response.",
      "weight": 70,
      "source": "Slides 11-20",
      "quiz_topic": "Reliability",
      "prerequisites": ["foundation"],
      "accent": "#34567f",
      "magnitude": {"slides": 10, "concepts": 9, "formulas": 2, "minutes": 35},
      "big_ideas": [
        {
          "title": "Targets and measurements",
          "summary": "An SLO is an internal target, an SLI is the measurement, and an SLA is a contract with a consequence.",
          "weight": 35,
          "concepts": [
            {"title": "SLO", "gist": "An internal reliability target over a defined window.", "source": "Slides 11-13"},
            {"title": "SLI", "gist": "The measurement that evaluates the target.", "source": "Slides 12-14"},
            {"title": "SLA", "gist": "A contractual commitment with a consequence.", "source": "Slides 13-15", "trap": "SLO and SLA are not synonyms."}
          ]
        },
        {
          "title": "Error budget",
          "summary": "The error budget is the allowed unreliability derived from the SLO. It is a decision tool, not a cost limit.",
          "weight": 35,
          "concepts": [
            {"title": "Error budget formula", "gist": "The complement of the SLO over the same window.", "formula": "(1 - SLO) x window", "source": "Slides 15-17"},
            {"title": "Burn rate", "gist": "How fast the budget is consumed against the target.", "source": "Slides 16-18"},
            {"title": "Response", "gist": "Pause change or invest when the budget is exhausted.", "source": "Slides 17-19", "trap": "An error budget is not a spending limit."}
          ]
        },
        {
          "title": "Recovery and incidents",
          "summary": "RTO, RPO, MTTR, and MTBF describe time and data loss, not the same thing.",
          "weight": 30,
          "concepts": [
            {"title": "RTO and RPO", "gist": "RTO is time to restore; RPO is acceptable data loss.", "source": "Slides 18-20"},
            {"title": "MTTR and MTBF", "gist": "MTTR is recovery speed; MTBF is time between failures.", "source": "Slides 19-20", "trap": "MTTR is not failure frequency."},
            {"title": "Incident review", "gist": "Review the timeline, the customer impact, and the recovery decision.", "source": "Slides 20"}
          ]
        }
      ],
      "connections": [
        {"to": "foundation", "relation": "depends on", "mechanism": "The shared process and vocabulary make the targets comparable."}
      ],
      "matrix": {
        "Identify": "User-visible behavior",
        "Measure": "SLI and error budget",
        "Monitor": "Burn rate and alerts",
        "Respond": "Pause releases or invest"
      }
    }
  ],
  "relationships": [
    {
      "from": "Foundation",
      "to": "Reliability",
      "mechanism": "Shared definitions make targets comparable and prevent SLO and SLA confusion."
    }
  ],
  "route": [
    {"title": "Foundation", "detail": "Read the vocabulary and process, then open the two big ideas.", "page": "foundation.html", "minutes": 20},
    {"title": "Reliability", "detail": "Read targets, error budget, and recovery, then open the concepts.", "page": "topic.html", "minutes": 35},
    {"title": "Practice", "detail": "Answer every question, read the feedback, then retry wrong answers.", "page": "bank-soal.html", "minutes": 25},
    {"title": "Interview", "detail": "Explain one decision aloud using the five-step answer structure.", "page": "interview.html", "minutes": 15}
  ]
};
