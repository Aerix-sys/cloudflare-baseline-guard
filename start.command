#!/bin/zsh
cd "${0:A:h}" || exit 1
export PYTHONPATH="$PWD/src"
python3 -m cfguard.web --port 8765 &
server_pid=$!
sleep 1
if kill -0 "$server_pid" 2>/dev/null; then
  open "http://127.0.0.1:8765"
  echo "Press Ctrl+C to stop the app."
  wait "$server_pid"
else
  wait "$server_pid"
fi
