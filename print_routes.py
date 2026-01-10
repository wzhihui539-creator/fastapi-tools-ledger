# from fastapi.routing import APIRoute
# from app.main import app
#
# target_path = "/tools"
# target_method = "GET"
#
# for r in app.routes:
#     if isinstance(r, APIRoute) and r.path == target_path and target_method in r.methods:
#         print("=== Route Detail ===")
#         print("path:", r.path)
#         print("methods:", r.methods)
#         print("name:", r.name)
#         print("endpoint:", r.endpoint)
#         print("endpoint.__name__:", r.endpoint.__name__)
#         print("response_model:", r.response_model)
#         print("dependant.path_params:", [p.name for p in r.dependant.path_params])
#         print("dependant.query_params:", [p.name for p in r.dependant.query_params])
#         print("dependant.body_params:", [p.name for p in r.dependant.body_params])
#         print("dependant.dependencies:", [d.call.__name__ for d in r.dependant.dependencies])
#         break
# else:
#     print("Target route not found")



# from fastapi.routing import APIRoute
# from app.main import app
#
# target_path = "/tools/{tool_id}/quantity"
# target_method = "PATCH"
#
# for r in app.routes:
#     if isinstance(r, APIRoute) and r.path == target_path and target_method in r.methods:
#         print("=== Route Detail ===")
#         print("path:", r.path)
#         print("methods:", r.methods)
#         print("name:", r.name)
#         print("endpoint:", r.endpoint)
#         print("endpoint.__name__:", r.endpoint.__name__)
#         print("response_model:", r.response_model)
#         print("dependant.path_params:", [p.name for p in r.dependant.path_params])
#         print("dependant.query_params:", [p.name for p in r.dependant.query_params])
#         print("dependant.body_params:", [p.name for p in r.dependant.body_params])
#         print("dependant.dependencies:", [d.call.__name__ for d in r.dependant.dependencies])
#         break
# else:
#     print("Target route not found:", target_method, target_path)


from fastapi.routing import APIRoute
from fastapi.dependencies.models import Dependant
from app.main import app


target_path = "/tools/{tool_id}/quantity"
target_method = "PATCH"


def callable_name(obj) -> str:
    """更稳地拿到可调用对象的名字（函数 / 类实例 / lambda 等）。"""
    if hasattr(obj, "__name__"):
        return obj.__name__
    # OAuth2PasswordBearer 这类对象是可调用实例，没有 __name__
    cls = obj.__class__
    return f"{cls.__module__}.{cls.__name__}"


def print_dependant(dep: Dependant, indent: int = 0):
    prefix = "  " * indent
    call = dep.call
    if call is None:
        print(prefix + "- <no call>")
        return

    print(prefix + f"- {callable_name(call)}")

    # 递归打印它的子依赖
    for child in dep.dependencies:
        print_dependant(child, indent + 1)


for r in app.routes:
    if isinstance(r, APIRoute) and r.path == target_path and target_method in r.methods:
        print("=== Route Detail ===")
        print("path:", r.path)
        print("methods:", r.methods)
        print("name:", r.name)
        print("endpoint:", callable_name(r.endpoint))
        print("response_model:", r.response_model)

        print("path_params:", [p.name for p in r.dependant.path_params])
        print("query_params:", [p.name for p in r.dependant.query_params])
        print("body_params:", [p.name for p in r.dependant.body_params])

        print("\n=== Dependency Tree ===")
        # 注意：r.dependant 本身代表“这个路由函数的依赖集合”
        for d in r.dependant.dependencies:
            print_dependant(d, indent=0)

        break
else:
    print("Target route not found:", target_method, target_path)
