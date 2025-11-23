#!/usr/bin/env python3
"""
Python script to query GraphQL for pending orders in the last 7 days
and log reminders to /tmp/order_reminders_log.txt
"""

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql"

# Prepare transport and client
transport = RequestsHTTPTransport(url=GRAPHQL_URL, verify=False, retries=3)
client = Client(transport=transport, fetch_schema_from_transport=True)

# GraphQL query to get orders in the last 7 days
query = gql("""
query getRecentOrders($startDate: DateTime!) {
  allOrders(filter: {orderDateGte: $startDate}) {
    edges {
      node {
        id
        customer {
          email
        }
        orderDate
      }
    }
  }
}
""")

# Calculate start date
start_date = (datetime.now() - timedelta(days=7)).isoformat()

# Execute query
try:
    result = client.execute(query, variable_values={"startDate": start_date})
    orders = result["allOrders"]["edges"]
except Exception as e:
    print(f"Error fetching orders: {e}")
    orders = []

# Logging
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open("/tmp/order_reminders_log.txt", "a") as f:
    for order in orders:
        order_node = order["node"]
        order_id = order_node["id"]
        customer_email = order_node["customer"]["email"]
        f.write(f"{timestamp} - Order ID {order_id}, Customer {customer_email}\n")

print("Order reminders processed!")
