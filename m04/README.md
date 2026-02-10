# m04 - IAM

Create and assume IAM roles, investigate AccessDenied errors, and simulate permissions with the IAM policy simulator.

## Demos

| Name | Description |
|------|-------------|
| `assume-role` | Creates a temporary IAM role, assumes it, shows before/after identity diff |
| `detective` | Tests real API calls and displays a colored ALLOWED/DENIED matrix |
| `policy-simulator` | Uses IAM SimulatePrincipalPolicy to test a matrix of actions |

## Usage

Run all demos:
```bash
python3 m04/run.py
```

Run a specific demo:
```bash
python3 m04/run.py --demo assume-role
```
```bash
python3 m04/run.py --demo detective
```
```bash
python3 m04/run.py --demo policy-simulator
```

Use an existing role instead of creating one:
```bash
python3 m04/run.py --demo assume-role --role-arn arn:aws:iam::123456789012:role/MyRole
```

Clean up created IAM roles:
```bash
python3 m04/run.py --cleanup
```

## AWS Services

- **IAM** -- CreateRole, AttachRolePolicy, DeleteRole, SimulatePrincipalPolicy
- **STS** -- AssumeRole, GetCallerIdentity
