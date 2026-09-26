"""V8.5 orchestrator around the audited Racing specialist chain."""
import os,sys,traceback,json
from pathlib import Path
import motogp_content_agency_v2 as agency
import racing_run_controller as rc
from racing_v855_hardening import install as install_v855_hardening

# Runtime hardening is installed before any Racing work starts.
install_v855_hardening(agency)
agency.VERSION=rc.ARCH_VERSION
_orig_send=agency.send_message
BATCH_ID=''
TELEGRAM_OUTBOX=Path(os.getenv('RACING_TELEGRAM_OUTBOX','/tmp/racing_telegram_outbox.jsonl'))

def _controlled_send(message):
    # Approval prompts must never become visible before their READY state is durable on main.
    if rc.notification_allowed('racing-status',str(message)):
        TELEGRAM_OUTBOX.parent.mkdir(parents=True,exist_ok=True)
        with TELEGRAM_OUTBOX.open('a',encoding='utf-8') as fh:
            fh.write(json.dumps(str(message),ensure_ascii=False)+'\\n')
        print('V8.5 TELEGRAM DEFERRED: waiting for durable persistence')
        return None
    print('V8.5 TELEGRAM SUPPRESSED: duplicate/rate-limited Racing notification')
    return None

def _session_status():
    try:
        raw=agency.SESSION.read_text(encoding='utf-8')
        if ('Approval-Status: READY' in raw or 'Approval-Status: FREIGEGEBEN' in raw) and 'QM: PASS' in raw:return 'READY_FOR_APPROVAL'
    except Exception:pass
    return 'BLOCKED'

def main():
    global BATCH_ID
    TELEGRAM_OUTBOX.unlink(missing_ok=True)
    ok,BATCH_ID,reason=rc.begin()
    if not ok:
        print(f'V8.5 RUN SUPPRESSED: {reason}; batch={BATCH_ID}')
        return 0
    agency.send_message=_controlled_send
    print(f'V8.5 RUN START batch={BATCH_ID} event={rc.event_name()} github_run={rc.github_run_id()}')
    try:
        agency.run_v8()
        status=_session_status();rc.transition(BATCH_ID,status)
        print(f'V8.5 RUN END batch={BATCH_ID} status={status}')
        return 0
    except Exception as e:
        rc.transition(BATCH_ID,'BLOCKED',error=f'{type(e).__name__}: {str(e)[:300]}')
        print('V8.5 FATAL:',type(e).__name__,str(e)[:300]);traceback.print_exc();return 1
    finally:
        agency.send_message=_orig_send

if __name__=='__main__':raise SystemExit(main())
