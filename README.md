# ClickHouse MCP Agent

An AI-powered agent that interacts with ClickHouse databases using natural language queries. Built with the Model Context Protocol (MCP) and Claude AI.

## Overview

This project consists of two main components:

1. **ClickHouse MCP Server** (`clickhouse_mcp_server.py`) - An MCP server that exposes ClickHouse database operations as tools
2. **MCP Client** (`mcp_client.py`) - An intelligent client that uses Claude AI to process natural language queries and automatically execute the appropriate ClickHouse operations

## Features

### ClickHouse MCP Server Tools

- **Get Tables**: List all tables in the ClickHouse database
- **Execute Query**: Run any ClickHouse SQL query and get results
- **File Management**: List CSV and Parquet files in the ClickHouse user files directory
- **Import Data**: Copy CSV/Parquet files to ClickHouse user files directory
- **Create Tables**: Create ClickHouse tables directly from CSV files
- **Drop Tables**: Remove tables from the database

### MCP Client Capabilities

- Natural language query processing using Claude AI
- Automatic tool selection and execution
- Multi-step tool call handling
- API call limiting for cost control
- Interactive chat interface
- Detailed execution logging

## Prerequisites

- Python 3.10+
- ClickHouse server running locally or accessible via network
- Anthropic API key (for Claude AI)
- Required Python packages (see Installation)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd clickhouse-agent
```

2. Install dependencies:
```bash
pip install anthropic python-dotenv mcp clickhouse-connect
```

3. Create a `.env` file in the project root and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

4. Configure ClickHouse connection:
   - Update the connection parameters in `clickhouse_mcp_server.py` (lines 10-11) to match your ClickHouse setup
   - Update the user files directory path in the server if needed

## Usage

### Starting the Client

Run the MCP client to start an interactive session:

```bash
python mcp_client.py
```

The client will:
1. Connect to the ClickHouse MCP server
2. Load available tools
3. Start an interactive chat loop

### Example Queries

Once the client is running, you can ask natural language questions:

```
Query: What tables are available in the database?

Query: Show me the first 10 rows from the orders table

Query: Find all orders where the shipping city is different from the billing city

Query: Create a table called customer_data from the customers.csv file

Query: What are the top 5 products by total order amount?
```

### How It Works

1. You enter a natural language query
2. The client sends your query to Claude AI along with available MCP tools
3. Claude analyzes the query and determines which tools to use
4. The client executes the selected tools on the ClickHouse MCP server
5. Results are sent back to Claude for processing
6. Claude provides a natural language response with the results

### API Call Limits

The client has a built-in API call limit (default: 20 calls per session) to control costs. You can modify this in `mcp_client.py` by changing the `max_total_api_calls` parameter.

## Configuration

### ClickHouse Connection

Edit `clickhouse_mcp_server.py` to configure your ClickHouse connection:

```python
clickhouse_client = clickhouse_connect.get_client(
    host='your_host',
    port=your_port,
    username='your_username',
    password='your_password'  # if required
)
```

### MCP Server Selection

By default, `mcp_client.py` connects to `clickhouse_mcp_server.py`. You can change the server by modifying:

```python
SERVER_SCRIPT_PATH = "clickhouse_mcp_server.py"
```

## Project Structure

```
clickhouse-agent/
├── clickhouse_mcp_server.py   # MCP server with ClickHouse tools
├── mcp_client.py               # AI-powered MCP client
├── .env                        # Environment variables (API keys)
├── README.md                   # This file
└── csv_files/                  # Sample CSV files (if any)
```

## Architecture

```
┌─────────────────┐
│   User Query    │
│  (Natural Lang) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Client    │
│  (mcp_client)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Claude API    │
│  (Anthropic)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Server    │
│  (clickhouse)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ClickHouse    │
│    Database     │
└─────────────────┘
```

## Error Handling

The client includes comprehensive error handling:
- API call limit enforcement
- Connection error management
- Tool execution error reporting
- Detailed logging for debugging

## Development

### Adding New Tools

To add new tools to the ClickHouse MCP server:

1. Open `clickhouse_mcp_server.py`
2. Add a new function decorated with `@mcp.tool()`:

```python
@mcp.tool()
async def your_new_tool(param1: str, param2: int) -> dict[str, Any]:
    """Description of what your tool does"""
    try:
        # Your implementation
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {e}"
        }
```

3. Restart the client to load the new tool

## Limitations

- Requires active internet connection for Claude API calls
- API costs apply for each Claude API call
- ClickHouse server must be accessible from the machine running the MCP server
- File operations assume specific directory structure (configurable)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Acknowledgments

- Built with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- Powered by [Claude AI](https://www.anthropic.com/) from Anthropic
- Uses [ClickHouse](https://clickhouse.com/) for data storage and querying

## Support

For issues, questions, or contributions, please open an issue on GitHub.

