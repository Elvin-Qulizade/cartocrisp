"""Run the cartocrisp web UI locally and open it in the default browser."""
import webbrowser

import uvicorn


def run_server(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    if open_browser:
        webbrowser.open(f"http://{host}:{port}")
    uvicorn.run("cartocrisp.web.app:app", host=host, port=port)
