#!/usr/bin/env python3
"""Writes cases.json: container image reference strings in six groups."""
import json
H = "0123456789abcdef" * 4                     # 64 hex characters
D = "sha256:" + H
C = [
 # B basic names and Docker Hub normalisation
 ("B01", "ubuntu"), ("B02", "ubuntu:22.04"), ("B03", "library/ubuntu"), ("B04", "docker.io/library/ubuntu:22.04"),
 ("B05", "docker.io/ubuntu"), ("B06", "index.docker.io/library/ubuntu"), ("B07", "user/app"), ("B08", "user/app:v1"),
 ("B09", "ghcr.io/owner/repo:tag"), ("B10", "quay.io/org/repo"), ("B11", "registry.example.com/a/b/c:1"), ("B12", "registry-1.docker.io/library/ubuntu"),
 # H registry host detection
 ("H01", "localhost/app"), ("H02", "localhost:5000/app"), ("H03", "localhost:5000/app:1.0"), ("H04", "myregistry:5000/app"),
 ("H05", "127.0.0.1:5000/app"), ("H06", "[::1]:5000/app"), ("H07", "example.com/app"), ("H08", "example/app"),
 ("H09", "my-host/app"), ("H10", "sub.example.com:443/a:tag"), ("H11", "Example.com/app"), ("H12", "localhost"),
 ("H13", "localhost:5000"), ("H14", "registry:5000/a/b:t"), ("H15", "[2001:db8::1]/app"), ("H16", "example.com:/app"),
 # D digests
 ("D01", "app@" + D), ("D02", "app:tag@" + D), ("D03", "ghcr.io/o/r@" + D), ("D04", "app@sha256:abc"),
 ("D05", "app@sha512:" + H + H), ("D06", "app@md5:" + H[:32]), ("D07", "app@sha256:" + H.upper()), ("D08", "app@" + D + "x"),
 ("D09", "localhost:5000/app@" + D), ("D10", "app@"), ("D11", "app@sha256:" + H + "@" + D), ("D12", "app@foo+bar:" + H),
 # T tags
 ("T01", "app:1.2.3-rc_1"), ("T02", "app:.hidden"), ("T03", "app:-dash"), ("T04", "app:" + "a" * 128), ("T05", "app:" + "a" * 129),
 ("T06", "app:Latest"), ("T07", "app:"), ("T08", "app:1:2"), ("T09", "app:_x"), ("T10", "app:v1.0/x"),
 # N repository names
 ("N01", "Ubuntu"), ("N02", "user/App"), ("N03", "a__b"), ("N04", "a___b"), ("N05", "a..b"), ("N06", "a.-b"), ("N07", "-a/b"),
 ("N08", "a/b/"), ("N09", "a//b"), ("N10", "/a/b"), ("N11", "a" * 256), ("N12", "café"), ("N13", "a b"), ("N14", ""),
 ("N15", "a-b_c.d/e--f"), ("N16", "a/" + "/".join(["b"] * 10)), ("N17", "a_b"), ("N18", "a--b"), ("N19", "ubuntu "), ("N20", "a__"),
 # L practical references
 ("L01", "nginx:1.27-alpine"), ("L02", "postgres:16"), ("L03", "mcr.microsoft.com/dotnet/sdk:8.0"),
 ("L04", "gcr.io/distroless/static-debian12:nonroot"), ("L05", "public.ecr.aws/lambda/python:3.12"),
 ("L06", "registry.k8s.io/pause:3.9"), ("L07", "ghcr.io/home-assistant/home-assistant:stable"), ("L08", "docker.io/bitnami/redis:7.2"),
 ("L09", "quay.io/prometheus/node-exporter:v1.8.2"), ("L10", "redis@" + D),
]
GROUP = dict(B="basic and Docker Hub", H="registry host", D="digests", T="tags", N="repository names", L="practical")
json.dump([dict(id=i, s=s, group=GROUP[i[0]]) for i, s in C], open("cases.json", "w"), indent=1, ensure_ascii=False)
print(len(C), "cases")
