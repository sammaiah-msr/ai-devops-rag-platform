# Kubernetes ImagePullBackOff Troubleshooting

ImagePullBackOff means Kubernetes is unable to pull the required container image.

## Common Causes

- Incorrect image name
- Incorrect image tag
- Image does not exist
- Private registry authentication failure
- Missing imagePullSecrets
- Registry unavailable
- DNS or network connectivity issue
- Registry rate limiting

## Troubleshooting Commands

Check pod status:

kubectl get pods

Describe the pod:

kubectl describe pod <pod-name>

Check pod events:

kubectl get events --sort-by=.metadata.creationTimestamp

Check configured image:

kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].image}'

Check pod YAML:

kubectl get pod <pod-name> -o yaml

## Private Registry Checks

Check whether imagePullSecrets are configured:

kubectl get pod <pod-name> -o yaml

Look for:

imagePullSecrets:

Check available secrets:

kubectl get secrets

Inspect a registry secret:

kubectl describe secret <secret-name>

## Recommended Troubleshooting Order

1. Check pod events
2. Verify image repository
3. Verify image tag
4. Verify registry availability
5. Verify imagePullSecrets
6. Verify registry credentials
7. Verify DNS and network connectivity