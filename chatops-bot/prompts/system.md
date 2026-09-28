# InsightHub ChatOps system contract

This directory is the versioned home for ChatOps prompt assets.

The Day 5 bot must answer only supported operational intents using bounded,
read-only tools. It must not expose secrets, document content, tokens, or
unfiltered tool output. Mutating actions require a separate service identity
and an approval bound to the exact action, arguments, requesting user, and
expiry.

Transport authentication, permission enforcement, audit logging, queueing,
deduplication, and retry remain application responsibilities; prompt text is
not a security boundary.
