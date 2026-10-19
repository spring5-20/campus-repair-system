# Sequential TicketNo via a counter row

The prototype displays ticket numbers as `REP-0001`, and the PRD requires a unique `ticketNo`, but a naive `MAX(ticketNo)+1` races under concurrency. We decided to keep the prototype format and generate each number from a dedicated counter row incremented atomically inside the ticket-creation transaction. Rejected alternatives: date-prefixed numbers (breaks the prototype baseline), UUIDs (not human-friendly), and `MAX()+1` (not safe under concurrent creates).
