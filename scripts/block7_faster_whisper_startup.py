"""Block 7: real CPU faster-whisper bootstrap using synthetic samples only.

No owner voice, private source or external paid API. All generated smoke
files stay in GitHub runner temporary storage and get automatically deleted.
Synthetic TTS audio cannot validate real DE/TR transcription quality.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import time


def _run(cmd: list[str], *, timeout: int=50) -> None:
    subprocess.run(cmd,check=True,timeout=timeout,stdout=subprocess.DEVNULL,
                   stderr=subprocess.PIPE)


def startup(*, model_name: str="tiny", output_dir: Path | None=None) -> dict:
    from faster_whisper import WhisperModel
    started=time.monotonic()
    model=WhisperModel(model_name,device="cpu",compute_type="int8",
                       cpu_threads=min(2,os.cpu_count() or 1))
    load_s=round(time.monotonic()-started,2)
    reports=[]
    with tempfile.TemporaryDirectory(prefix="block7-whisper-") as temp:
        base=Path(temp)
        # Offline espeak synthetic pronunciations are only mechanical proof
        # that real model inference/timestamps can execute. Never quality PASS.
        for lang,phrase in (
            ("de","Guten Tag. Hier spricht unsere technische Teststimme."),
            ("tr","Merhaba. Bu sadece teknik bir ses denemesidir."),
        ):
            wav=base/f"synthetic-{lang}.wav"
            _run(["espeak-ng","-v",lang,"-s","140","-w",str(wav),phrase])
            if not wav.is_file() or wav.stat().st_size<1000:
                raise RuntimeError(f"synthetic_{lang}_fixture_missing")
            start=time.monotonic()
            segments,info=model.transcribe(str(wav),language=lang,beam_size=1,
                                           word_timestamps=True,vad_filter=False)
            # faster-whisper inference does not run before consuming generator.
            finished=list(segments)
            if not finished or not any(s.text.strip() for s in finished):
                raise RuntimeError(f"real_{lang}_asr_returned_no_text")
            if not all(s.end>s.start>=0 for s in finished):
                raise RuntimeError(f"real_{lang}_segment_timestamps_invalid")
            words=[w for seg in finished for w in (seg.words or ())]
            if not words or not all(w.end>=w.start>=0 for w in words):
                raise RuntimeError(f"real_{lang}_word_timestamps_invalid")
            reports.append({"lang":lang,"segments":len(finished),
                            "words":len(words),
                            "inference_s":round(time.monotonic()-start,2),
                            "quality":"UNVERIFIED_SYNTHETIC_SPEAKER",
                            "recognized_language":info.language})
            if output_dir:
                output_dir.mkdir(parents=True,exist_ok=True)
                lines=[]
                for index,seg in enumerate(finished,1):
                    def ts(sec):
                        n=round(sec*1000)
                        return f"{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}"
                    lines.append(f"{index}\n{ts(seg.start)} --> {ts(seg.end)}\n{seg.text.strip()}\n")
                (output_dir/f"synthetic-{lang}.srt").write_text(
                    "\n".join(lines)+"\n",encoding="utf-8")
    return {"engine":"faster-whisper","model":model_name,"device":"cpu",
            "compute_type":"int8","load_s":load_s,"results":reports,
            "truth":"REAL_INFERENCE_SYNTHETIC_AUDIO_NOT_USER_ACCEPTANCE"}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--model",default="tiny")
    parser.add_argument("--out",type=Path,default=None)
    args=parser.parse_args()
    report=startup(model_name=args.model,output_dir=args.out)
    import json
    print("BLOCK7_FASTER_WHISPER_REAL_CPU_SMOKE "+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
