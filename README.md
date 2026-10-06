# Intelligent FAQ Chatbot Using Python and NLP

A college/department information chatbot, built progressively in stages.

## Folder structure

```
college-faq-chatbot/
├── README.md
├── requirements.txt
├── .gitignore
├── stage1_rule_based/
│   └── chatbot_v1.py        # if/elif rules, whole-word matching
└── stage2_knowledge_base/
    └── chatbot_v2.py        # FAQ knowledge base + keyword scoring
```

## How to run

```bash
cd stage1_rule_based
python chatbot_v1.py

cd ../stage2_knowledge_base
python chatbot_v2.py
```

Stage 2 writes questions it could not answer to `unanswered_questions.txt`
(created in the folder you run it from). Use it to improve the knowledge base.

## Stages

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | Rule-based chatbot | Done |
| 2 | Knowledge base with keyword scoring | Done |
| 3 | NLP preprocessing + TF-IDF similarity | Planned |
| 4-8 | Web app and further improvements | Planned |
