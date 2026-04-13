"""
Session Lifecycle:
created
-> ready
-> active
-> paused
-> active
-> completed

created
-> cancelled

active
-> cancelled

Meanings:
- created: session DB record exists
- ready: rounds/questions/config resolved, not live yet
- active: live interview running
- paused: temporarily halted
- completed: normal end
- cancelled: abnormal/user end
"""
