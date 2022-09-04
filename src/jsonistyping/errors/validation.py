from typing import List


class BaseValidationError(Exception):
    pass


class PropertiesValidationError(BaseValidationError):
    def __init__(self, missing_fields: List[str] = None, *args: object) -> None:
        self.missing_fields = missing_fields if missing_fields is not None else missing_fields
        super().__init__(f"Some fields are missing: {', '.join(missing_fields)}", *args)


class TypeValidationError(BaseValidationError):
    def __init__(self, fields: List[str] = None, *args: object) -> None:
        self.fields = fields if fields is not None else fields
        super().__init__(f"Some fields have incorrect type: {', '.join(fields)}", *args)


class ModelValidationError(BaseValidationError):
    def __init__(self, field_name: str, reason: str):
        super(ModelValidationError, self).__init__(f"Field '{field_name}' is invalid. Reason: {reason}")
