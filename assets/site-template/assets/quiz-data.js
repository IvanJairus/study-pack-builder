window.QUIZ_DATA = [
  {
    "id": "Q01",
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
    "topic": "Foundation",
    "topic_slug": "foundation",
    "slides": "Sample 2",
    "question": "What is the main difference between an SLO and an SLA?",
    "options": {
      "A": "An SLO is internal, an SLA is a contractual commitment",
      "B": "An SLO is contractual, an SLA is internal",
      "C": "Both are identical",
      "D": "An SLA only applies to databases"
    },
    "order": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "SLOs guide engineering decisions inside the team. SLAs define what happens with customers when a commitment is missed, including credits or penalties.",
    "trap": "Do not use SLO and SLA as synonyms.",
    "sources": ["Sample 2"],
    "source_count": 1
  },
  {
    "id": "Q03",
    "topic": "Reliability",
    "topic_slug": "reliability",
    "slides": "Sample 3",
    "question": "What is an error budget?",
    "options": {
      "A": "The allowed amount of unreliability derived from the SLO",
      "B": "A billing limit for cloud spend",
      "C": "A quota for on-call staff",
      "D": "A backup retention period"
    },
    "order": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "An error budget is the complement of the SLO. If the SLO is 99.9 percent, the error budget is 0.1 percent of the measured window. It helps teams balance reliability work with feature delivery.",
    "trap": "Error budget is a reliability allowance, not a cost limit.",
    "sources": ["Sample 3"],
    "source_count": 2
  },
  {
    "id": "Q04",
    "topic": "Reliability",
    "topic_slug": "reliability",
    "slides": "Sample 4",
    "question": "What does MTTR measure?",
    "options": {
      "A": "Mean time to recover from a failure",
      "B": "Mean time between planned releases",
      "C": "Maximum throughput per request",
      "D": "Minimum time to reproduce a bug"
    },
    "order": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "MTTR is the average time needed to restore service after an incident. It measures recovery speed, not how often failures occur. MTBF measures the time between failures.",
    "trap": "MTTR is recovery time, not failure frequency.",
    "sources": ["Sample 4"],
    "source_count": 2
  },
  {
    "id": "Q05",
    "topic": "Reliability",
    "topic_slug": "reliability",
    "slides": "Sample 5",
    "question": "Which pair correctly describes RTO and RPO?",
    "options": {
      "A": "RTO is recovery time, RPO is acceptable data loss",
      "B": "RTO is acceptable data loss, RPO is recovery time",
      "C": "Both measure network latency",
      "D": "Both measure deployment frequency"
    },
    "order": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "Recovery Time Objective is how long recovery may take. Recovery Point Objective is how much data loss is acceptable, measured in time. A short RPO requires frequent backups or replication.",
    "trap": "RTO is time to restore, RPO is data loss tolerance.",
    "sources": ["Sample 5"],
    "source_count": 1
  }
];
