# m09 - Lambda

Deploy Lambda functions, measure cold starts, and explore error handling patterns.

## Demos

| Name | Description |
|------|-------------|
| `deploy` | Auto-creates IAM role, packages handler, deploys a word frequency analyzer Lambda, invokes it |
| `cold-start` | Deploys a function and invokes it 10x, parses REPORT lines for Init Duration vs Duration |
| `errors` | Deploys a function that throws different error types (timeout, exception), shows how Lambda reports each |

## Usage

```bash
# Run all demos
python3 m09/run.py

# Run a specific demo
python3 m09/run.py --demo deploy
python3 m09/run.py --demo cold-start
python3 m09/run.py --demo errors

# Clean up Lambda functions and IAM roles
python3 m09/run.py --cleanup
```

## SAM App

There's also a SAM-based event source demo:

```bash
cd m09/sam-event-source
sam build --use-container
sam deploy --guided
```

## AWS Services

- **Lambda** -- CreateFunction, Invoke, GetFunctionConfiguration
- **IAM** -- CreateRole, AttachRolePolicy
