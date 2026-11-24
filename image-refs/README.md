# image-refs

Supports the Pubroot draft "One Image Name, Seven Readings: Container Image Reference Parsers Checked Against
distribution/reference" (batch 9, 2026-11-24).

80 image reference strings (`cases.json`, written by `gen_cases.py`) are parsed by distribution/reference
(`ParseNormalizedNamed` + `TagNameOnly`, the code Docker and containerd use for familiar names; the reference) and by
seven libraries:

- Go: go-containerregistry `name.ParseReference` (default options)
- Python: docker-image-py `Reference.parse_normalized_named`; docker (docker-py) `utils.parse_repository_tag` +
  `auth.resolve_repository_name`, the path its `images.pull()` takes for a string
- Node: @swimlane/docker-reference `parseFamiliarName`, docker-parse-image, parse-docker-image-name
- Rust: oci-spec `distribution::Reference` (also re-exported by oci-client as `oci_client::Reference`)

Each result is reduced to (registry, repository, tag, digest), and Docker's documented defaults are applied to every
result alike (`common.py`): no registry means docker.io, index.docker.io is docker.io, a one-component Docker Hub name
gets `library/`, and no tag and no digest means tag `latest`. Classes: A same as the reference, W different, R library
error where the reference parses, L library parses a string the reference rejects. Groups: B Docker Hub forms, H
registry hosts, D digests, T tags, N repository names, L practical. N15 is open (the reference returns an empty
registry). container_image_dist_ref was tried and left out: it mirrors `reference.Parse`, which does not apply
Docker's familiar-name rules, so every Docker Hub user name would count against it.

Reproduce (Node 24, Python 3.13, Go 1.27, Rust 1.85):

    python3 -m venv .venv && .venv/bin/pip install -r py/requirements.txt
    cd js && npm ci && cd ..
    PY=.venv/bin/python ./run_all.sh

Outputs: `results/refs.json`, `results/summary.json`, `results/report.txt` (full per-case matrix),
`results/realworld.{json,txt}`, `results/versions.txt`. No network, no keys. Cost: $0.

`realworld/image_refs.json` holds every `image:` value in the YAML files of six public repositories at pinned commits
(docker/awesome-compose, kubernetes/examples, argoproj/argo-workflows, GoogleCloudPlatform/kubernetes-engine-samples,
GoogleCloudPlatform/microservices-demo, tektoncd/catalog), made by `realworld/fetch_refs.py` on 2026-11-24.
