# Language Support

This document explains how to use and extend the language support in the NLP2DB-MRAG application.

## Available Languages

The application currently supports the following languages:

- English (en)
- Portuguese (pt)
- Chinese (zh)

## Configuration

Language selection is controlled by the `LANGUAGE` environment variable. You can set this in your `.env` file:

```
LANGUAGE=pt  # Options: en, pt, zh
```

## How Language Support Works

The application uses a translation system with two main components:

1. **UI Translations**: Managed by `lang_content_mapping.py` and accessed through `get_lang_text()`
2. **Model Prompts**: Managed by `prompt_language.py` and accessed through `get_prompt_template()`

### UI Translations

UI translations are used for interface elements like buttons, labels, and messages. These are stored in the `lang_dicts` dictionary in `pilot/language/lang_content_mapping.py`.

Example usage:
```python
from pilot.language.translation_handler import get_lang_text

button_label = get_lang_text("send")  # Returns "Send" in English or "Enviar" in Portuguese
```

### Model Prompts

Model prompts are used for interactions with the language model. These are stored in the `prompt_templates` dictionary in `pilot/language/prompt_language.py`.

Example usage:
```python
from pilot.language.prompt_language import get_prompt_template

sql_role_prompt = get_prompt_template("sql_expert_role")
```

## Adding New Translations

### Adding a New UI Translation

1. Add the new key and translation to each language dictionary in `pilot/language/lang_content_mapping.py`:

```python
"en": {
    "new_key": "English translation",
    # ...
},
"pt": {
    "new_key": "Portuguese translation",
    # ...
},
```

2. Use the translation in your code:

```python
label = get_lang_text("new_key")
```

### Adding a New Prompt Translation

1. Add the new key and translation to each language dictionary in `pilot/language/prompt_language.py`:

```python
"en": {
    "new_prompt_key": "English prompt text",
    # ...
},
"pt": {
    "new_prompt_key": "Portuguese prompt text",
    # ...
},
```

2. Use the translation in your code:

```python
prompt = get_prompt_template("new_prompt_key")
```

## Adding a New Language

To add support for a new language:

1. Add a new language dictionary to `lang_dicts` in `pilot/language/lang_content_mapping.py`
2. Add a new language dictionary to `prompt_templates` in `pilot/language/prompt_language.py`
3. Translate all keys from an existing language to the new language

## Testing Language Support

You can test language support using the `test_language_support.py` script:

```bash
python test_language_support.py
```

This will display translations for various keys in all supported languages.
