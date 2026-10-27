| case | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 |
|---|---|---|---|---|---|---|---|---|
| C00 control: plain text | OK | OK | OK | OK | OK | OK | OK | OK |
| C01 accidental: ### subsection with unknown label | DESC_ALTERED+EXTRA_KEYS | DESC_ALTERED+EXTRA_KEYS | DESC_ALTERED+EXTRA_KEYS | DESC_ALTERED+EXTRA_KEYS | OK | DESC_ALTERED+EXTRA_KEYS | DESC_ALTERED+EXTRA_KEYS | OK |
| C02 accidental: ## and #### headings | DESC_ALTERED+EXTRA_KEYS | OK | OK | DESC_ALTERED+EXTRA_KEYS | OK | DESC_ALTERED+EXTRA_KEYS | OK | OK |
| C03 injection: bare ### Priority line | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | REJECT |
| C04 injection inside ``` fence | FIELD_CHANGED+DESC_ALTERED | OK | OK | DESC_ALTERED | DESC_ALTERED | OK | DESC_ALTERED | OK |
| C05 injection inside ~~~ fence | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | DESC_RESERIALIZED | DESC_ALTERED | OK |
| C06 injection inside ```` fence that contains ``` lines | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | OK | DESC_ALTERED | OK |
| C07 injection inside 4-space indented code | FIELD_CHANGED+DESC_ALTERED | OK | OK | DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | OK | OK |
| C08 injection as 2-space-indented ATX heading | FIELD_CHANGED+DESC_ALTERED | OK | OK | DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | OK | REJECT |
| C09 accidental: unterminated ``` fence | OK | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | OK | OK | FIELD_CHANGED+DESC_ALTERED | OK | REJECT |
| C10 injection inside HTML comment | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | OK |
| C11 injection of a new key | DESC_ALTERED+EXTRA_KEYS | DESC_ALTERED+EXTRA_KEYS | DESC_ALTERED+EXTRA_KEYS | DESC_ALTERED+EXTRA_KEYS | OK | DESC_ALTERED+EXTRA_KEYS | DESC_ALTERED+EXTRA_KEYS | OK |
| C12 control: '###Priority' without space (not a heading) | DESC_ALTERED | OK | OK | DESC_ALTERED | DESC_ALTERED | DESC_ESCAPED | OK | OK |
| C13 control: CRLF line endings | OK | OK | OK | OK | OK | OK | OK | OK |
| C14 fence break-out from a render:-wrapped textarea | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | DESC_ALTERED | REJECT |
| L03 desc-last: bare ### Priority line | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | REJECT |
| L05 desc-last: injection inside ~~~ fence | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | DESC_RESERIALIZED | FIELD_CHANGED+DESC_ALTERED | OK |
| L10 desc-last: injection inside HTML comment | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | OK |
| L14 desc-last: fence break-out from render:-wrapped textarea | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | FIELD_CHANGED+DESC_ALTERED | REJECT |

Counts over the 16 non-control cases (C00, C12, C13 are controls):

| parser | FIELD_CHANGED | DESC_ALTERED (content lost/added) | EXTRA_KEYS | REJECT | fully OK |
|---|---|---|---|---|---|
| P1 | 12 | 15 | 3 | 0 | 1 |
| P2 | 10 | 12 | 2 | 0 | 4 |
| P3 | 10 | 12 | 2 | 0 | 4 |
| P4 | 4 | 15 | 3 | 0 | 1 |
| P5 | 4 | 12 | 0 | 0 | 4 |
| P6 | 3 | 12 | 3 | 0 | 2 |
| P7 | 4 | 12 | 2 | 0 | 4 |
| P8 | 0 | 0 | 0 | 6 | 10 |

P1 = stefanbuck/github-issue-parser v3.2.4
P2 = stefanbuck/github-issue-parser v3.2.5
P3 = stefanbuck/github-issue-parser v3.2.5 +template
P4 = @github/issue-parser 2.0.0
P5 = @github/issue-parser 2.0.0 +template
P6 = @zentered/issue-forms-body-parser 3.0.0
P7 = baseline: naive split /^### /m (reference)
P8 = strict-AST reference (hypothesis defense, ours)
