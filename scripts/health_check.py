
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


HEALTH_URL = "http://127.0.0.1:8007/health"


def main():
    print("FDS Application Health Check")
    print(f"Checking: {HEALTH_URL}")

    try:
        with urlopen(HEALTH_URL, timeout=10) as response:
            status_code = response.status
            data = json.load(response)

        if status_code == 200 and data.get("status") == "ok":
            print("SUCCESS: FastAPI application is healthy")
            sys.exit(0)

        print(f"FAILED: Unexpected response: {data}")
        sys.exit(1)

    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"FAILED: Application health check error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
