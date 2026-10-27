"""Voice approval-gate pilot (research stub, $0, offline).
Synthetic replies (espeak-ng, no human voices) -> 16 kHz WAV -> Vosk streaming recognizer
fed in 100 ms chunks. Four gate policies decide on the partial/final transcript stream.
Outputs results/clips.jsonl and results/summary.json. HYPOTHESIS under test: committing on
the first affirmative partial produces false approvals on hesitant replies."""
import json, os, re, subprocess, sys, wave
from vosk import Model, KaldiRecognizer, SetLogLevel
SetLogLevel(-1)
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "replies.json")))
VOICES = [("en-us", 150), ("en-us", 190), ("en-gb", 150), ("en-gb", 190), ("en-us+f3", 170), ("en-gb-x-rp", 170)]
AFF = re.compile(r"\b(yes|yeah|yep|okay|ok|sure|approved?|go ahead|do it)\b")
NEG = re.compile(r"\b(no|not|don't|dont|wait|hold|cancel|stop|but|actually|later|keep|mean|guess|after)\b")
CHUNK = 1600  # 100 ms at 16 kHz mono 16-bit

def synth(text, voice, speed, path):
    tmp = path + ".raw.wav"
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-w", tmp, text], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-ar", "16000", "-ac", "1", path], check=True)
    os.remove(tmp)

def stream(model, path):
    wf = wave.open(path, "rb"); rec = KaldiRecognizer(model, 16000); rec.SetWords(False)
    partials, t, finals = [], 0.0, []
    while True:
        data = wf.readframes(CHUNK)
        if not data: break
        t += len(data) / 2 / 16000
        if rec.AcceptWaveform(data):
            finals.append(json.loads(rec.Result()).get("text", ""))
        else:
            p = json.loads(rec.PartialResult()).get("partial", "")
            if p and (not partials or partials[-1][1] != p): partials.append((round(t, 2), p))
    finals.append(json.loads(rec.FinalResult()).get("text", ""))
    return partials, " ".join(f for f in finals if f).strip(), round(t, 2)

def gates(partials, final, dur, action):
    first = next((ts for ts, p in partials if AFF.search(p)), None)
    out = {"P1_first_affirmative_partial": (first is not None or bool(AFF.search(final)), first if first is not None else dur),
           "P2_final_affirmative": (bool(AFF.search(final)), dur),
           "P3_final_affirmative_no_negation": (bool(AFF.search(final)) and not NEG.search(final), dur),
           "P4_P3_plus_action_echo": (bool(AFF.search(final) or action in final) and not NEG.search(final) and action in final, dur)}
    return out

def main():
    model = Model(os.path.join(HERE, "models", "vosk-model-small-en-us-0.15"))
    os.makedirs(os.path.join(HERE, "results", "wav"), exist_ok=True)
    rows = []
    for i, r in enumerate(CFG["replies"]):
        for v, s in VOICES:
            wav = os.path.join(HERE, "results", "wav", f"r{i:02d}_{v.replace('+','_')}_{s}.wav")
            synth(r["text"], v, s, wav)
            partials, final, dur = stream(model, wav)
            g = gates(partials, final, dur, CFG["action_word"])
            rows.append({"reply": r["text"], "approve": r["approve"], "voice": v, "speed": s, "dur_s": dur,
                         "partials": partials, "final": final,
                         "decisions": {k: {"approve": a, "decided_at_s": t} for k, (a, t) in g.items()}})
    with open(os.path.join(HERE, "results", "clips.jsonl"), "w") as f:
        for x in rows: f.write(json.dumps(x) + "\n")
    summ = {"n_clips": len(rows), "n_replies": len(CFG["replies"]), "voices": VOICES, "policies": {}}
    for k in rows[0]["decisions"]:
        fa = sum(1 for x in rows if x["decisions"][k]["approve"] and not x["approve"])
        fr = sum(1 for x in rows if not x["decisions"][k]["approve"] and x["approve"])
        npos = sum(1 for x in rows if x["approve"]); nneg = len(rows) - npos
        lead = [x["dur_s"] - x["decisions"][k]["decided_at_s"] for x in rows if x["decisions"][k]["approve"]]
        summ["policies"][k] = {"false_approvals": fa, "of_non_approvals": nneg, "false_rejections": fr, "of_approvals": npos,
                               "mean_decision_lead_s": round(sum(lead) / len(lead), 3) if lead else None}
    summ["final_exact_match"] = sum(1 for x in rows if x["final"] == re.sub(r"[^a-z' ]", "", x["reply"].lower()).replace("  ", " ").strip())
    json.dump(summ, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))

if __name__ == "__main__":
    main()
