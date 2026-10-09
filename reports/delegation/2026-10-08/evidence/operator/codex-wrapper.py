#!/usr/bin/python3
import os, sys
args=sys.argv[1:]
if args and args[0]=='exec':
    args[1:1]=['--ignore-user-config','--ignore-rules',
        '-c','web_search="disabled"','-c','features.apps=false',
        '-c','features.plugins=false','-c','features.memory_tool=false',
        '-c','model="gpt-6.1-sol"','-c','model_reasoning_effort="high"',
        '-c','agents.max_threads=4','-c','agents.max_depth=1']
os.execv('/usr/lib/node_modules/@openai/codex/bin/codex.js',['/usr/lib/node_modules/@openai/codex/bin/codex.js',*args])
