#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListResourcesRequestSchema, ListToolsRequestSchema, ReadResourceRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import sql from 'mssql';

function sendLog(message) {
  process.stdout.write(JSON.stringify({ type: 'log', message }) + '\n');
}

function sendError(error) {
  process.stdout.write(JSON.stringify({ type: 'error', message: error.message, stack: error.stack }) + '\n');
}

sendLog('Script started');

const server = new Server({
    name: "example-servers/mssql",
    version: "0.1.0",
}, {
    capabilities: {
        resources: {},
        tools: {},
    },
});

// รับ config จาก command line argument
let sqlConfig;
try {
    sqlConfig = JSON.parse(process.argv[2]);
} catch (error) {
    sendError(new Error('Invalid configuration provided'));
    process.exit(1);
}

sendLog(`Received SQL Config: ${JSON.stringify(sqlConfig, null, 2)}`);

if (!sqlConfig.server) {
    sendError(new Error('Server configuration is missing'));
    process.exit(1);
}

sqlConfig.options = {
    ...sqlConfig.options,
    encrypt: false,
    trustServerCertificate: true
};

sqlConfig.pool = {
    max: 10,
    min: 0,
    idleTimeoutMillis: 30000
};

let poolConnection = null;
async function getConnection() {
    if (!poolConnection) {
        sendLog('Establishing new connection...');
        poolConnection = sql.connect(sqlConfig);
    }
    return poolConnection;
}

server.setRequestHandler(ListResourcesRequestSchema, async () => {
    const pool = await getConnection();
    try {
        const result = await pool.request().query("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'");
        return {
            resources: result.recordset.map((row) => ({
                uri: `mssql://${row.TABLE_NAME}/schema`,
                mimeType: "application/json",
                name: `"${row.TABLE_NAME}" database schema`,
            })),
        };
    }
    catch (error) {
        sendError(error);
        throw error;
    }
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const uri = new URL(request.params.uri);
    const tableName = uri.pathname.split('/')[1];
    const pool = await getConnection();
    try {
        const result = await pool.request()
            .input('tableName', sql.VarChar, tableName)
            .query("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = @tableName");
        return {
            contents: [
                {
                    uri: request.params.uri,
                    mimeType: "application/json",
                    text: JSON.stringify(result.recordset, null, 2),
                },
            ],
        };
    }
    catch (error) {
        sendError(error);
        throw error;
    }
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "query",
                description: "Run a read-only SQL query",
                inputSchema: {
                    type: "object",
                    properties: {
                        sql: { type: "string" },
                    },
                },
            },
        ],
    };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === "query") {
        const pool = await getConnection();
        try {
            const result = await pool.request().query(request.params.arguments?.sql);
            return {
                content: [{
                    type: "text",
                    text: JSON.stringify(result.recordset, null, 2)
                }],
                isError: false,
            };
        }
        catch (error) {
            sendError(error);
            throw error;
        }
    }
    throw new Error(`Unknown tool: ${request.params.name}`);
});

process.on('beforeExit', async () => {
    if (poolConnection) {
        const pool = await poolConnection;
        await pool.close();
    }
});

async function runServer() {
    try {
        sendLog('Starting server...');
        const transport = new StdioServerTransport();
        await server.connect(transport);
        sendLog('Server connected successfully');
    } catch (error) {
        sendError(error);
    }
}

runServer().catch(sendError);