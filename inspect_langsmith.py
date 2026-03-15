from langsmith import trace
try:
    with trace('test_exception') as rt:
        raise ValueError("Boom!")
except Exception:
    print(f"Error on rt: {rt.error}")
