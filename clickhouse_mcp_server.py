from typing import Any
from mcp.server.fastmcp import FastMCP
import clickhouse_connect
import os
import shutil

# Initialize FastMCP server
mcp = FastMCP("clickhouse")

clickhouse_client = clickhouse_connect.get_client(host='localhost', username='default')
clickhouse_client.query('set mutations_sync=1')


@mcp.tool()
async def get_tables() -> dict[str, str]:
    """Get all tables in the ClickHouse database"""
    try:
        result = clickhouse_client.query("SHOW TABLES")
        if result is not None and result.result_rows is not None:
            tables = ", ".join([row[0] for row in result.result_rows])
            return {
                "status": "success",
                "comma-separated-table-names": tables,
            }
        return {
            "status": "success",
            "message": "No tables found",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting tables: {e}",
        }


@mcp.tool()
async def execute_query(query: str) -> dict[str, Any]:
    """Execute a ClickHouse query and return the results"""
    try:
        result = clickhouse_client.query(query)
        
        return {
            "status": "success",
            "data": result.result_rows
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error executing query: {e}",
        }


@mcp.tool()
async def show_csv_and_parquetfiles_in_clickhouse_user_files_directory() -> dict[str, Any]:
    """Show files in the ClickHouse user files directory"""
    try:
        path = "clickhouse_user_files_path"
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith('.csv') or f.endswith('.parquet')]
        files_string = ", ".join(files)
        return {
            "status": "success",
            "comma-separated-file-names": files_string,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error showing files: {e}",
        }


@mcp.tool()
async def copy_csv_or_parquet_file_to_clickhouse_user_files_directory(windows_file_path: str) -> dict[str, Any]:
    """Copy a Windows file to the ClickHouse user files directory"""
    try:
        path = "clickhouse_user_files_path"
        if windows_file_path.endswith('.csv') or windows_file_path.endswith('.parquet'):
            shutil.copy(windows_file_path, path)
        else:
            return {
                "status": "error",
                "message": "File is not a CSV or Parquet file",
            }
        return {
            "status": "success",
            "message": f"File {windows_file_path} copied to {path}",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error copying file: {e}",
        }


@mcp.tool()
async def create_table_from_csv(table_name: str, csv_file: str) -> dict[str, str]:
    """Create a clickhouse table from a CSV file"""
    try:
        clickhouse_client.query(f"""CREATE TABLE {table_name}
            ENGINE = MergeTree()
            ORDER BY tuple() AS
            SELECT *
            FROM file('{csv_file}', 'CSVWithNames')""")
        return {
            "status": "success",
            "message": f"Table {table_name} created successfully",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating table: {e}",
        }


@mcp.tool()
async def drop_table(table_name: str) -> dict[str, str]:
    """Drop a clickhouse table"""
    try:
        clickhouse_client.query(f"DROP TABLE {table_name}")
        return {
            "status": "success",
            "message": f"Table {table_name} dropped successfully",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error dropping table: {e}",
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")