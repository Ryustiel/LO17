
from typing import (
    List,
    Optional,
    Union,
    Literal,
)
from pydantic import BaseModel, Field
from datetime import datetime
import xml.etree.ElementTree as ET


class XMLBaseModel(BaseModel):
    """
    Base class that provides XML serialization and deserialization methods
    by iterating over fields.
    """

    def model_dump_xml(self, tag: Optional[str] = None) -> ET.Element:
        """
        Serializes the model instance to an XML element.
        
        Args:
            tag (Optional[str]): The tag name for the root element; if not provided,
                the class name is used.
        
        Returns:
            ET.Element: The XML element representing the model.
        """
        if tag is None:
            tag = self.__class__.__name__
        root = ET.Element(tag)
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            if value is None:
                continue

            # Handle datetime values.
            if isinstance(value, datetime):
                child = ET.SubElement(root, field_name)
                child.text = value.isoformat()

            # If the field is a nested model (assumed to be XMLBaseModel).
            elif isinstance(value, XMLBaseModel):
                # Dump the nested model and change its tag to match the field name.
                child = value.model_dump_xml(tag=field_name)
                root.append(child)

            # If the field is a list.
            elif isinstance(value, list):
                container = ET.SubElement(root, field_name)
                for item in value:
                    if isinstance(item, XMLBaseModel):
                        container.append(item.model_dump_xml())
                    else:
                        item_elem = ET.SubElement(container, "item")
                        item_elem.text = str(item)

            # Other primitive types.
            else:
                child = ET.SubElement(root, field_name)
                child.text = str(value)
        return root
    
    def model_dump_xml_str(self, tag: Optional[str] = None, encoding: Literal["unicode", "utf-8"] = "utf-8") -> str:
        """
        Serializes the model instance to an XML string representation.
        
        Args:
            tag (Optional[str]): 
                The tag name for the root element; if not provided,
                the class name is used.
            encoding ("utf-8", "unicode"):
                The encoding of the output string. Defaults to "utf-8".
        
        Returns:
            str: A valid XML string, encoded in utf-8.
        """
        return ET.tostring(self.model_dump_xml(tag=tag), encoding="utf-8")

    @classmethod
    def model_validate_xml(cls, xml_data: Union[bytes, str, ET.Element], encoding: Optional[str] = "utf-8") -> "XMLBaseModel":
        """
        Parses XML data and returns an instance of the model by iterating over its fields.
        
        Args:
            xml_data (Union[str, ET.Element]): The XML data as a string or Element.
            encoding (str, Optional): If xml_data is bytes, run decode using this encoding parameter. Defaults to "utf-8".
        
        Returns:
            An instance of the model populated from the XML.
        """
        if isinstance(xml_data, str):
            root = ET.fromstring(xml_data)
        elif isinstance(xml_data, bytes):
            root = ET.fromstring(xml_data.decode(encoding=encoding))
        else:
            root = xml_data

        data = {}
        for field_name, field_info in cls.model_fields.items():
            elem = root.find(field_name)
            if elem is None:
                continue

            # Retrieve the field type using the annotation.
            field_type = field_info.annotation

            # Handle list types by examining the __args__ attribute.
            if getattr(field_type, "__origin__", None) is list:
                # Get the inner type for the list.
                inner_type = field_type.__args__[0]
                items = []
                for child in list(elem):
                    if isinstance(inner_type, type) and issubclass(inner_type, XMLBaseModel):
                        items.append(inner_type.model_validate_xml(child))
                    elif inner_type is datetime:
                        items.append(datetime.fromisoformat(child.text) if child.text else None)
                    elif inner_type in (int, float):
                        items.append(inner_type(child.text))
                    else:
                        items.append(child.text)
                data[field_name] = items
            # Handle nested XMLBaseModel types.
            elif isinstance(field_type, type) and issubclass(field_type, XMLBaseModel):
                data[field_name] = field_type.model_validate_xml(elem)
            # Handle datetime values.
            elif field_type is datetime:
                data[field_name] = datetime.fromisoformat(elem.text) if elem.text else None
            # Handle numeric types.
            elif field_type in (int, float):
                data[field_name] = field_type(elem.text)
            # Default: assign the text content.
            else:
                data[field_name] = elem.text

        return cls(**data)
    