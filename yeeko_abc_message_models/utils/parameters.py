import re


def replace_parameter(extra_values_data: dict, text: str, default: str = ""):
    pattern = r"\{\{([\w.]+)\}\}"

    def get_nested_value(data, keys):
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]

            elif isinstance(data, list):
                if not data:
                    return default

                key = "0" if key == "first" else "-1" if key == "last" else key

                if key.isdigit() and int(key) < len(data):
                    data = data[int(key)]
                elif key == "count":
                    data = len(data)
                elif key == "sum":
                    data = sum(data)
                else:
                    return default

            elif isinstance(data, str) and key in ["lower", "upper"]:
                f_data = getattr(data, key)
                data = f_data()
            else:
                return default
        return data

    def replace_match(match):
        variable = match.group(1)
        keys = variable.split(".")
        if keys[0] not in extra_values_data:
            return default

        value = get_nested_value(extra_values_data[keys[0]], keys[1:])

        if isinstance(value, str):
            return value
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, list):
            return str(value[0]) if value else default
        elif isinstance(value, dict):
            return default
        else:
            return str(value)

    result = re.sub(pattern, replace_match, text)
    result_text = re.sub(r'\s+', ' ', result.strip())
    return result_text
