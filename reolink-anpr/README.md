# Reolink ANPR — standalone vehicle capture & search (Raspberry Pi)

Watches multiple Reolink cameras over your LAN, detects vehicles, reads
license plates, estimates each vehicle's colour, and stores a searchable
record with snapshots — plate, colour, camera, and time-range search via a
small local web dashboard. Everything runs on-device: no cloud account, no
vendor API, no internet dependency at runtime. The only network traffic is
RTSP from your cameras to the Pi, and the dashboard served on your LAN.

Built and tuned for: **Raspberry Pi 4 (4-8GB), 3-4 cameras, moderate
traffic.**

## How it works

- One `capture_worker.py` process per camera pulls its RTSP stream and runs
  cheap frame-difference motion detection at a low sample rate (default
  every 0.5s). Full detection only runs when motion is seen, which is what
  makes 3-4 simultaneous streams workable on a Pi 4 CPU.
- On motion: YOLOv8n (nano weights) finds vehicle bounding boxes, each crop
  is run through `fast-alpr` for plate detection + OCR, and a small
  k-means-based colour estimate is computed from the vehicle body.
- Every vehicle found is written to `captures.db` (SQLite) plus full-frame,
  vehicle-crop, and plate-crop JPEGs under `captures/<date>/<camera>/`.
- `dashboard/app.py` (FastAPI) serves a search page on your LAN — filter by
  plate substring, colour, camera, or a date/time range.
- `cleanup.py`, run daily via a systemd timer, deletes captures (files +
  DB rows) older than `storage.retention_days` in `config.yaml`.

## Requirements

- Raspberry Pi 4 (4GB+ recommended), Raspberry Pi OS (64-bit) Bookworm or
  newer.
- Python 3.11+, `ffmpeg`, and BLAS libs for numpy/onnxruntime on ARM:

  ```bash
  sudo apt update
  sudo apt install -y python3-venv python3-pip ffmpeg libatlas-base-dev libopenblas-dev
  ```

- Each Reolink camera reachable on your LAN with a known IP, RTSP enabled
  (on by default), and a local admin/user account for the stream
  credentials (Reolink app/web UI → Settings → Network → Advanced →
  Server Settings). Using each camera's **sub stream**
  (`h264Preview_01_sub` instead of `_main`) trades resolution for much
  lower decode cost — worth it if the Pi struggles to keep up with 3-4
  main streams.

## Setup

```bash
cd /home/pi
git clone <this-repo-or-copy-the-reolink-anpr-folder> reolink-anpr
cd reolink-anpr
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Edit `config.yaml`:
- Fill in each camera's `name` and `rtsp_url` (host, credentials, and
  main/sub stream path).
- Adjust `capture.sample_interval_sec` / `motion_threshold` if you're
  getting missed vehicles (lower threshold) or too many false triggers
  from things like blowing trees (raise threshold, or mask that area out
  of frame in the camera's own motion-zone settings).
- Set `storage.retention_days` to whatever your SD card/USB storage can
  hold — each vehicle event is roughly a few hundred KB across its three
  images.

First run (models download once and are cached under `~/.cache`):

```bash
python capture_worker.py --camera cam1   # test one camera in the foreground first
```

Once each camera is confirmed working, install as services:

```bash
sudo cp systemd/*.service systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload

# one instance per camera name from config.yaml
sudo systemctl enable --now anpr-capture@cam1
sudo systemctl enable --now anpr-capture@cam2
sudo systemctl enable --now anpr-capture@cam3
sudo systemctl enable --now anpr-capture@cam4

sudo systemctl enable --now anpr-dashboard
sudo systemctl enable --now anpr-cleanup.timer
```

Check logs with `journalctl -u anpr-capture@cam1 -f`.

The systemd unit files assume the project lives at `/home/pi/reolink-anpr`
and runs as user `pi` — edit `WorkingDirectory`/`ExecStart`/`User` in the
`.service` files if your setup differs, then `daemon-reload` again.

## Using the dashboard

Open `http://<pi-ip>:8080` from any device on your LAN. Filter by plate
(partial match), colour, camera, or a date/time range; click a result for
the full-frame, vehicle, and plate images plus OCR confidence. This is
LAN-only by design — don't port-forward it to the internet.

## Performance notes / tuning for a Pi 4

- 3-4 cameras at continuous full-frame detection will overload a Pi 4 —
  that's why detection is motion-gated rather than running on every frame.
  If you still see the Pi struggling: increase `sample_interval_sec`,
  switch cameras to their sub-stream, or reduce `detect_max_dim`.
- YOLOv8n and fast-alpr's default models are both intentionally the
  smallest/fastest variants available for this reason. Bigger models
  (`yolov8s`+, larger fast-alpr detector/OCR pairs) will be more accurate
  but may not keep up in real time with several concurrent cameras.
- If your traffic volume grows beyond "moderate" (busy road, not a
  driveway), consider offloading detection to a beefier device (Pi 5, or a
  small local box with a Coral/USB accelerator) — the capture workers,
  storage layer, and dashboard here don't change, only where
  `detector.py`'s models run.

## What "no APIs" means here

Reolink cameras are addressed over the LAN via standard RTSP — the same
local video protocol any NVR software uses — so there's no camera-vendor
cloud account or API key involved. YOLOv8n and fast-alpr run their models
fully on-device (downloaded once, cached locally, no calls at inference
time). Nothing in this project talks to the internet after initial model
download.

## Limitations to know about

- Plate OCR accuracy depends heavily on camera angle, lighting, and plate
  format — expect some misreads, especially at night or oblique angles.
  Consider aiming at least one camera for a more head-on plate view if
  read-rate matters.
- Colour estimation is a simple dominant-colour heuristic, not a trained
  classifier — it's a reasonable searchable approximation, not
  forensic-grade.
- This was designed and reviewed for a Pi 4 + 3-4-camera, moderate-traffic
  setup as described by the requester; it hasn't been load-tested against
  real Reolink hardware in this environment. Validate detection rate and
  Pi CPU headroom against your actual cameras/traffic and tune the
  `capture` settings in `config.yaml` accordingly.
