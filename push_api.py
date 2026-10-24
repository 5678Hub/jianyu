#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub API 推送封装
背景：本机代理(127.0.0.1:61114) 对 github.com 的 CONNECT 隧道返回 502，
      git push 走不通；但 api.github.com / codeload.github.com 正常。
方案：改用 GitHub REST API 的 Contents API 直接 PUT 文件，绕过 git 协议。

用法：
    python push_api.py --git "<提交信息>"          # 推荐：走 git push 通道（多文件一次推）
    python push_api.py "<文件路径>" "<提交信息>"    # REST Contents API（单文件）
    python push_api.py --token ghp_xxx            # 验证 token
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error

PROXY = "http://127.0.0.1:7897"
REPO = "5678Hub/jianyu"
API = "https://api.github.com"


def _opener():
    handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    return urllib.request.build_opener(handler)


def api(token, method, path, body=None, timeout=60):
    url = API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Accept", "application/vnd.github+json")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with _opener().open(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:500]}


def get_token():
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok.strip()
    # 回退到 GCM 已存凭据
    # ⚠ 2026-10-24：本机 GCM 未存 github.com 凭据（GitHub CLI 目录为空、无 .git-credentials），
    #   `git credential fill` 在无头环境会**挂起等交互**而不是返回空 → 必须加短 timeout 并容忍超时
    try:
        import subprocess
        p = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=8,
        )
        for line in p.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def push_git(token, message="update", branch="main"):
    """git push 通道：绕开 GCM 交互弹窗，直接注入 Authorization header

    背景：本机 GCM 无 github.com 凭据，git push 会挂起等待账号密码输入。
    方案：credential.helper 置空 + http.extraheader 注入 Basic 认证。
    注意：代理对 github.com 的 CONNECT 隧道不稳定（时通时 502），
          失败时由调用方回退到 REST API 通道。
    """
    import base64
    import subprocess

    cred = base64.b64encode(("x-access-token:" + token).encode()).decode()
    msg = message.splitlines()[0] if message else "update"
    cmd = [
        "git", "-c", "credential.helper=",
        "-c", "http.https://github.com/.extraheader=Authorization: Basic " + cred,
        "push", "origin", branch,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    out = (p.stdout + p.stderr).strip()
    if p.returncode == 0:
        print("[OK] git push 成功")
        print("    " + "\n    ".join(out.splitlines()[-3:]))
        return 0
    print("[X] git push 失败 rc=%d（代理 CONNECT 隧道不稳定，可重试或改用 API 通道）" % p.returncode)
    print("    " + "\n    ".join(out.splitlines()[-4:]))
    return 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    token = get_token()
    if not token:
        print("[X] 找不到 token")
        return 1

    # token 自检
    if sys.argv[1] == "--token" or (len(sys.argv) == 2 and sys.argv[1].startswith("gh")):
        st, data = api(token, "GET", "/user")
        if st == 200:
            print("[OK] token 有效，账号 =", data.get("login"))
            return 0
        print("[X] token 无效 HTTP", st, str(data)[:300])
        return 1

    file_path = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else "update"
    branch = sys.argv[3] if len(sys.argv) > 3 else "main"

    # --git：走 git push 通道（多文件一次推，推荐）
    if file_path == "--git":
        return push_git(token, message, branch)

    with open(file_path, "rb") as f:
        content = f.read()
    b64 = base64.b64encode(content).decode()

    api_path = "/repos/{}/contents/{}".format(REPO, file_path.replace("\\", "/"))

    # 先取现有 sha
    st, info = api(token, "GET", api_path + "?ref=" + branch)
    sha = info.get("sha") if st == 200 else None

    body = {
        "message": message,
        "content": b64,
        "branch": branch,
    }
    if sha:
        body["sha"] = sha

    st, info = api(token, "PUT", api_path, body, timeout=120)
    if st in (200, 201):
        print("[OK] 推送成功 ->", info.get("commit", {}).get("sha", "")[:7],
              "|", info.get("commit", {}).get("message", "").splitlines()[0])
        return 0
    print("[X] 推送失败 HTTP", st, json.dumps(info, ensure_ascii=False)[:600])
    return 1


if __name__ == "__main__":
    sys.exit(main())