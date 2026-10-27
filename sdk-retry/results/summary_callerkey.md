| SDK | scenario | attempts | same caller key on every attempt | header seen |
|---|---|---|---|---|
| anthropic | drop | 3 | yes | {"Idempotency-Key": "caller-k1-anthropic"} |
| anthropic | e500 | 3 | yes | {"Idempotency-Key": "caller-k1-anthropic"} |
| anthropic | timeout | 3 | yes | {"Idempotency-Key": "caller-k1-anthropic"} |
| groq | drop | 3 | yes | {"Idempotency-Key": "caller-k1-groq"} |
| groq | e500 | 3 | yes | {"Idempotency-Key": "caller-k1-groq"} |
| groq | timeout | 3 | yes | {"Idempotency-Key": "caller-k1-groq"} |
| openai | drop | 3 | yes | {"idempotency-key": "caller-k1-openai"} |
| openai | e500 | 3 | yes | {"idempotency-key": "caller-k1-openai"} |
| openai | timeout | 3 | yes | {"idempotency-key": "caller-k1-openai"} |
| together | drop | 3 | yes | {"Idempotency-Key": "caller-k1-together"} |
| together | e500 | 3 | yes | {"Idempotency-Key": "caller-k1-together"} |
| together | timeout | 3 | yes | {"Idempotency-Key": "caller-k1-together"} |
