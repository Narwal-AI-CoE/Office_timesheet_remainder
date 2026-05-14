from dotenv import load_dotenv
load_dotenv()

from graph_auth import get_graph_token

print(get_graph_token()[:30])