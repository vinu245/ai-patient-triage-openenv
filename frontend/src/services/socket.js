const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws`;

export function createSocket(onMessage) {
  let ws;
  let heartbeat;

  const connect = () => {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, 8000);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        onMessage(payload);
      } catch {
        // Ignore malformed messages.
      }
    };

    ws.onclose = () => {
      if (heartbeat) {
        clearInterval(heartbeat);
      }
      setTimeout(connect, 2000);
    };
  };

  connect();

  return () => {
    if (heartbeat) {
      clearInterval(heartbeat);
    }
    if (ws && ws.readyState <= 1) {
      ws.close();
    }
  };
}
