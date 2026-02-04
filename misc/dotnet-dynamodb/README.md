# .NET DynamoDB Demo

Demonstrates DynamoDB operations in C# using the AWS SDK for .NET, comparing the Document Model API versus the Low-Level API.

## Prerequisites

```bash
# Install .NET 8 SDK
# See: https://dotnet.microsoft.com/download

# Restore NuGet packages
dotnet restore

# Configure AWS credentials
aws configure
```

## Quick Start

```bash
# Build the project
dotnet build

# Run the demo
dotnet run
```

## What This Demonstrates

### Two API Styles

1. **Document Model API** (High-Level)
   - Object-oriented approach using `Document` class
   - Automatic type conversion
   - Cleaner syntax for most use cases

2. **Low-Level API**
   - Direct access to DynamoDB operations
   - Full control over request/response
   - Uses `AttributeValue` dictionaries

### Operations Covered

- Creating a DynamoDB table
- Inserting items with complex attributes (lists, maps)
- Querying by partition key
- Waiting for table creation

## Code Structure

```csharp
// Document Model API - cleaner syntax
var table = Table.LoadTable(client, tableName);
var doc = new Document
{
    ["UserId"] = userId,
    ["NoteId"] = noteId,
    ["Note"] = "My note content",
    ["Tags"] = new DynamoDBList { "tag1", "tag2" }
};
await table.PutItemAsync(doc);

// Low-Level API - more control
var request = new PutItemRequest
{
    TableName = tableName,
    Item = new Dictionary<string, AttributeValue>
    {
        { "UserId", new AttributeValue { N = userId.ToString() } },
        { "Note", new AttributeValue { S = "My note" } }
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
- .NET 8.0

## When to Use Each API

| Document Model | Low-Level API |
|---------------|---------------|
| CRUD operations | Complex transactions |
| Rapid development | Batch operations |
| Type safety | Fine-grained control |
| Cleaner code | Performance optimization |

## Notes

- Update `RegionEndpoint` in code to match your region
- Uncomment `CreateExampleTableLowLevelApi` to create the table
- Table creation takes ~30 seconds
