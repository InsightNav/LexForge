from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()


def redact_text(text: str):
    results = analyzer.analyze(text=text, language="en")

    if not results:
        return text, {}

    mapping = {}
    redacted_text = text

    # reverse order prevents index shifting bugs
    for i, res in enumerate(sorted(results, key=lambda x: x.start, reverse=True)):
        placeholder = f"[REDACTED_{res.entity_type}_{i}]"

        mapping[placeholder] = text[res.start:res.end]

        redacted_text = (
            redacted_text[:res.start]
            + placeholder
            + redacted_text[res.end:]
        )

    return redacted_text, mapping


def restore_text(text: str, mapping: dict):
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text


def restore_text_deep(data, mapping):
    if isinstance(data, dict):
        return {k: restore_text_deep(v, mapping) for k, v in data.items()}
    if isinstance(data, list):
        return [restore_text_deep(i, mapping) for i in data]
    if isinstance(data, str):
        return restore_text(data, mapping)
    return data