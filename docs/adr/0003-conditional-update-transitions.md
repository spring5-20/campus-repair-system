# State transitions use conditional UPDATE, not row locks

Accept, assign, and status transitions must be concurrency-safe and return 409 on conflict, and tests run on aiosqlite. We decided to issue a conditional `UPDATE ... WHERE id = ? AND status = <expected>` (plus owner conditions), treat a zero rowcount as 409, and write the TicketLog in the same transaction. Rejected alternatives: `SELECT ... FOR UPDATE` (semantics differ on aiosqlite) and application-level locks (unnecessary complexity for a classroom data volume).
