# Corporate Agent Use Cases

## Use Cases

| Use case | Minimum shape | Data | Eval |
|----------|---------------|------|------|
| Invoice matching | Deterministic + extraction | invoices, POs, receipts | field accuracy, duplicate detection |
| Reconciliation assistant | Workflow + bounded tool-use | ledger, bank statements | match accuracy, exception recall |
| Spend policy Q&A | RAG + deterministic rules | policy docs, approvals | citation precision, no-answer accuracy |
| Payment draft assistant | Bounded tool-use | vendor master, invoice, payment policy | wrong-payment rate, approval edits |
| Treasury report summarizer | Workflow | balances, reports | factuality, source citation |
| Compliance checklist assistant | RAG/extraction | KYC/AML docs | missing-document recall, false-pass rate |

## Boundary

These are hypotheses for discovery. Do not claim production fit until data
readiness, eval readiness, permissions, and compliance review are complete.

