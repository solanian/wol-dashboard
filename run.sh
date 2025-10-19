#!/bin/bash
docker run -d --name wol-dashboard -p 8501:8501 \
  -v $(pwd)/devices.yaml:/app/devices.yaml \
  sorld0603/wol-dashboard:latest
