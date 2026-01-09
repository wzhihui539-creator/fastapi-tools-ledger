from fastapi.routing import APIRoute
from app.main import app

target_path = "/tools"
target_method = "GET"

for r in app.routes:
    if isinstance(r, APIRoute) and r.path == target_path and target_method in r.methods:
        print("=== Route Detail ===")
        print("path:", r.path)
        print("methods:", r.methods)
        print("name:", r.name)
        print("endpoint:", r.endpoint)
        print("endpoint.__name__:", r.endpoint.__name__)
        print("response_model:", r.response_model)
        print("dependant.path_params:", [p.name for p in r.dependant.path_params])
        print("dependant.query_params:", [p.name for p in r.dependant.query_params])
        print("dependant.body_params:", [p.name for p in r.dependant.body_params])
        print("dependant.dependencies:", [d.call.__name__ for d in r.dependant.dependencies])
        break
else:
    print("Target route not found")
