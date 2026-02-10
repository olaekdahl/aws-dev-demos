# .NET DynamoDB Demo

Demonstrates DynamoDB operations in C# using the AWS SDK for .NET, comparing the three programming models: Object Persistence, Document Model, and Low-Level API.

## Prerequisites

```bash
# Install .NET 9 SDK
# See: https://dotnet.microsoft.com/download

# Restore NuGet packages
dotnet restore

# Configure AWS credentials
aws configure
```

## Quick Start

Build the project:
```bash
dotnet build
```

Run the demo:
```bash
dotnet run
```

## What This Demonstrates

### Three API Levels

1. **Object Persistence Model** (Highest Level)
   - ORM-like approach with POCO classes
   - Uses `DynamoDBContext` and attributes like `[DynamoDBTable]`, `[DynamoDBHashKey]`
   - Automatic serialization/deserialization
   - Best for: Domain-driven design, clean code

2. **Document Model API** (Medium Level)
   - JSON-like approach using `Document` class
   - Flexible schema, schemaless operations
   - Automatic type conversion
   - Best for: Dynamic schemas, rapid prototyping

3. **Low-Level API** (Lowest Level)
   - Direct access using `PutItemRequest`, `QueryRequest`, etc.
   - Full control over `AttributeValue` dictionaries
   - Required for transactions, batch operations
   - Best for: Performance optimization, advanced features

### Operations Covered

- Creating a DynamoDB table
- Inserting items with complex attributes (lists, maps, nested objects)
- Querying by partition key
- Comparing all three programming models

## Code Structure

```csharp
// ═══════════════════════════════════════════════════════════════════
// 1. Object Persistence Model - ORM-like with POCOs
// ═══════════════════════════════════════════════════════════════════
[DynamoDBTable("Notes")]
public class Note
{
    [DynamoDBHashKey]
    public int UserId { get; set; }

    [DynamoDBRangeKey]
    public long NoteId { get; set; }

    [DynamoDBProperty]
    public string? Content { get; set; }
}

var context = new DynamoDBContext(client);
var note = new Note { UserId = 1, NoteId = 123, Content = "Hello!" };
await context.SaveAsync(note);

// Query returns strongly-typed objects
var notes = await context.QueryAsync<Note>(userId).GetRemainingAsync();

// ═══════════════════════════════════════════════════════════════════
// 2. Document Model API - JSON-like, flexible schema
// ═══════════════════════════════════════════════════════════════════
var table = Table.LoadTable(client, tableName);
var doc = new Document
{
    ["UserId"] = userId,
    ["NoteId"] = noteId,
    ["Content"] = "My note content",
    ["Tags"] = new DynamoDBList { "tag1", "tag2" }
};
await table.PutItemAsync(doc);

// ═══════════════════════════════════════════════════════════════════
// 3. Low-Level API - Full control
// ═══════════════════════════════════════════════════════════════════
var request = new PutItemRequest
{
    TableName = tableName,
    Item = new Dictionary<string, AttributeValue>
    {
        { "UserId", new AttributeValue { N = userId.ToString() } },
        { "Content", new AttributeValue { S = "My note" } }
    }
};
await client.PutItemAsync(request);
```

## Table Schema

```
Table: Notes
├── Partition Key: UserId (Number)
└── Sort Key: NoteId (Number)
```

## Dependencies

- AWSSDK.DynamoDBv2 (NuGet)
- .NET 9.0

## When to Use Each API

| Object Persistence | Document Model | Low-Level API |
|-------------------|----------------|---------------|
| Domain entities | Dynamic schemas | Transactions |
| Clean architecture | Rapid prototyping | Batch operations |
| Type safety | Flexible attributes | Fine-grained control |
| CRUD operations | JSON-like access | Performance tuning |

## Notes

- Update `RegionEndpoint` in code to match your region
- Uncomment `CreateExampleTableLowLevelApi` to create the table
- Table creation takes ~30 seconds
