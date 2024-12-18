# Uninstall Procedure

## 1-Edge Part
  - From the Edge Cluster, execute the following command:
    ```bash
    curl -O https://raw.githubusercontent.com/chriscrcodes/talk-to-your-factory/main/artifacts/templates/deploy/4_edge-unprovision.yaml
    ansible-playbook 4_edge-unprovision.yaml
    ```
    ![edge-uninstall](./artifacts/media/edge-uninstall.png "edge-uninstall")
## 2-Cloud Part
  - From Azure Portal > Azure Cloud Shell, upload the files `variables.yaml` (from your Edge Cluster) and [`5_cloud-unprovision.yaml`](./artifacts/templates/deploy/5_cloud-unprovision.yaml) via `Manage files` > `Upload`.
  - Execute the following command:
    ```bash
    ansible-playbook 5_cloud-unprovision.yaml
    ```
    ![cloud-uninstall](./artifacts/media/cloud-uninstall.png "cloud-uninstall")