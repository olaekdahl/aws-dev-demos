"""
Demo: DynamoDB Gaming Leaderboard - CRUD, Queries, Transactions

Creates a DynamoDB table modelling a gaming leaderboard with composite keys,
seeds it with player scores across multiple games, then demonstrates GetItem,
Query (sorted leaderboard), FilterExpression, conditional UpdateItem, and
TransactWriteItems (atomic bonus-point transfer).
"""
import time
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    table, generate_name, track_resource, progress_bar,
)

# ── Seed data ──────────────────────────────────────────────────────

GAMES = ["space-invaders", "pac-man", "tetris"]

PLAYERS = {
    "Ada":       "Ada Lovelace",
    "Linus":     "Linus Torvalds",
    "Grace":     "Grace Hopper",
    "Alan":      "Alan Turing",
    "Margaret":  "Margaret Hamilton",
    "Dijkstra":  "Edsger Dijkstra",
    "Knuth":     "Donald Knuth",
}

# (game, player, score)
SCORES = [
    # space-invaders
    ("space-invaders", "Ada",       9500),
    ("space-invaders", "Linus",     8700),
    ("space-invaders", "Grace",    12300),
    ("space-invaders", "Alan",      7400),
    ("space-invaders", "Margaret", 11000),
    ("space-invaders", "Dijkstra",  6800),
    ("space-invaders", "Knuth",    10200),
    # pac-man
    ("pac-man", "Ada",       15600),
    ("pac-man", "Linus",     13200),
    ("pac-man", "Grace",     17800),
    ("pac-man", "Alan",      14100),
    ("pac-man", "Margaret",  16500),
    ("pac-man", "Dijkstra",  11900),
    ("pac-man", "Knuth",     18200),
    # tetris
    ("tetris", "Ada",       245000),
    ("tetris", "Linus",     312000),
    ("tetris", "Grace",     198000),
    ("tetris", "Alan",      287000),
    ("tetris", "Margaret",  330000),
    ("tetris", "Dijkstra",  275000),
    ("tetris", "Knuth",     301000),
]


