"""Deploy (or refresh) a Node-RED flow that keeps the live bolão site updated.

Every 15 min the flow fetches the published data.js, and if any knockout match
is inside its end-window (kicked off 85–230 min ago and not yet decided) it calls
the GitHub workflow_dispatch API to trigger an immediate deploy — bypassing the
laggy GitHub schedule. Runs in the always-on Node-RED container (restart:
unless-stopped), so it survives reboots.

The GitHub token is read from `gh auth token` at deploy time and embedded into
the flow (Lucas opted to reuse it). This script itself stays token-free.

Usage:  python3 scripts/setup_nodered_watcher.py
"""
import json
import os
import urllib.request

NODE_RED = "http://192.168.1.107:1880"
TAB = "bolaoflow"

DECIDE = r"""
var txt = msg.payload || "";
var K;
try { K = JSON.parse(txt.substring(txt.indexOf("=") + 1).replace(/;\s*$/, "")); }
catch (e) { node.warn("data.js parse fail"); return null; }
var now = Date.now(), fire = false;
(K.stages || []).forEach(function (s) {
  (s.matches || []).forEach(function (m) {
    if (!m.date) return;
    var age = (now - new Date(m.date).getTime()) / 60000; // min since kickoff
    if (age >= 85 && age <= 230 && !m.winner) fire = true; // reg+ET+pens+API lag, undecided
  });
});
if (!fire) { node.status({ fill: "grey", shape: "ring", text: "sem jogo na janela" }); return null; }
node.status({ fill: "green", shape: "dot", text: "dispatch " + new Date().toISOString().slice(11, 16) });
msg.method = "POST";
msg.url = "https://api.github.com/repos/lvolcov/bolao-da-copa/actions/workflows/deploy.yml/dispatches";
msg.headers = {
  "Authorization": "Bearer __TOKEN__",
  "Accept": "application/vnd.github+json",
  "X-GitHub-Api-Version": "2022-11-28",
  "Content-Type": "application/json",
  "User-Agent": "node-red-bolao"
};
msg.payload = { ref: "main" };
return msg;
"""


def build_nodes(token: str):
    return [
        {"id": TAB, "type": "tab", "label": "Bolão auto-deploy", "disabled": False, "info":
            "A cada 15 min: se houver jogo do mata-mata terminando, dispara o deploy do GitHub Pages."},
        {"id": "bolao_tick", "type": "inject", "z": TAB, "name": "a cada 15 min",
         "props": [{"p": "payload"}], "repeat": "900", "crontab": "", "once": True, "onceDelay": "25",
         "topic": "", "payload": "", "payloadType": "date", "x": 150, "y": 100, "wires": [["bolao_get"]]},
        {"id": "bolao_get", "type": "http request", "z": TAB, "name": "GET data.js (live)",
         "method": "GET", "ret": "txt", "paytoqs": "ignore",
         "url": "https://lvolcov.github.io/bolao-da-copa/data.js", "persist": False,
         "x": 370, "y": 100, "wires": [["bolao_decide"]]},
        {"id": "bolao_decide", "type": "function", "z": TAB, "name": "jogo terminando? → dispatch",
         "func": DECIDE.replace("__TOKEN__", token), "outputs": 1, "noerr": 0,
         "x": 620, "y": 100, "wires": [["bolao_post"]]},
        {"id": "bolao_post", "type": "http request", "z": TAB, "name": "GitHub workflow_dispatch",
         "method": "use", "ret": "txt", "paytoqs": "ignore", "url": "", "persist": False,
         "x": 880, "y": 100, "wires": [["bolao_dbg"]]},
        {"id": "bolao_dbg", "type": "debug", "z": TAB, "name": "resp", "active": True,
         "tosidebar": True, "console": False, "complete": "statusCode", "x": 1080, "y": 100, "wires": []},
    ]


def gh_token() -> str:
    path = os.path.expanduser("~/.config/gh/hosts.yml")
    for line in open(path):
        s = line.strip()
        if s.startswith("oauth_token:"):
            return s.split(":", 1)[1].strip()
    raise SystemExit("oauth_token not found in gh hosts.yml")


def main():
    token = gh_token()
    cur = json.load(urllib.request.urlopen(NODE_RED + "/flows", timeout=10))
    keep = [n for n in cur if n.get("z") != TAB and n.get("id") != TAB]  # drop old version
    merged = keep + build_nodes(token)
    req = urllib.request.Request(
        NODE_RED + "/flows", data=json.dumps(merged).encode(), method="POST",
        headers={"Content-Type": "application/json", "Node-RED-Deployment-Type": "full"})
    r = urllib.request.urlopen(req, timeout=15)
    print(f"Node-RED deploy: HTTP {r.status} — flow '{TAB}' instalado ({len(build_nodes(token))} nós)")


if __name__ == "__main__":
    main()
