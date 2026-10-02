"""Guarded first boot of Chatterbox Multilingual V3.

Use synthetic espeak reference only; owner voice is never in GitHub.
The selected model MUST be multilingual and the output is *not* a successful
voice-clone of Bülent. Bounded CPU startup for existing CI runner resources.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def startup(*, load_model: bool=False) -> dict:
    import chatterbox.mtl_tts as multilingual
    # Explicit identity, not the English-only Nano/Turbo class.
    model_type=multilingual.ChatterboxMultilingualTTS
    result={"engine":"ChatterboxMultilingualTTS","device":"cpu",
            "owner_voice_used":False,"runtime_import":"PASS",
            "model_load":"NOT_RUN","speech_generation":"NOT_RUN",
            "user_voice_acceptance":"NOT_RUN"}
    if not load_model:
        return result
    import torch
    import torchaudio
    torch.set_num_threads(min(2,os.cpu_count() or 1))
    start=time.monotonic()
    model=model_type.from_pretrained(device="cpu")
    result["model_load"]="PASS"
    result["load_s"]=round(time.monotonic()-start,2)
    with tempfile.TemporaryDirectory(prefix="block7-chatterbox-") as temp:
        ref=Path(temp)/"synthetic-reference.wav"
        subprocess.run(["espeak-ng","-v","de","-s","150","-w",str(ref),
                        "Hallo dies ist eine synthetische Teststimme."],
                       check=True,timeout=30,stdout=subprocess.DEVNULL)
        if ref.stat().st_size<1000:
            raise RuntimeError("synthetic reference failed")
        for lang,text in (("de","Willkommen zum technischen Audiotest."),
                          ("tr","Merhaba, bu bir ses denemesidir.")):
            started=time.monotonic()
            generated=model.generate(text,audio_prompt_path=str(ref),
                                     language_id=lang)
            out=Path(temp)/f"synthetic-{lang}.wav"
            torchaudio.save(str(out),generated.cpu(),model.sr)
            if out.stat().st_size<1000:
                raise RuntimeError(f"{lang} yielded empty WAV")
            result[f"{lang}_synthetic"]={
                "wav_bytes":out.stat().st_size,
                "generation_s":round(time.monotonic()-started,2)}
    result["speech_generation"]="PASS_SYNTHETIC_REFERENCE_NOT_VOICE_CLONE"
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--real-model",action="store_true")
    x=p.parse_args()
    out=startup(load_model=x.real_model)
    print("BLOCK7_CHATTERBOX_BOOT "+json.dumps(out,sort_keys=True))


if __name__=="__main__":
    main()
