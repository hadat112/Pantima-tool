#!/bin/bash
# Preview all chat templates - mỗi template chạy trên 1 port khác nhau
# Usage: bash preview_all.sh
# Stop:  Ctrl+C

PORTS=(8901 8902 8903 8904 8905 8906)

cleanup() {
  echo ""
  echo "Stopping all preview servers..."
  for port in "${PORTS[@]}"; do
    pid=$(lsof -ti ":$port" 2>/dev/null)
    if [ -n "$pid" ]; then
      kill $pid 2>/dev/null
    fi
  done
  wait 2>/dev/null
  echo "Stopped."
  exit 0
}

trap cleanup SIGINT SIGTERM

# Kill any previous preview servers on these ports
for port in "${PORTS[@]}"; do
  pid=$(lsof -ti ":$port" 2>/dev/null)
  if [ -n "$pid" ]; then
    kill $pid 2>/dev/null
  fi
done
sleep 1

poetry run python preview_template.py ios_imessage      8901 &
poetry run python preview_template.py ios_whatsapp      8902 &
poetry run python preview_template.py android_whatsapp  8903 &
poetry run python preview_template.py telegram          8904 &
poetry run python preview_template.py messenger         8905 &
poetry run python preview_template.py luminati          8906 &

echo ""
echo "=== All templates running ==="
echo "  ios_imessage      → http://localhost:8901"
echo "  ios_whatsapp      → http://localhost:8902"
echo "  android_whatsapp  → http://localhost:8903"
echo "  telegram          → http://localhost:8904"
echo "  messenger         → http://localhost:8905"
echo "  luminati          → http://localhost:8906"
echo ""
echo "Press Ctrl+C to stop all."
wait
