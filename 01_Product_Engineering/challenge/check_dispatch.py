"""What the model gets back when its tool call is wrong. No model, no wiki.

    uv run python check_dispatch.py

Feeds suggest.dispatch two bad calls, an unknown tool name and malformed arguments, with a
search that fails the check if it is ever reached: neither call may run the capability.
"""

from suggest import CapabilityCounter, dispatch


def must_not_run(**kwargs):
    raise AssertionError(f"search ran for a bad call: {kwargs}")


counter = CapabilityCounter()
cases = {
    "unknown tool name": {"name": "lookup_skill", "arguments": '{"query": "water bars"}'},
    "malformed arguments": {"name": "search_chunks", "arguments": '{"query": "water bars", k: 4'},
    "missing query": {"name": "search_chunks", "arguments": '{"k": 4}'},
}
for label, function in cases.items():
    print(f"{label}: {dispatch({'id': 'call_1', 'function': function}, must_not_run, counter)}")
assert counter.calls == 0
print("ok: no bad call reached search_chunks")