def _pad_score(score: int, width: int = 10) -> str:
    """Zero-pad a score so lexicographic sort matches numeric sort."""
    return str(score).zfill(width)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _wait_for_table(ddb, table_name: str, timeout: int = 60):
    """Poll until the table becomes ACTIVE."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = ddb.describe_table(TableName=table_name)["Table"]["TableStatus"]
        if status == "ACTIVE":
            return
        time.sleep(2)
    raise TimeoutError(f"Table {table_name} did not become ACTIVE within {timeout}s")


def run(args):
    banner("m07", "Gaming Leaderboard - DynamoDB CRUD")

    session = create_session(args.profile, args.region)
    ddb = session.client("dynamodb")

    table_name = generate_name("leaderboard", getattr(args, "prefix", None))

    # ── Step 1: Create the table ──────────────────────────────────
    step(1, "Create DynamoDB table with composite key (PK + SK)")
    kv("Table", table_name)
    kv("PK", "PK (String) - e.g. GAME#space-invaders or PLAYER#Ada")
    kv("SK", "SK (String) - e.g. SCORE#0000009500#Ada or PROFILE")

    try:
        ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        info("Waiting for table to become ACTIVE...")
        _wait_for_table(ddb, table_name)
        success(f"Table '{table_name}' is ACTIVE")
    except ClientError as exc:
        fail(f"Could not create table: {exc}")
        return

    track_resource("m07", "dynamodb_table", table_name)

    # ── Step 2: Seed data ─────────────────────────────────────────
    step(2, "Seed table with player profiles and 21 scores across 3 games")

    items_written = 0
    total_items = len(PLAYERS) + len(SCORES)

    # Player profiles
    for short_name, full_name in PLAYERS.items():
        try:
            ddb.put_item(
                TableName=table_name,
                Item={
                    "PK":     {"S": f"PLAYER#{short_name}"},
                    "SK":     {"S": "PROFILE"},
                    "name":   {"S": full_name},
                    "joined": {"S": _now_iso()},
                },
            )
            items_written += 1
            progress_bar(items_written, total_items, label="seeding")
        except ClientError as exc:
            fail(f"Failed to write profile for {short_name}: {exc}")
            return

    # Game scores
    for game, player, score in SCORES:
        padded = _pad_score(score)
        try:
            ddb.put_item(
                TableName=table_name,
                Item={
                    "PK":        {"S": f"GAME#{game}"},
                    "SK":        {"S": f"SCORE#{padded}#{player}"},
                    "player":    {"S": player},
                    "score":     {"N": str(score)},
                    "played_at": {"S": _now_iso()},
                },
            )
            items_written += 1
            progress_bar(items_written, total_items, label="seeding")
        except ClientError as exc:
            fail(f"Failed to write score {player}/{game}: {exc}")
            return

    success(f"Wrote {items_written} items ({len(PLAYERS)} profiles + {len(SCORES)} scores)")

    # ── Step 3: GetItem - fetch a single score ────────────────────
    step(3, "GetItem - fetch Grace's space-invaders score")

    target_game = "space-invaders"
    target_player = "Grace"
    target_score = 12300

    try:
        resp = ddb.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"GAME#{target_game}"},
                "SK": {"S": f"SCORE#{_pad_score(target_score)}#{target_player}"},
            },
        )
        item = resp.get("Item")
        if item:
            kv("PK", item["PK"]["S"])
            kv("SK", item["SK"]["S"])
            kv("Player", item["player"]["S"])
            kv("Score", item["score"]["N"])
            kv("Played at", item["played_at"]["S"])
            success("GetItem returned the exact item in a single read")
        else:
            warn("Item not found (unexpected)")
    except ClientError as exc:
        fail(f"GetItem failed: {exc}")

    # ── Step 4: Query - full leaderboard for a game (sorted) ─────
    step(4, "Query - leaderboard for space-invaders (sorted by score)")

    info("Using Query on PK=GAME#space-invaders with SK begins_with SCORE#")
    info("SK is zero-padded so lexicographic order = numeric order\n")

    try:
        resp = ddb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk":     {"S": "GAME#space-invaders"},
                ":prefix": {"S": "SCORE#"},
            },
            ScanIndexForward=False,  # descending = highest score first
        )
        items = resp.get("Items", [])

        rows = []
        for rank, item in enumerate(items, start=1):
            rows.append([
                str(rank),
                item["player"]["S"],
                f"{int(item['score']['N']):,}",
            ])

        table(["Rank", "Player", "Score"], rows, col_width=14)
        success(f"Returned {len(items)} scores in sorted order (descending)")
    except ClientError as exc:
        fail(f"Query failed: {exc}")

    # ── Step 5: Query with FilterExpression ───────────────────────
    step(5, "Query with FilterExpression - pac-man scores above 15,000")

    threshold = 15000

    try:
        resp = ddb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            FilterExpression="score > :threshold",
            ExpressionAttributeValues={
                ":pk":        {"S": "GAME#pac-man"},
                ":prefix":    {"S": "SCORE#"},
                ":threshold": {"N": str(threshold)},
            },
            ScanIndexForward=False,
        )
        items = resp.get("Items", [])

        rows = []
        for item in items:
            rows.append([
                item["player"]["S"],
                f"{int(item['score']['N']):,}",
            ])

        table(["Player", "Score"], rows, col_width=14)
        info(f"FilterExpression removed scores <= {threshold:,} after the query read them")
        success(f"{len(items)} players scored above {threshold:,} in pac-man")
    except ClientError as exc:
        fail(f"Query with filter failed: {exc}")

    # ── Step 6: Conditional UpdateItem ────────────────────────────
    step(6, "Conditional UpdateItem - only update if new score is higher")

    update_game = "space-invaders"
    update_player = "Ada"
    original_score = 9500
    lower_score = 5000
    higher_score = 25000
    padded_original = _pad_score(original_score)

    info(f"Ada's current space-invaders score: {original_score:,}")
    info(f"Attempting to update with a LOWER score ({lower_score:,})...\n")

    try:
        ddb.update_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"GAME#{update_game}"},
                "SK": {"S": f"SCORE#{padded_original}#{update_player}"},
            },
            UpdateExpression="SET score = :new_score",
            ConditionExpression="score < :new_score",
            ExpressionAttributeValues={
                ":new_score": {"N": str(lower_score)},
            },
        )
        warn("Update succeeded unexpectedly")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            success(f"Condition blocked the update - {lower_score:,} < {original_score:,} (correct!)")
        else:
            fail(f"Unexpected error: {exc}")

    info(f"\nAttempting to update with a HIGHER score ({higher_score:,})...")

    # For a higher score we need to delete the old SK and write a new one
    # because the SK contains the zero-padded score.
    new_padded = _pad_score(higher_score)

    try:
        ddb.transact_write_items(
            TransactItems=[
                {
                    "Delete": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": f"GAME#{update_game}"},
                            "SK": {"S": f"SCORE#{padded_original}#{update_player}"},
                        },
                        "ConditionExpression": "score < :new_score",
                        "ExpressionAttributeValues": {
                            ":new_score": {"N": str(higher_score)},
                        },
                    },
                },
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": {
                            "PK":        {"S": f"GAME#{update_game}"},
                            "SK":        {"S": f"SCORE#{new_padded}#{update_player}"},
                            "player":    {"S": update_player},
                            "score":     {"N": str(higher_score)},
                            "played_at": {"S": _now_iso()},
                        },
                    },
                },
            ],
        )
        success(f"Score updated atomically: {original_score:,} -> {higher_score:,}")
    except ClientError as exc:
        fail(f"Conditional update failed: {exc}")

    # Verify by querying the leaderboard again
    info("\nVerifying updated leaderboard for space-invaders:")

    try:
        resp = ddb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk":     {"S": "GAME#space-invaders"},
                ":prefix": {"S": "SCORE#"},
            },
            ScanIndexForward=False,
        )
        items = resp.get("Items", [])
        rows = []
        for rank, item in enumerate(items, start=1):
            player = item["player"]["S"]
            score_val = f"{int(item['score']['N']):,}"
            marker = " << updated!" if player == update_player else ""
            rows.append([str(rank), player, score_val + marker])

        table(["Rank", "Player", "Score"], rows, col_width=20)
    except ClientError as exc:
        fail(f"Verification query failed: {exc}")

    # ── Step 7: TransactWriteItems - atomic bonus point transfer ──
    step(7, "TransactWriteItems - atomic bonus-point transfer between players")

    # Transfer 1000 bonus points from Grace to Alan in tetris
    from_player = "Grace"
    to_player = "Alan"
    bonus = 1000
    from_original = 198000
    to_original = 287000

    info(f"Transferring {bonus:,} bonus points: {from_player} -> {to_player} (tetris)")
    kv(f"{from_player} before", f"{from_original:,}")
    kv(f"{to_player} before", f"{to_original:,}")
    info("")

    from_padded_old = _pad_score(from_original)
    from_padded_new = _pad_score(from_original - bonus)
    to_padded_old = _pad_score(to_original)
    to_padded_new = _pad_score(to_original + bonus)

    try:
        ddb.transact_write_items(
            TransactItems=[
                # Remove Grace's old score entry
                {
                    "Delete": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": "GAME#tetris"},
                            "SK": {"S": f"SCORE#{from_padded_old}#{from_player}"},
                        },
                        "ConditionExpression": "score >= :bonus",
                        "ExpressionAttributeValues": {
                            ":bonus": {"N": str(bonus)},
                        },
                    },
                },
                # Write Grace's new score entry
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": {
                            "PK":        {"S": "GAME#tetris"},
                            "SK":        {"S": f"SCORE#{from_padded_new}#{from_player}"},
                            "player":    {"S": from_player},
                            "score":     {"N": str(from_original - bonus)},
                            "played_at": {"S": _now_iso()},
                        },
                    },
                },
                # Remove Alan's old score entry
                {
                    "Delete": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": "GAME#tetris"},
                            "SK": {"S": f"SCORE#{to_padded_old}#{to_player}"},
                        },
                    },
                },
                # Write Alan's new score entry
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": {
                            "PK":        {"S": "GAME#tetris"},
                            "SK":        {"S": f"SCORE#{to_padded_new}#{to_player}"},
                            "player":    {"S": to_player},
                            "score":     {"N": str(to_original + bonus)},
                            "played_at": {"S": _now_iso()},
                        },
                    },
                },
            ],
        )
        kv(f"{from_player} after", f"{from_original - bonus:,}")
        kv(f"{to_player} after", f"{to_original + bonus:,}")
        success("Atomic transfer complete - both updates succeeded or neither would have")
    except ClientError as exc:
        fail(f"Transaction failed (both writes rolled back): {exc}")

    # Final tetris leaderboard
    info("\nFinal tetris leaderboard after bonus transfer:")

    try:
        resp = ddb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk":     {"S": "GAME#tetris"},
                ":prefix": {"S": "SCORE#"},
            },
            ScanIndexForward=False,
        )
        items = resp.get("Items", [])
        rows = []
        for rank, item in enumerate(items, start=1):
            rows.append([
                str(rank),
                item["player"]["S"],
                f"{int(item['score']['N']):,}",
            ])

        table(["Rank", "Player", "Score"], rows, col_width=14)
    except ClientError as exc:
        fail(f"Final query failed: {exc}")

    success(f"Table '{table_name}' tracked for cleanup (run with --cleanup)")
