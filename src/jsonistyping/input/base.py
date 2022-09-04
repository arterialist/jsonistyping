from inspect import isclass
from typing import Union, _GenericAlias

from jsonistyping.errors.validation import PropertiesValidationError, TypeValidationError


class BaseModel:
    def __init__(self, data: dict, annotations: dict, request_parameters_class=None):
        self.request_parameters_class = request_parameters_class

        if data is None:
            raise ValueError("Request data is empty")

        # noinspection PyUnresolvedReferences
        for field in annotations:
            if self.request_parameters_class and isinstance(data, self.request_parameters_class):
                field_data: list = data.getlist(field, None)
            elif isinstance(data, dict):
                field_data: list = data.get(field, None)
            else:
                raise TypeError("Invalid model data type")

            field_type: Union[type, _GenericAlias] = annotations.get(field)
            field_type_class = field_type if isclass(field_type) else field_type.__class__
            field_type_class_name = field_type.__dict__.get("_name", field_type_class.__name__)

            if field_data is None:
                if field_type_class_name == "Optional":
                    self.__dict__[field] = self.__class__.__dict__.get(field, None)
                    continue
                raise PropertiesValidationError([field])

            if field_type_class_name == "Optional":
                field_type = field_type.__args__[0]
                field_type_class = field_type if isclass(field_type) else field_type.__class__
                field_type_class_name = field_type.__dict__.get("_name", field_type_class.__name__)

            try:
                if field_type_class_name == "List":
                    list_elements_type = field_type.__args__[0]
                    if isinstance(field_data, list):
                        self.__dict__[field] = list(map(lambda item: list_elements_type(item), field_data))
                    else:
                        self.__dict__[field] = [list_elements_type(field_data)]
                else:
                    if isinstance(field_data, list):
                        self.__dict__[field] = field_type(field_data[0])
                    else:
                        self.__dict__[field] = field_type(field_data)
            except ValueError:
                raise TypeError(f"Invalid field data type for {field}")

    def validate(self, initial_data: Union[dict], annotations: dict):
        if not annotations:
            raise AttributeError("Annotations are empty")

        raise TypeError(f"Class {self.__class__.__name__} can't be validated")


class ValidatableModel(BaseModel):
    def validate(self, initial_data: Union[dict], annotations: dict):
        raise NotImplementedError(f"validate() must be implemented for class {self.__class__.__name__}")


class GenericValidatableModel(ValidatableModel):
    def validate(self, initial_data: Union[dict], annotations: dict):
        missing_fields = []
        incorrect_type_fields = []
        for key in annotations:
            requested_field_type: Union[type, _GenericAlias] = annotations.get(key)
            requested_field_type_class = requested_field_type if isclass(
                requested_field_type) else requested_field_type.__class__
            field_value = self.__dict__.get(key, None)

            if key not in initial_data and requested_field_type.__dict__.get("_name", None) != "Optional":
                missing_fields.append(key)
                continue

            if not issubclass(requested_field_type_class, _GenericAlias) and not isinstance(field_value,
                                                                                            requested_field_type):
                incorrect_type_fields.append(key)
                continue

            if requested_field_type.__dict__.get("__args__", None) \
                    and requested_field_type._name in ["List", "Optional"]:  # is subscripted generic, e.g. List[int]

                allowed_types = [*requested_field_type.__args__]

                for index, allowed_type in enumerate(allowed_types):
                    class_names = [allowed_type.__dict__.get("_name", None),
                                   allowed_type.__dict__.get("__name__", None)]
                    if "List" in class_names:
                        allowed_types[index] = list
                        break

                # TODO: add proper check for Optional[List[type]] fields that will check list items' types
                if requested_field_type._name == "Optional":
                    if type(field_value) not in allowed_types:
                        incorrect_type_fields.append(key)
                        continue
                else:
                    if type(field_value) != list or list(
                            filter(lambda item: type(item) not in allowed_types, field_value)):
                        incorrect_type_fields.append(key)
                        continue

            elif type(field_value) is not requested_field_type:
                incorrect_type_fields.append(key)

        if missing_fields:
            raise PropertiesValidationError(missing_fields)

        if incorrect_type_fields:
            raise TypeValidationError(incorrect_type_fields)
