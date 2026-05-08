import json
import re
import time


def extract_code_blocks(text: str) -> str:

    matches = re.findall(
        r"```(?:\w+)?\n(.*?)```",
        text,
        re.DOTALL,
    )

    return "\n\n".join(matches)


def timed(label, fn):
    start = time.time()
    result = fn()
    elapsed = time.time() - start
    print(f"{label}: {elapsed:.2f}s")
    return result


def extract_json(text: str):
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        json_text = text[start:end]
        return json.loads(json_text)

    except Exception as e:
        print("JSON PARSE ERROR")
        print(e)

        return []
