#!/bin/bash
# Blue/Green Deployment Script for FlipSync API

set -e

# Configuration
NAMESPACE="flipsync-prod"
DEPLOYMENT_BLUE="flipsync-api-blue"
DEPLOYMENT_GREEN="flipsync-api-green"
SERVICE="flipsync-api"

# Function to display usage
usage() {
  echo "Usage: $0 [deploy|rollback|status]"
  echo "  deploy   - Deploy new version to green environment and switch traffic"
  echo "  rollback - Roll back to blue environment"
  echo "  status   - Show current deployment status"
  exit 1
}

# Function to check deployment status
check_status() {
  echo "Current Deployment Status:"
  echo "-------------------------"

  # Check which version the service is pointing to
  CURRENT_VERSION=$(kubectl -n $NAMESPACE get service $SERVICE -o jsonpath='{.spec.selector.version}')
  echo "Service is currently pointing to: $CURRENT_VERSION"

  # Get replica counts
  BLUE_REPLICAS=$(kubectl -n $NAMESPACE get deployment $DEPLOYMENT_BLUE -o jsonpath='{.spec.replicas}')
  GREEN_REPLICAS=$(kubectl -n $NAMESPACE get deployment $DEPLOYMENT_GREEN -o jsonpath='{.spec.replicas}')

  echo "Blue deployment ($DEPLOYMENT_BLUE) replicas: $BLUE_REPLICAS"
  echo "Green deployment ($DEPLOYMENT_GREEN) replicas: $GREEN_REPLICAS"

  # Get deployment images
  BLUE_IMAGE=$(kubectl -n $NAMESPACE get deployment $DEPLOYMENT_BLUE -o jsonpath='{.spec.template.spec.containers[0].image}')
  GREEN_IMAGE=$(kubectl -n $NAMESPACE get deployment $DEPLOYMENT_GREEN -o jsonpath='{.spec.template.spec.containers[0].image}')

  echo "Blue deployment image: $BLUE_IMAGE"
  echo "Green deployment image: $GREEN_IMAGE"
}

# Function to deploy new version
deploy() {
  echo "Starting blue/green deployment..."

  # Update green deployment with new image
  echo "Updating green deployment with latest image..."
  kubectl -n $NAMESPACE set image deployment/$DEPLOYMENT_GREEN api=flipsync/api:latest

  # Scale up green deployment
  echo "Scaling up green deployment..."
  kubectl -n $NAMESPACE scale deployment $DEPLOYMENT_GREEN --replicas=3

  # Wait for green deployment to be ready
  echo "Waiting for green deployment to be ready..."
  kubectl -n $NAMESPACE rollout status deployment/$DEPLOYMENT_GREEN --timeout=300s

  # Switch service to green deployment
  echo "Switching service to green deployment..."
  kubectl -n $NAMESPACE patch service $SERVICE -p '{"spec":{"selector":{"version":"green"}}}'

  # Wait for a minute to ensure traffic is flowing to green
  echo "Waiting for traffic to stabilize..."
  sleep 60

  # Scale down blue deployment
  echo "Scaling down blue deployment..."
  kubectl -n $NAMESPACE scale deployment $DEPLOYMENT_BLUE --replicas=1

  echo "Deployment completed successfully!"
  check_status
}

# Function to rollback to previous version
rollback() {
  echo "Starting rollback to blue deployment..."

  # Scale up blue deployment
  echo "Scaling up blue deployment..."
  kubectl -n $NAMESPACE scale deployment $DEPLOYMENT_BLUE --replicas=3

  # Wait for blue deployment to be ready
  echo "Waiting for blue deployment to be ready..."
  kubectl -n $NAMESPACE rollout status deployment/$DEPLOYMENT_BLUE --timeout=300s

  # Switch service to blue deployment
  echo "Switching service to blue deployment..."
  kubectl -n $NAMESPACE patch service $SERVICE -p '{"spec":{"selector":{"version":"blue"}}}'

  # Wait for a minute to ensure traffic is flowing to blue
  echo "Waiting for traffic to stabilize..."
  sleep 60

  # Scale down green deployment
  echo "Scaling down green deployment..."
  kubectl -n $NAMESPACE scale deployment $DEPLOYMENT_GREEN --replicas=0

  echo "Rollback completed successfully!"
  check_status
}

# Main script logic
case "$1" in
  deploy)
    deploy
    ;;
  rollback)
    rollback
    ;;
  status)
    check_status
    ;;
  *)
    usage
    ;;
esac
