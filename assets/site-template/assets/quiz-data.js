window.QUIZ_DATA = [
  {
    "id": "Q01",
    "type": "single_choice",
    "topic": "Foundation",
    "topic_slug": "foundation",
    "slides": "Sample 1",
    "question": "What is a Service Level Objective (SLO)?",
    "options": {
      "A": "A measurable reliability target for a service",
      "B": "A legal contract with a customer",
      "C": "A monitoring dashboard",
      "D": "A deployment pipeline"
    },
    "order": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "An SLO is an internal target for a reliability metric, such as 99.9 percent availability over 30 days. An SLA is a contractual commitment, and a dashboard is only a tool to observe the metric.",
    "trap": "SLO is a target, SLA is a contract.",
    "sources": ["Sample 1"],
    "source_count": 1
  },
  {
    "id": "Q02",
    "type": "true_false",
    "topic": "Foundation",
    "topic_slug": "foundation",
    "slides": "Sample 2",
    "question": "An error budget is derived from the SLO.",
    "answer": true,
    "explanation": "The error budget is the allowed unreliability left after the SLO target. If the SLO is 99.9 percent, the error budget is 0.1 percent of the measured window.",
    "trap": "The error budget is a reliability allowance, not a cost limit.",
    "sources": ["Sample 2"],
    "source_count": 1
  },
  {
    "id": "Q03",
    "type": "multiple_choice",
    "topic": "Reliability",
    "topic_slug": "reliability",
    "slides": "Sample 3",
    "question": "Which measurements describe recovery?",
    "options": {
      "A": "Recovery Time Objective",
      "B": "Service Level Agreement",
      "C": "Recovery Point Objective",
      "D": "Mean Time To Recovery",
      "E": "Net Promoter Score"
    },
    "order": ["A", "B", "C", "D", "E"],
    "answer": ["A", "C", "D"],
    "explanation": "RTO and RPO define recovery targets and acceptable data loss. MTTR measures actual recovery speed. An SLA is a contract, and NPS is a customer score.",
    "trap": "Do not confuse RTO with MTTR.",
    "sources": ["Sample 3a", "Sample 3b"],
    "source_count": 2
  },
  {
    "id": "Q04",
    "type": "short_answer",
    "topic": "Reliability",
    "topic_slug": "reliability",
    "slides": "Sample 4",
    "question": "What does MTTR measure?",
    "accepted_answers": ["mean time to recovery", "mean time to recover", "MTTR"],
    "explanation": "MTTR is the average time needed to restore service after an incident. It measures recovery speed, not how often failures occur. MTBF measures the time between failures.",
    "trap": "MTTR is recovery time, not failure frequency.",
    "sources": ["Sample 4"],
    "source_count": 1
  },
  {
    "id": "Q05",
    "type": "single_choice",
    "topic": "Reliability",
    "topic_slug": "reliability",
    "slides": "Sample 5",
    "question": "Which pair correctly describes RTO and RPO?",
    "options": {
      "A": "RTO is recovery time, RPO is acceptable data loss",
      "B": "RTO is acceptable data loss, RPO is recovery time",
      "C": "Both measure network latency"
    },
    "order": ["A", "B", "C"],
    "answer": "A",
    "explanation": "Recovery Time Objective is how long recovery may take. Recovery Point Objective is how much data loss is acceptable, measured in time. A short RPO requires frequent backups or replication.",
    "trap": "RTO is time to restore, RPO is data loss tolerance.",
    "sources": ["Sample 5"],
    "source_count": 1
  }
];
