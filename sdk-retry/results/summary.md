| SDK (version) | scenario | attempts per logical call (3 reps) | idempotency header sent | same key on every attempt | client saw a timeout |
|---|---|---|---|---|---|
| openai 3.37.0 | e500 | 3, 3, 3 | no | n/a | no |
| openai 3.37.0 | timeout | 3, 3, 3 | no | n/a | yes |
| openai 3.37.0 | drop | 3, 3, 3 | no | n/a | no |
| anthropic 2.3.0 | e500 | 3, 3, 3 | no | n/a | no |
| anthropic 2.3.0 | timeout | 3, 3, 3 | no | n/a | yes |
| anthropic 2.3.0 | drop | 3, 3, 3 | no | n/a | no |
| groq 1.7.0 | e500 | 3, 3, 3 | no | n/a | no |
| groq 1.7.0 | timeout | 3, 3, 3 | no | n/a | yes |
| groq 1.7.0 | drop | 3, 3, 3 | no | n/a | no |
| together 3.0.0 | e500 | 3, 3, 3 | no | n/a | no |
| together 3.0.0 | timeout | 3, 3, 3 | no | n/a | yes |
| together 3.0.0 | drop | 3, 3, 3 | no | n/a | no |
| mistralai 3.5.0 | e500 | 1, 1, 1 | no | n/a | no |
| mistralai 3.5.0 | timeout | 1, 1, 1 | no | n/a | yes |
| mistralai 3.5.0 | drop | 1, 1, 1 | no | n/a | no |
| cohere 7.3.0 | e500 | 3, 3, 3 | no | n/a | no |
| cohere 7.3.0 | timeout | 1, 1, 1 | no | n/a | yes |
| cohere 7.3.0 | drop | 3, 3, 3 | no | n/a | no |
| replicate 1.0.7 | e500 | 1, 1, 1 | no | n/a | no |
| replicate 1.0.7 | timeout | 1, 1, 1 | no | n/a | no |
| replicate 1.0.7 | drop | 1, 1, 1 | no | n/a | no |
| fal-client 1.0.3 | e500 | 1, 1, 1 | no | n/a | no |
| fal-client 1.0.3 | timeout | 10, 10, 10 | no | n/a | yes |
| fal-client 1.0.3 | drop | 10, 10, 10 | no | n/a | no |
| google-genai 2.33.0 | e500 | 1, 1, 1 | no | n/a | no |
| google-genai 2.33.0 | timeout | 1, 1, 1 | no | n/a | yes |
| google-genai 2.33.0 | drop | 1, 1, 1 | no | n/a | no |

Total logical calls: 81; total duplicate POSTs reaching the stub: 138; calls with >1 attempt: 48; duplicate POSTs carrying a stable idempotency key: 0.
