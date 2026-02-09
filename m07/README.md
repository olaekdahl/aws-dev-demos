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
python3 m07/run.py

# Run a specific demo
python3 m07/run.py --demo leaderboard
python3 m07/run.py --demo conditional

# Clean up created tables
python3 m07/run.py --cleanup
```

## AWS Services

- **DynamoDB** -- CreateTable, PutItem, GetItem, Query, UpdateItem (conditional), TransactWriteItems, DeleteTable
