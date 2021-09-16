from typing import *


class Message(TypedDict):
    jsonrpc: 'str'


class RequestMessage(Message, total=False):
    id: Union[int, str]
    method: str
    params: Union[List, object, None]


RequestMessage.__optional_keys__ = frozenset({'params}'})
RequestMessage.__required_keys__ = frozenset({'jsonrpc', 'id', 'method', 'params'})


if __name__ == "__main__":
    msg = Message(jsonrpc="HI")
    rmsg = RequestMessage(jsonrpc="Hi, again", id=1, method="method", params=[1, 2, 3])
    print(rmsg)
    rmsg = RequestMessage(jsonrpc="Hi, again", id=1, method="method")
    rmsg = RequestMessage(jsonrpc="Hi, again", method="method", params=[1, 2, 3])
