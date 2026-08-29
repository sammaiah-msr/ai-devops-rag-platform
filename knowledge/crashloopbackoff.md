# Kubernetes CrashLoopBackOff Troubleshooting

CrashLoopBackOff occurs when a container repeatedly starts, exits or crashes,
and Kubernetes applies an increasing delay before restarting it again.

## Initial Checks

Check pod status:

kubectl get pods

Describe the pod:

kubectl describe pod <pod-name>

Review events near the bottom of the describe output.

## Check Container Logs

kubectl logs <pod-name>

For a previously crashed container:

kubectl logs <pod-name> --previous

## Common Causes

- Application startup failure
- Missing environment variables
- Missing ConfigMap or Secret
- Invalid application configuration
- Failed database connection
- Failed dependency connection
- Incorrect command or entrypoint
- Liveness probe failure
- Out-of-memory termination
- File permission problems

## Check Container Exit State

kubectl describe pod <pod-name>

Review:

State
Last State
Reason
Exit Code

## Check Resource Limits

kubectl get pod <pod-name> -o yaml

Look for:

resources:
  requests:
  limits:

If the container was terminated because of memory pressure, the reason may
appear as OOMKilled.

## Check Probes

Review liveness, readiness and startup probes.

kubectl describe pod <pod-name>

Incorrect liveness probes may continuously restart an otherwise healthy
application.

## Recommended Troubleshooting Order

1. kubectl get pods
2. kubectl describe pod
3. kubectl logs
4. kubectl logs --previous
5. Review events
6. Review exit codes
7. Check ConfigMaps and Secrets
8. Check resource requests and limits
9. Check probes
10. Validate dependent services