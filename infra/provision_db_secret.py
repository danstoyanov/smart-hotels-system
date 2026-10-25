"""Create the one demo SQL user and put its URL in Secret Manager.

The password stays in process memory. This command prints no credential or URL.
Run it once after the approved SQL instance and database exist.
"""

import argparse
import base64
import secrets
import time
from urllib.parse import quote

import google.auth
from google.auth.transport.requests import AuthorizedSession


def request(session, method, url, *, body=None):
    response = session.request(method, url, json=body, timeout=30)
    if not response.ok:
        raise RuntimeError(f"Cloud API request failed: HTTP {response.status_code}")
    return response.json()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="Check resources without changes")
    action.add_argument("--apply", action="store_true", help="Create the user and secret version")
    args = parser.parse_args()

    project = "smart-hotels-system"
    region = "europe-central2"
    instance = "smart-hotel-demo-db"
    database = "smart_hotels"
    user = "smart_hotels"
    secret = "smart-hotel-database-url"
    sql = f"https://sqladmin.googleapis.com/sql/v1beta4/projects/{project}/instances/{instance}"
    vault = f"https://secretmanager.googleapis.com/v1/projects/{project}/secrets/{secret}"

    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    session = AuthorizedSession(credentials)
    state = request(session, "GET", sql)
    if state.get("state") != "RUNNABLE" or state.get("region") != region:
        raise RuntimeError("The approved SQL instance is not ready in the approved region")
    databases = request(session, "GET", f"{sql}/databases").get("items", [])
    if database not in {item["name"] for item in databases}:
        raise RuntimeError("The approved demo database does not exist")
    users = request(session, "GET", f"{sql}/users").get("items", [])
    if user in {item["name"] for item in users}:
        raise RuntimeError("Demo SQL user already exists; refusing to rotate its password")
    versions = request(session, "GET", f"{vault}/versions").get("versions", [])
    if versions:
        raise RuntimeError("Database secret already has a version; refusing to replace it")
    if args.check:
        print("Approved SQL instance, database and empty secret are ready.")
        return

    password = secrets.token_urlsafe(36)
    operation = request(
        session,
        "POST",
        f"{sql}/users",
        body={"name": user, "password": password, "type": "BUILT_IN"},
    )
    operation_url = (
        f"https://sqladmin.googleapis.com/sql/v1beta4/projects/{project}/operations/"
        f"{operation['name']}"
    )
    for _ in range(90):
        result = request(session, "GET", operation_url)
        if result.get("status") == "DONE":
            if result.get("error"):
                raise RuntimeError("Cloud SQL user creation failed")
            break
        time.sleep(2)
    else:
        raise RuntimeError("Timed out waiting for Cloud SQL user creation")

    socket = quote(f"/cloudsql/{project}:{region}:{instance}", safe="")
    url = f"postgresql://{user}:{quote(password, safe='')}@/{database}?host={socket}"
    payload = base64.b64encode(url.encode("utf-8")).decode("ascii")
    version = request(session, "POST", f"{vault}:addVersion", body={"payload": {"data": payload}})
    print(
        f"Created demo SQL user and database secret version {version['name'].rsplit('/', 1)[-1]}."
    )


if __name__ == "__main__":
    main()
