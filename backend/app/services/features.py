"""Turn validated customer rows into the numeric matrix the model needs.

Categories are one-hot encoded with a *fixed* list of values (from fields.py),
so training and prediction always produce exactly the same columns.
"""
import pandas as pd

from app.services.fields import FEATURE_FIELDS, CategoryField


def _one_hot_name(field_name: str, category: str) -> str:
    return f"{field_name}__{category.replace(' ', '_')}"


MODEL_COLUMNS: list[str] = []
SOURCE_FEATURE: dict[str, str] = {}  # model column -> original customer field
for _spec in FEATURE_FIELDS:
    if isinstance(_spec, CategoryField):
        for _category in _spec.allowed:
            MODEL_COLUMNS.append(_one_hot_name(_spec.name, _category))
            SOURCE_FEATURE[MODEL_COLUMNS[-1]] = _spec.name
    else:
        MODEL_COLUMNS.append(_spec.name)
        SOURCE_FEATURE[_spec.name] = _spec.name


def build_feature_matrix(data: pd.DataFrame) -> pd.DataFrame:
    columns = {}
    for spec in FEATURE_FIELDS:
        if isinstance(spec, CategoryField):
            for category in spec.allowed:
                columns[_one_hot_name(spec.name, category)] = (data[spec.name] == category).astype(int)
        else:
            columns[spec.name] = data[spec.name].astype(float)
    return pd.DataFrame(columns, index=data.index)[MODEL_COLUMNS]
