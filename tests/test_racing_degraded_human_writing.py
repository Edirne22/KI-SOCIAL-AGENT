"""DEGRADED-PASS must never bypass deterministic Human Writing QM."""
import importlib
import motogp_content_agency_v2 as agency
import racing_v855_hardening as hardening

def main():
    importlib.reload(agency)
    importlib.reload(hardening).install(agency)
    item={"series":"MotoGP","source_series":"MotoGP","trusted_series":"MotoGP","series_locked":True,
          "title":"Fermin Aldeguer Japonya MotoGP Öncesi Ameliyat Oldu",
          "summary":"Fermin Aldeguer had surgery before the Japan MotoGP round."}
    outputs=[
      "Fermin Aldeguer musste kurz vor Japan operiert werden. 🏍️\n\nSo kurz vor dem Renne auf den OP-Tisch.\n\nWie seht ihr das?\n\n#MotoGP #FerminAldeguer #MotorradRacing #BuelentsBikeLife",
      "Fermin Aldeguer musste kurz vor Japan operiert werden. 🏍️\n\nSo kurz vor dem Rennen auf den OP-Tisch.\n\nWie seht ihr das?\n\n#MotoGP #FerminAldeguer #MotorradRacing #BuelentsBikeLife",
    ]
    calls={"editor":0}
    old_editor,old_racing,old_sem,old_reanalyse=agency.german_editor,agency.racing_review,agency.semantic_review_detailed,agency.reanalyse_source
    try:
      def editor(x,reasons=None,*a,**kw):
        i=min(calls["editor"],len(outputs)-1);calls["editor"]+=1;return outputs[i]
      agency.german_editor=editor
      agency.racing_review=lambda x,c:(True,[])
      agency.reanalyse_source=lambda x,*a,**kw:x
      agency.semantic_review_detailed=lambda x,c:{"hard_ok":False,"language_ok":False,"hard_reasons":["provider unavailable"],"repair_reasons":[],"technical_error":True,"technical_reason":"ProviderUnavailableError"}
      assert agency.qualify_copy(item) is True,item
      assert calls["editor"]==2,calls
      assert "vor dem Rennen" in item["caption"] and "vor dem Renne " not in item["caption"],item["caption"]
      assert item.get("semantic_qm")=="DEGRADED-PASS",item
      print("RACING DEGRADED HUMAN WRITING REGRESSION: PASS")
    finally:
      agency.german_editor,agency.racing_review,agency.semantic_review_detailed,agency.reanalyse_source=old_editor,old_racing,old_sem,old_reanalyse

if __name__=="__main__":main()
