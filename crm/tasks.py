from celery import shared_task
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

@shared_task
def generate_crm_report():
    """
    Generates a weekly CRM report: total customers, total orders, total revenue.
    Logs the report to /tmp/crm_report_log.txt
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Setup GraphQL client
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # GraphQL query to fetch totals
    query = gql("""
    query {
        allCustomers {
            totalCount
        }
        allOrders {
            totalCount
            edges {
                node {
                    totalAmount
                }
            }
        }
    }
    """)

    try:
        result = client.execute(query)
        total_customers = result['allCustomers']['totalCount']
        total_orders = result['allOrders']['totalCount']
        total_revenue = sum(order['node']['totalAmount'] for order in result['allOrders']['edges'])

        # Log the report
        log_line = f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n"
        with open("/tmp/crm_report_log.txt", "a") as f:
            f.write(log_line)

        print("CRM report generated successfully!")

    except Exception as e:
        with open("/tmp/crm_report_log.txt", "a") as f:
            f.write(f"{timestamp} - Error generating report: {e}\n")
        print(f"Error generating CRM report: {e}")
