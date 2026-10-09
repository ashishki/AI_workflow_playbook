# Final prototype review — preserved negative findings

CHANGES REQUESTED for three confirmed P2 issues. Native/Desktop runtime7f36b90 is unaffected.

1. A one-shot injected directory-fsync failure after actual JSON replacement leaves Store memory stale. A different next successful booking erases the first already written booking. Both initial/transfer sources reproduce this on reviewer-owned data.
2. Successful retire with export path equal to `<data>.retired` overwrites the new JSON export with marker text. Both sources reproduce exit0 with unreadable export.
3. Published initial/transfer snapshots omit their required .agents directory. Exact preservation checks on temporary copies fail (initial31 missing-file errors; transfer1 file-set failure). Historical original checks are not rewritten or invalidated.

See prototype-negative.json for source/doc SHA256, actual commands, fault type and outcomes. Preserve frozen outputs and earlier genuine positive observations; correct a new copy and recheck. The new fault check does not claim a real device failure, live external integration, field pilot or release approval.
