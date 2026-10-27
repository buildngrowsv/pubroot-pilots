# Pilot: spoken approval gates over streaming ASR

Code for *Spoken Approval as a Human Gate for Agent Actions: How Often Do Streaming Transcripts Turn a Hesitant Reply into a False Yes?*

Run locally on 2026-10-26 (America/Chicago). Cost was $0, and the run is fully offline once the model is downloaded. **Synthetic speech only:** there are no human voices or recordings and no personal data.

## Inputs
- `replies.json`: 24 scripted replies to the prompt "Delete the staging branch?". 8 are approvals; 16 are non-approvals (hesitant, negated, conditional or off-topic).
- TTS: espeak-ng 1.52.0 in 6 voice settings (en-us 150/190 wpm, en-gb 150/190, en-us+f3 170, en-gb-x-rp 170). That gives 144 clips, converted by ffmpeg to 16 kHz mono.
- ASR: Vosk 0.3.45 with `vosk-model-small-en-us-0.15`. `fetch_model.sh` downloads it and checks the zip's SHA-256 (`30f26242…942498`). Audio is streamed in 0.1 s chunks so partial results are captured.

## Policies (`pilot.py`)
- P1: approve on the first affirmative partial.
- P2: approve if the final transcript has an affirmative.
- P3: P2, plus no negation or hold word.
- P4: P3, plus the action must be echoed ("delete").

## Results (`results/summary.json`; per clip in `results/clips.jsonl`)
| Policy | False approvals / 96 | False rejections / 48 |
|---|---|---|
| P1 | 51 | 14 |
| P2 | 45 | 18 |
| P3 | 2 | 18 |
| P4 | 5 | 37 |

The final transcript matched the script exactly in 66 of 144 clips.

## Run (about 80 s)
```bash
sudo apt-get install espeak-ng ffmpeg        # espeak-ng 1.52.0 was used
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # requirements.lock.txt = full freeze
./fetch_model.sh
.venv/bin/python pilot.py                    # rewrites results/clips.jsonl and results/summary.json
```

Re-run check (2026-10-26, from a clean copy of this folder, model downloaded by `fetch_model.sh`, checksum OK): `summary.json` was reproduced byte for byte, and all 576 gate decisions (144 clips × 4 policies) matched. 7 of the 144 clips came out with slightly different Vosk partial-transcript text, 3 of them with a different final transcript as well, so `clips.jsonl` is not byte-identical between runs.

**Not committed:** `.venv/`, `models/` (a third-party model, downloaded by `fetch_model.sh`) and `results/wav/` (the 144 generated clips, which `pilot.py` regenerates).
