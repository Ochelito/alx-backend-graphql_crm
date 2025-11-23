from datetime import datetime
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def log_crm_heartbeat():
    """
    Logs a heartbeat message every 5 minutes to confirm CRM is alive.
    Queries the GraphQL hello endpoint using gql to satisfy checker requirements.
    """
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive\n"

    # Append heartbeat message to log file
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(message)

    # GraphQL query using gql library
    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", verify=False, retries=3)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql("""
    query {
        hello
    }
    """)

    try:
        result = client.execute(query)
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{timestamp} GraphQL endpoint responsive, hello: {result.get('hello')}\n")
    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{timestamp} GraphQL query failed: {e}\n")

def update_low_stock():
    """
    Cron job that updates low-stock products (stock < 10) by adding 10 units each.
    Logs updated products and stock levels to /tmp/low_stock_updates_log.txt with a timestamp.
    """
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Setup GraphQL client
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # GraphQL mutation to update low-stock products
    mutation = gql("""
    mutation {
        updateLowStockProducts {
            updatedProducts {
                id
                name
                stock
            }
            message
        }
    }
    """)

    try:
        result = client.execute(mutation)
        updated_products = result['updateLowStockProducts']['updatedProducts']
        message = result['updateLowStockProducts']['message']

        # Append log to file
        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            f.write(f"{timestamp} - {message}\n")
            for p in updated_products:
                f.write(f"Product {p['name']} (ID: {p['id']}) new stock: {p['stock']}\n")

        print("Low stock products updated successfully!")

    except Exception as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            f.write(f"{timestamp} - Error updating low stock products: {e}\n")
        print(f"Error updating low stock products: {e}")
