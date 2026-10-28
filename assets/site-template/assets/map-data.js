window.STUDY_MAP = {
  "title": "Study map",
  "subtitle": "Learn the shared vocabulary first, then apply it to one risk area. Practice after reading, and finish with spoken answers.",
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
    {
      "title": "Foundation",
      "detail": "Learn the vocabulary and the four-step process.",
      "page": "foundation.html",
      "minutes": 20
    },
    {
      "title": "Reliability",
      "detail": "Apply the process to SLOs, error budgets, and recovery.",
      "page": "topic.html",
      "minutes": 35
    },
    {
      "title": "Practice",
      "detail": "Answer every question, read the feedback, then retry wrong answers.",
      "page": "bank-soal.html",
      "minutes": 25
    },
    {
      "title": "Interview",
      "detail": "Explain one decision aloud using the five-step answer structure.",
      "page": "interview.html",
      "minutes": 15
    }
  ]
};
