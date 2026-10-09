# Synthetic APP technical journey, not a real user pilot

Build a small runnable local web booking application using Python standard library only.
Owner scenario supplied by maintainer: two teachers, anna and boris, each see only their own appointments. This is a local technical access-control scenario with explicit teacher identity headers, not production login/authentication. It must bind localhost and clearly label the identity mechanism as a demo.

Requirements frozen before model work:
- UI Russian, mobile/desktop, list and create own booking (student name, ISO date, slot HH:MM), show validation/conflict errors.
- persist JSON data across restart; unique (teacher,date,slot), repeated same request_id returns same booking, different request with occupied slot rejected.
- teacher isolation; never expose the other teacher's student names via list or id access.
- API POST/GET /api/bookings and GET /api/bookings/{id}; identity header X-Teacher: anna or boris, absent/unknown gets403. POST uses JSON teacher determined only by header.
- operations serialized to protect concurrent conflicting requests and atomic persistence; bad JSON produces 400. Dates must be real YYYY-MM-DD and slot HH:MM.
- local start command documented; backup/export/restore and retire procedure on disposable copy, no blind repeat external sends and no fake cancellation of subscriptions.
- future transfer: docs current purpose/rules/data/commands/ownership and the next rule can be changed by a new agent without prior chat. Include existing solution_record helper evidence if useful, not mandatory ritual.
- existing notes.txt byte preserved. Existing .agents and TASK.md must remain unchanged.
- do not call paid model/API, use accounts, global install, publish, or launch reviewer. A separate independent reviewer will inspect outcome.

This is technical synthetic coverage. No human usefulness, later real return, or production authentication is inferred.
