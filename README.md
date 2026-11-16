# GitOps Release Pipeline

A Kubernetes release and rollback demo for a small Python HTTP API. GitHub Actions builds a Docker image, checks `/health`, and publishes the image to GitHub Container Registry (GHCR) with the source commit SHA as its tag. Argo CD watches `k8s/` on `main` and deploys the image declared in `k8s/deployment.yaml`.

## How a release works

1. Push a change to `app.py`, `Dockerfile`, or the publish workflow on `main`. GitHub Actions builds and smoke-tests the image before publishing it to GHCR.
2. Copy the image reference from the Actions run summary into [`k8s/deployment.yaml`](k8s/deployment.yaml). Commit and push this change separately so it can be reverted on its own.
3. Argo CD syncs the Deployment. Kubernetes uses `/health` as a readiness probe, and `/version` shows which API version is running.

## Run the demo on Docker Desktop

Prerequisites are Git, Docker Desktop with Kubernetes enabled, and `kubectl`. Commands below use PowerShell and the `docker-desktop` context.

```powershell
git clone https://github.com/mixsupasek/gitops-release-pipeline.git
cd gitops-release-pipeline
kubectl --context docker-desktop get nodes
```

On a fresh cluster, install Argo CD and wait for its repo server and application controller to become ready. [Argo CD installation guide](https://argo-cd.readthedocs.io/en/stable/getting_started/#1-install-argo-cd)

```powershell
kubectl --context docker-desktop create namespace argocd
kubectl --context docker-desktop apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl --context docker-desktop -n argocd rollout status deployment/argocd-repo-server --timeout=180s
kubectl --context docker-desktop -n argocd rollout status statefulset/argocd-application-controller --timeout=180s
```

Apply the [Argo CD Application](argocd-app.yaml) and wait for `Synced` and `Healthy`. Press `Ctrl+C` to exit the watch.

```powershell
kubectl --context docker-desktop apply -f argocd-app.yaml
kubectl --context docker-desktop -n argocd get application release-api -w
```

Keep the port-forward running in one PowerShell window.

```powershell
kubectl --context docker-desktop -n default port-forward deployment/release-api 18081:8080
```

From a second window, check the API. With the rollback commit `6aa8a63` deployed, `/health` returns `ok` and `/version` returns `v1`.

```powershell
Invoke-RestMethod http://127.0.0.1:18081/health
Invoke-RestMethod http://127.0.0.1:18081/version
```

## Deploy and roll back a version

To try the full release flow, fork this repository, enable Actions for the fork, and update `spec.source.repoURL` in `argocd-app.yaml` to point to it. Apply the updated Application to your cluster. Set `VERSION` in `app.py` to the version you want to ship and push to `main`. After the workflow succeeds, make the fork's GHCR package public so the cluster can pull it, then commit the published image reference in `k8s/deployment.yaml`.

To roll back, run `git revert --no-edit <deployment-commit-sha>` with the SHA of the commit that changed only the image reference, then run `git push`. The revert restores the previous image, which already contains the earlier API code.

Check that Argo CD reports `Synced` and `Healthy` for the rollback commit. Restart port-forwarding after the Pod is replaced, then call `/version` to verify the rollback. If Argo CD still shows the previous Git revision, request a refresh. [Argo CD refresh annotation](https://argo-cd.readthedocs.io/en/stable/user-guide/annotations-and-labels/#argocdargoprojio-refresh)

```powershell
kubectl --context docker-desktop -n argocd annotate application release-api argocd.argoproj.io/refresh=hard --overwrite
kubectl --context docker-desktop -n argocd get application release-api -w -o 'custom-columns=SYNC:.status.sync.status,HEALTH:.status.health.status,REVISION:.status.sync.revision'
```

## Verified release and rollback

| Step | Evidence | `/version` |
| --- | --- | --- |
| Deploy the first GHCR image | [Successful v1 build](https://github.com/mixsupasek/gitops-release-pipeline/actions/runs/43882592573) · [Deployment commit](https://github.com/mixsupasek/gitops-release-pipeline/commit/05f3a923cef8f356dd08108ca0b20c0487df0615) | `v1` |
| Release v2 | [Successful v2 build](https://github.com/mixsupasek/gitops-release-pipeline/actions/runs/43887848453) · [Deployment commit](https://github.com/mixsupasek/gitops-release-pipeline/commit/148c698fae21906cd48bd1fb270fcf38ace68f10) | `v2` |
| Roll back via Git revert | [Rollback commit](https://github.com/mixsupasek/gitops-release-pipeline/commit/6aa8a635164196ca6f53ed5cad2052ad9b2c03f2) | `v1` |
