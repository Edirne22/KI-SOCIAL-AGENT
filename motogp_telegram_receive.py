"""Compatibility entrypoint for Racing V8.5 human approval.
Legacy MIN_SESSION_VERSION=10 is forbidden; V8.5 enforces session version 18 in motogp_telegram_receive_v85.
"""
from motogp_telegram_receive_v85 import *

if __name__=='__main__':
    main()
