from app import create_app, socketio
from apscheduler.schedulers.background import BackgroundScheduler
from services.games import get_games
import threading
import datetime
import os
import requests

from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

app = create_app()
scheduler = BackgroundScheduler()

TOKEN_URL = "https://safeguard-platform.m4d.iti.gr/auth/realms/SAFEGUARD/protocol/openid-connect/token"


def _persist_neo4j_tokens(access_token: str, refresh_token: str | None) -> None:
    """
    Store tokens in process env and persist them to the project .env file.
    """
    # Store in process environment for this runtime
    os.environ["NEO4J_TOKEN"] = access_token
    if refresh_token:
        os.environ["NEO4J_REFRESH_TOKEN"] = refresh_token

    # Also persist to the .env file at the project root
    try:
        # main.py is under Twitch_API/, project root is one level up
        project_root = os.path.dirname(os.path.dirname(__file__))
        env_path = os.path.join(project_root, ".env")

        lines: list[str] = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

        def upsert_key(key: str, value: str) -> None:
            prefix = f"{key}="
            for i, line in enumerate(lines):
                if line.startswith(prefix):
                    lines[i] = f"{prefix}{value}"
                    break
            else:
                lines.append(f"{prefix}{value}")

        upsert_key("NEO4J_TOKEN", access_token)
        if refresh_token:
            upsert_key("NEO4J_REFRESH_TOKEN", refresh_token)

        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        print("NEO4J_TOKEN and NEO4J_REFRESH_TOKEN persisted to .env.")
    except OSError as e:
        print(f"WARNING: Failed to persist Neo4j tokens to .env: {e}")


def generate_neo4j_token() -> None:
    client_id = os.getenv("NEO4J_CLIENT_ID")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    client_secret = os.getenv("NEO4J_CLIENT_SECRET")

    if not all([client_id, username, password, client_secret]):
        print(
            "WARNING: Missing one or more Neo4j auth env vars "
            "(NEO4J_CLIENT_ID, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_CLIENT_SECRET). "
            "Skipping initial NEO4J_TOKEN generation."
        )
        return

    data = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password,
        "client_secret": client_secret,
        "scope": "offline_access",
    }

    try:
        response = requests.post(TOKEN_URL, data=data)
        response.raise_for_status()
        body = response.json()
        access_token = body.get("access_token")
        refresh_token = body.get("refresh_token")

        if not access_token:
            print("WARNING: Token endpoint response did not contain 'access_token'.")
            return

        _persist_neo4j_tokens(access_token, refresh_token)
        print("NEO4J tokens successfully generated and stored.")
    except requests.RequestException as e:
        print(f"ERROR: Failed to generate NEO4J_TOKEN: {e}")


def refresh_neo4j_token() -> None:
    """
    Refresh the Neo4j tokens using the latest refresh token and update
    both env vars and .env file.
    """
    print(f"[Neo4J Token Refresh] Running at {datetime.datetime.utcnow().isoformat()}Z")

    client_id = os.getenv("NEO4J_CLIENT_ID")
    client_secret = os.getenv("NEO4J_CLIENT_SECRET")
    refresh_token = os.getenv("NEO4J_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print(
            "WARNING: Cannot refresh Neo4j token; missing one of "
            "NEO4J_CLIENT_ID, NEO4J_CLIENT_SECRET, NEO4J_REFRESH_TOKEN."
        )
        return

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        response = requests.post(TOKEN_URL, data=data)
        response.raise_for_status()
        body = response.json()
        new_access_token = body.get("access_token")
        new_refresh_token = body.get("refresh_token")

        if not new_access_token or not new_refresh_token:
            print(
                "WARNING: Refresh response missing 'access_token' or 'refresh_token'; "
                "tokens not updated."
            )
            return

        _persist_neo4j_tokens(new_access_token, new_refresh_token)
        print("NEO4J tokens successfully refreshed and stored.")
    except requests.RequestException as e:
        print(f"ERROR: Failed to refresh Neo4j token: {e}")


def run_scheduler() -> None:
    with app.app_context():
        # get_games(None, {"data": []})
        # scheduler.add_job(
        #     func=get_games,
        #     args=(None, {"data": []}),
        #     trigger="interval",
        #     hours=3,
        # )
        # Refresh Neo4j tokens every 15 minutes
        scheduler.add_job(
            func=refresh_neo4j_token,
            trigger="interval",
            minutes=20,
        )
        print("Scheduler started at ", datetime.datetime.now())
        scheduler.start()


def run_app() -> None:
    print("> Starting socketio.run(app)")
    socketio.run(
        app,
        port=3000,
        host="0.0.0.0",
        use_reloader=False,
        allow_unsafe_werkzeug=True,
        debug=True,
    )


if __name__ == "__main__":
    # Initial Neo4j token generation on startup
    generate_neo4j_token()

    # Start background scheduler for games + token refresh
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    run_app()