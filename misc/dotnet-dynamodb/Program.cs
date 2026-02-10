using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Amazon;
using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.DynamoDBv2.DocumentModel;
using Amazon.DynamoDBv2.DataModel;

// ═══════════════════════════════════════════════════════════════════════════
// Object Persistence Model - POCO class with DynamoDB attributes
// ═══════════════════════════════════════════════════════════════════════════
[DynamoDBTable("Notes")]
public class Note
{
    [DynamoDBHashKey]
    public int UserId { get; set; }

    [DynamoDBRangeKey]
    public long NoteId { get; set; }

    [DynamoDBProperty]
    public string? Content { get; set; }

    [DynamoDBProperty("Favorite")]
    public bool IsFavorite { get; set; }

    [DynamoDBProperty]
    public List<string>? Tags { get; set; }

    [DynamoDBProperty]
    public NoteMetadata? Metadata { get; set; }
}

public class NoteMetadata
{
    public string? Author { get; set; }
    public string? CreatedDate { get; set; }
}

class Program
{
    static async Task Main(string[] args)
    {
        var config = new AmazonDynamoDBConfig
        {
            RegionEndpoint = RegionEndpoint.USEast1 // Adjust as needed
        };
        var client = new AmazonDynamoDBClient(config);
        var tableName = "Notes";

        Console.WriteLine("═══════════════════════════════════════════════════════════════");
        Console.WriteLine("  .NET DynamoDB - Three Programming Models Comparison");
        Console.WriteLine("═══════════════════════════════════════════════════════════════\n");

        // Ensure table exists
        await EnsureTableExists(client, tableName);

        // ─── Object Persistence Model (Highest Level) ───
        Console.WriteLine("┌─────────────────────────────────────────────────────────────┐");
        Console.WriteLine("│  1. Object Persistence Model (DynamoDBContext)              │");
        Console.WriteLine("└─────────────────────────────────────────────────────────────┘");
        await InsertNoteObjectPersistence(client, userId: 1);
        await QueryNotesByUserIdObjectPersistence(client, userId: 1);

        // ─── Document Model API ───
        Console.WriteLine("\n┌─────────────────────────────────────────────────────────────┐");
        Console.WriteLine("│  2. Document Model API (Table + Document)                   │");
        Console.WriteLine("└─────────────────────────────────────────────────────────────┘");
        await InsertNoteDocumentApi(client, tableName, userId: 1);
        await QueryNotesByUserIdDocumentApi(client, tableName, userId: 1);

        // ─── Low-Level API ───
        Console.WriteLine("\n┌─────────────────────────────────────────────────────────────┐");
        Console.WriteLine("│  3. Low-Level API (PutItemRequest + AttributeValue)         │");
        Console.WriteLine("└─────────────────────────────────────────────────────────────┘");
        await InsertNoteLowLevelApi(client, tableName, userId: 1);
        await QueryNotesByUserIdLowLevelApi(client, tableName, userId: 1);

        // ─── Comparison Summary ───
        Console.WriteLine("\n═══════════════════════════════════════════════════════════════");
        Console.WriteLine("  API Comparison Summary");
        Console.WriteLine("═══════════════════════════════════════════════════════════════");
        Console.WriteLine();
        Console.WriteLine("  Model               Abstraction   Use Case");
        Console.WriteLine("  ────────────────────────────────────────────────────────────");
        Console.WriteLine("  Object Persistence  Highest       CRUD with POCOs, ORM-like");
        Console.WriteLine("  Document Model      Medium        Flexible schema, JSON-like");
        Console.WriteLine("  Low-Level           Lowest        Table mgmt, UpdateItem, PartiQL");
        Console.WriteLine();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Object Persistence Model Functions
    // ═══════════════════════════════════════════════════════════════════════════

    static async Task InsertNoteObjectPersistence(AmazonDynamoDBClient client, int userId)
    {
        var context = new DynamoDBContext(client);
        long noteId = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        var note = new Note
        {
            UserId = userId,
            NoteId = noteId,
            Content = "Hello from Object Persistence Model!",
            IsFavorite = true,
            Tags = new List<string> { "persistence", "dotnet", "poco" },
            Metadata = new NoteMetadata
            {
                Author = "User1",
                CreatedDate = DateTime.UtcNow.ToString("yyyy-MM-dd")
            }
        };

        await context.SaveAsync(note);
        Console.WriteLine($"  ✓ Inserted using Object Persistence Model. NoteId = {noteId}");
    }

    static async Task QueryNotesByUserIdObjectPersistence(AmazonDynamoDBClient client, int userId)
    {
        var context = new DynamoDBContext(client);

        // Query returns strongly-typed Note objects
        var notes = await context.QueryAsync<Note>(userId).GetRemainingAsync();

        Console.WriteLine($"  📄 Query results for UserId = {userId}:");
        foreach (var note in notes)
        {
            Console.WriteLine($"     NoteId: {note.NoteId}");
            Console.WriteLine($"     Content: {note.Content ?? "(null)"}");
            Console.WriteLine($"     Favorite: {note.IsFavorite}");
            Console.WriteLine($"     Tags: {string.Join(", ", note.Tags ?? new List<string>())}");
            Console.WriteLine("     ────");
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Document Model API Functions
    // ═══════════════════════════════════════════════════════════════════════════

    static async Task InsertNoteDocumentApi(AmazonDynamoDBClient client, string tableName, int userId)
    {
        var table = Table.LoadTable(client, tableName);
        long noteId = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        var tags = new DynamoDBList();
        tags.Add(new Primitive("document"));
        tags.Add(new Primitive("dotnet"));

        var doc = new Document
        {
            ["UserId"] = userId,
            ["NoteId"] = noteId,
            ["Content"] = "Hello from Document Model API!",
            ["Favorite"] = true,
            ["Tags"] = tags,
            ["Metadata"] = new Document
            {
                ["Author"] = "User1",
                ["CreatedDate"] = DateTime.UtcNow.ToString("yyyy-MM-dd")
            }
        };

        await table.PutItemAsync(doc);
        Console.WriteLine($"  ✓ Inserted using Document Model API. NoteId = {noteId}");
    }

    static async Task QueryNotesByUserIdDocumentApi(AmazonDynamoDBClient client, string tableName, int userId)
    {
        var table = Table.LoadTable(client, tableName);
        var filter = new QueryFilter("UserId", QueryOperator.Equal, userId);
        var search = table.Query(filter);

        Console.WriteLine($"  📄 Query results for UserId = {userId}:");
        do
        {
            var docs = await search.GetNextSetAsync();
            foreach (var doc in docs)
            {
                Console.WriteLine($"     NoteId: {doc["NoteId"]}");

                if (doc.ContainsKey("Content"))
                    Console.WriteLine($"     Content: {doc["Content"]}");
                else if (doc.ContainsKey("Note"))
                    Console.WriteLine($"     Content: {doc["Note"]}");
                else
                    Console.WriteLine("     Content: (not present)");

                Console.WriteLine("     ────");
            }
        } while (!search.IsDone);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Low-Level API Functions
    // ═══════════════════════════════════════════════════════════════════════════

    static async Task InsertNoteLowLevelApi(AmazonDynamoDBClient client, string tableName, int userId)
    {
        long noteId = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        var request = new PutItemRequest
        {
            TableName = tableName,
            Item = new Dictionary<string, AttributeValue>
            {
                { "UserId", new AttributeValue { N = userId.ToString() } },
                { "NoteId", new AttributeValue { N = noteId.ToString() } },
                { "Content", new AttributeValue { S = "Hello from Low-Level API!" } },
                { "Favorite", new AttributeValue { BOOL = true } },
                { "Tags", new AttributeValue {
                    L = new List<AttributeValue> {
                        new AttributeValue { S = "lowlevel" },
                        new AttributeValue { S = "dotnet" }
                    }
                }},
                { "Metadata", new AttributeValue {
                    M = new Dictionary<string, AttributeValue> {
                        { "Author", new AttributeValue { S = "User1" } },
                        { "CreatedDate", new AttributeValue { S = DateTime.UtcNow.ToString("yyyy-MM-dd") } }
                    }
                }}
            }
        };

        await client.PutItemAsync(request);
        Console.WriteLine($"  ✓ Inserted using Low-Level API. NoteId = {noteId}");
    }

    static async Task QueryNotesByUserIdLowLevelApi(AmazonDynamoDBClient client, string tableName, int userId)
    {
        var request = new QueryRequest
        {
            TableName = tableName,
            KeyConditionExpression = "UserId = :uid",
            ExpressionAttributeValues = new Dictionary<string, AttributeValue>
            {
                { ":uid", new AttributeValue { N = userId.ToString() } }
            }
        };

        var response = await client.QueryAsync(request);

        Console.WriteLine($"  📄 Query results for UserId = {userId}:");
        foreach (var item in response.Items)
        {
            string noteId = item.ContainsKey("NoteId") ? item["NoteId"].N : "(missing)";
            string content = item.ContainsKey("Content") ? item["Content"].S : 
                             item.ContainsKey("Note") ? item["Note"].S : "(missing)";

            Console.WriteLine($"     NoteId: {noteId}");
            Console.WriteLine($"     Content: {content}");
            Console.WriteLine("     ────");
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Table Creation (Low-Level API)
    // ═══════════════════════════════════════════════════════════════════════════

    static async Task EnsureTableExists(AmazonDynamoDBClient client, string tableName)
    {
        try
        {
            var describe = await client.DescribeTableAsync(tableName);
            Console.WriteLine($"  ✓ Table '{tableName}' exists (status: {describe.Table.TableStatus})\n");
        }
        catch (ResourceNotFoundException)
        {
            Console.WriteLine($"  Table '{tableName}' not found. Creating...");
            await CreateTableLowLevelApi(client, tableName);
        }
    }

    static async Task CreateTableLowLevelApi(AmazonDynamoDBClient client, string tableName)
    {
        var request = new CreateTableRequest
        {
            TableName = tableName,
            KeySchema = new List<KeySchemaElement>
            {
                new KeySchemaElement("UserId", KeyType.HASH),
                new KeySchemaElement("NoteId", KeyType.RANGE)
            },
            AttributeDefinitions = new List<AttributeDefinition>
            {
                new AttributeDefinition("UserId", ScalarAttributeType.N),
                new AttributeDefinition("NoteId", ScalarAttributeType.N)
            },
            BillingMode = BillingMode.PAY_PER_REQUEST
        };

        await client.CreateTableAsync(request);

        // Wait for table to become ACTIVE
        string status = "CREATING";
        while (status != "ACTIVE")
        {
            Console.WriteLine($"  Waiting for table... Status: {status}");
            await Task.Delay(3000);
            var describe = await client.DescribeTableAsync(tableName);
            status = describe.Table.TableStatus;
        }

        Console.WriteLine($"  ✓ Table '{tableName}' is ACTIVE\n");
    }
}
