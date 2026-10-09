#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../data/raw"
fetch() {
  local name=$1 url=$2 sha=$3
  curl -sS -L --retry 5 --retry-delay 10 -C - -o "$name" "$url"
  echo "$sha  $name" | sha256sum -c -
}
fetch vis_images_2012_2019.zip https://osf.io/download/680c1f2496c47f60b139a6e5/ f2bd02834f0dd60795ae682a58894c4333c2de6e59709cb076ff3f8a96fe67bb &
fetch vis_images_2020_2022.zip https://osf.io/download/680c1f36eab635b90e35fdc6/ 41ee371acbf23ad59a8c5e5be3dde72a397c272e9d7c3874792b0dca4fb340c6 &
fetch vis_images_2023_2025.zip https://osf.io/download/u35da/ 4feeffa02b41aa98e3cb9d9b57888c63f68a1c7128fc10b93102d5d9b72b237b &
wait
