# Kubernetes OOMKilled Troubleshooting

OOMKilled means the container exceeded the memory available to it and was terminated by the operating system or Kubernetes.

## Common Indicators

Typical signs include:

Reason: OOMKilled

Exit Code: 137

## Troubleshooting Commands

Describe the pod:

kubectl describe pod <pod-name>

Check previous container logs:

kubectl logs <pod-name> --previous

Check resource configuration:

kubectl get pod <pod-name> -o yaml

Look for:

resources:
  requests:
    memory:
  limits:
    memory:

Check current pod memory usage:

kubectl top pod <pod-name>

Check node utilization:

kubectl top nodes

## Common Causes

- Container memory limit is too low
- Application memory leak
- JVM heap too large
- Large in-memory cache
- High concurrency
- Large request payloads
- Unexpected workload growth
- Memory request/limit not properly configured

## Recommended Troubleshooting Order

1. Confirm OOMKilled in pod status
2. Check exit code
3. Check pod memory limit
4. Check actual memory usage
5. Review application logs
6. Check application heap configuration
7. Check for memory leaks
8. Increase memory only when justified

## Possible Remediation

- Correct application memory leaks
- Tune JVM or application heap
- Reduce cache size
- Reduce concurrency
- Increase memory limit when appropriate
- Configure proper memory requests
- Add memory monitoring and alerts