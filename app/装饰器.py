def deco(func):
    def wrapper(*args, **kwargs):
        print("调用前")
        result = func(*args, **kwargs)
        print("调用后")
        return result
    return wrapper

@deco
def hello(name):
    print("你好", name)

deco(hello('Jack'))

print(30*'-')

hello("Neil")