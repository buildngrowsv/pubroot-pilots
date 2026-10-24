# Window sensitivity (LangGraph runs, effect-log saga recovery, non-trivial runs)

| Window (ticks) | email_send label | Order | n | clean | residue | stuck | window-closed inverses |
|---|---|---|---|---|---|---|---|
| 1 | windowed | original | 33 | 6 | 8 | 19 | 16 |
| 1 | windowed | irreversible_last | 33 | 6 | 10 | 17 | 16 |
| 3 | windowed | original | 33 | 8 | 10 | 15 | 12 |
| 3 | windowed | irreversible_last | 33 | 8 | 12 | 13 | 12 |
| 6 | windowed | original | 33 | 10 | 14 | 9 | 4 |
| 6 | windowed | irreversible_last | 33 | 10 | 18 | 5 | 4 |
| 12 | windowed | original | 33 | 10 | 14 | 9 | 0 |
| 12 | windowed | irreversible_last | 33 | 10 | 20 | 3 | 0 |
