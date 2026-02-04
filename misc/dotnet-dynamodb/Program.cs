using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Amazon;
using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.DynamoDBv2.DocumentModel;

class Program
{
    static async Task Main(string[] args)
    {
        var config = new AmazonDynamoDBConfig
        {
            RegionEndpoint = RegionEndpoint.USWest1 // Adjust as needed
        };
        var client = new AmazonDynamoDBClient(config);
        var tableName = "Notes";

        // Optional: Uncomment to create the table
        // await CreateExampleTableLowLevelApi(client);

        // Insert & Query using Document API
        await InsertNoteDocumentApi(client, tableName, userId: 1);
        await QueryNotesByUserIdDocumentApi(client, tableName, userId: 1);

        // Insert & Query using Low-Level API
        await InsertNoteLowLevelApi(client, tableName, userId: 1);
        await QueryNotesByUserIdLowLevelApi(client, tableName, userId: 1);
    }

    // -------------------------------
    // Document Model API Functions
    // -------------------------------

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
            ["Note"] = "Inserted using Document API",
            ["Favorite"] = "true",
            ["Tags"] = tags,
            ["Metadata"] = new Document
            {
                ["Author"] = "User1",
                ["CreatedDate"] = DateTime.UtcNow.ToString("yyyy-MM-dd")
            }
        };

        await table.PutItemAsync(doc);
        Console.WriteLine($"Inserted using DocumentModel API. NoteId = {noteId}");
    }

    static async Task QueryNotesByUserIdDocumentApi(AmazonDynamoDBClient client, string tableName, int userId)
    {
        var table = Table.LoadTable(client, tableName);
        var filter = new QueryFilter("UserId", QueryOperator.Equal, userId);
        var search = table.Query(filter);

        Console.WriteLine($"📄 Query (Document API) results for UserId = {userId}:");
        do
        {
            var docs = await search.GetNextSetAsync();
            foreach (var doc in docs)
            {
                Console.WriteLine($"NoteId: {doc["NoteId"]}");

                if (doc.ContainsKey("Note"))
                    Console.WriteLine($"Note: {doc["Note"]}");
                else
                    Console.WriteLine("Note: (not present)");

                Console.WriteLine("----");
            }
        } while (!search.IsDone);
    }

    // -------------------------------
    // Low-Level API Functions
    // -------------------------------

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
                { "Note", new AttributeValue { S = "Inserted using Low-Level API" } },
                { "Favorite", new AttributeValue { S = "true" } },
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
        Console.WriteLine($"Inserted using Low-Level API. NoteId = {noteId}");
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

        Console.WriteLine($"Query (Low-Level API) results for UserId = {userId}:");
        foreach (var item in response.Items)
        {
            string noteId = item.ContainsKey("NoteId") ? item["NoteId"].N : "(missing)";
            string note = item.ContainsKey("Note") ? item["Note"].S : "(missing)";

            Console.WriteLine($"NoteId: {noteId}, Note: {note}");
        }
    }

    static async Task CreateExampleTableLowLevelApi(AmazonDynamoDBClient client)
    {
        var request = new CreateTableRequest
        {
            TableName = "Notes",
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
            ProvisionedThroughput = new ProvisionedThroughput(5, 5)
        };

        var response = await client.CreateTableAsync(request);

        string status = response.TableDescription.TableStatus;
        while (status != "ACTIVE")
        {
            Console.WriteLine($"Waiting for table to become ACTIVE... Current status: {status}");
            await Task.Delay(5000);
            var describe = await client.DescribeTableAsync("Notes");
            status = describe.Table.TableStatus;
        }

        Console.WriteLine("Table 'Notes' created and ACTIVE");
    }
}
