from fastapi import HTTPException

def remap_keys(data: dict, required: list[str]) -> dict[str, str]:
    found_substrings = {key: False for key in required}

    for key in data.keys():
        for substring in required:
            if substring in key:
                if found_substrings[substring]:
                    raise HTTPException(415, f".geojson properties has multiple substrings with '{substring}'. Please ensure each property only contains this substring once.")
                found_substrings[substring] = data[key]

    for substring, found in found_substrings.items():
        if not found:
            raise HTTPException(415, f"'{substring}' not found in .geojson properties. Please ensure '{substring}' is contained in one of the properties.")

    return found_substrings