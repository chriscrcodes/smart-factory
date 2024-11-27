#!/bin/bash

# Update apt repository
echo "--- Updating apt repository..."
sudo apt update

# Install prerequisites
echo "--- Installing prerequisites..."
sudo apt install curl -y
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az extension add --upgrade --name connectedk8s
az extension add --upgrade --name azure-iot-ops

# Install K3s
echo "--- Installing K3s..."
curl -sfL https://get.k3s.io | K3S_KUBECONFIG_MODE="644" INSTALL_K3S_EXEC="server --disable traefik" sh -

# Configure K3s
echo "--- Configuring K3s..."
mkdir ~/.kube
sudo KUBECONFIG=~/.kube/config:/etc/rancher/k3s/k3s.yaml kubectl config view --flatten > ~/.kube/merged
mv ~/.kube/merged ~/.kube/config
chmod  0600 ~/.kube/config
export KUBECONFIG=~/.kube/config
kubectl config use-context default
echo fs.inotify.max_user_instances=8192 | sudo tee -a /etc/sysctl.conf
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
echo fs.file-max = 100000 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Check Azure IoT Operations prerequisites
echo "--- Checking Azure IoT Operations prerequisites..."
az iot ops check

echo "--- Ready for Part 3: Connect Edge."