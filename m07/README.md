# m07 - DynamoDB CRUD

Gaming leaderboard with queries, transactions, and conditional writes demonstrating optimistic locking.

## Demos

| Name | Description |
|------|-------------|
| `leaderboard` | Seeds player scores across games, demonstrates GetItem, Query (sorted), filters, conditional UpdateItem, and TransactWriteItems |
| `conditional` | Simulates two concurrent writers with ConditionExpression to demonstrate conflict detection |

## Usage

```bash
# Run all demos
python m07/run.py

# Run a specific demo
python m07/run.py --demo leaderboard
python m07/run.py --demo conditional

# Clean up created tables
python m07/run.py --cleanup
```

## AWS Services

- **DynamoDB** -- CreateTable, PutItem, GetItem, Query, UpdateItem (conditional), TransactWriteItems, DeleteTable
