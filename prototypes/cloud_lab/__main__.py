"""Cloud-only lab entrypoint; never starts the unified local job composition."""
import os
import uvicorn


def main():
    uvicorn.run(
        "prototypes.cloud_lab.runtime:create_app", factory=True,
        host="0.0.0.0", port=int(os.environ.get("PORT", "8080")),
        workers=1, access_log=False, ws_max_size=1_000_000,
    )


if __name__ == "__main__":
    main()
