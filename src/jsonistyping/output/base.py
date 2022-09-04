from enum import Enum


class SerializableOutModel:

    def serialize(self) -> dict:
        props = self.__dict__

        for key in props.keys():
            if isinstance(props[key], SerializableOutModel):
                props[key] = props[key].serialize()
                continue

            if isinstance(props[key], Enum):
                props[key] = props[key].value
                continue

            if isinstance(props[key], list):
                if not props[key]:
                    continue

                test_item = props[key][0]
                if isinstance(test_item, SerializableOutModel) and test_item:
                    props[key] = list(map(lambda o: o.serialize(), props[key]))

        return props
