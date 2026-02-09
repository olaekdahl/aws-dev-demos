# m04 - IAM

Create and assume IAM roles, investigate AccessDenied errors, and simulate permissions with the IAM policy simulator.

## Demos

| Name | Description |
|------|-------------|
| `assume-role` | Creates a temporary IAM role, assumes it, shows before/after identity diff |
| `detective` | Tests real API calls and displays a colored ALLOWED/DENIED matrix |
| `policy-simulator` | Uses IAM SimulatePrincipalPolicy to test a matrix of actions |

## Usage

```bash
# Run all demos
python3 m04/run.py

# Run a specific demo
python3 m04/run.py --demo assume-role
python3 m04/run.py --demo detective
python3 m04/run.py --demo policy-simulator

# Use an existing role instead of creating one
python3 m04/run.py --demo assume-role --role-arn arn:aws:iam::123456789012:role/MyRole

# Clean up created IAM roles
python3 m04/run.py --cleanup
```

## AWS Services

- **IAM** -- CreateRole, AttachRolePolicy, DeleteRole, SimulatePrincipalPolicy
- **STS** -- AssumeRole, GetCallerIdentity
