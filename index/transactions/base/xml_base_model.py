from typing import (
    List,
    Optional,
    Union,
    Literal,
    Self,
    Dict,
)
from pydantic import BaseModel, Field
from datetime import datetime, date
import xml.etree.ElementTree as ET
from xml.dom import minidom


class XMLBaseModel(BaseModel):
    """
    Base class that provides XML serialization and deserialization methods.
    Being a subclass of pydantic.BaseModel, it works exactly the same internally.
    This only provide additional model_dump_xml and model_validate_xml methods for XML files.
    """

    def model_dump_xml(self, tag: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> ET.Element:
        """
        Serializes the model instance to an XML element.
        
        Args:
            tag (Optional[str]): The tag name for the root element; if not provided,
                the class name is used. This parameter is deprecated in favor of tags.
            tags (Optional[Dict[str, str]]): A dictionary mapping class names or field names
                to custom XML tag names.
        
        Returns:
            ET.Element: The XML element representing the model.
        """
        tags = tags or {}
        
        if tag is None:
            class_name = self.__class__.__name__
            tag = tags.get(class_name, class_name)
            
        root = ET.Element(tag)
        for field_name in self.model_dump().keys():
            value = self.model_dump()[field_name]
            if value is None:
                continue

            # Determine XML tag for this field
            field_tag = tags.get(field_name, field_name)

            # Handle datetime values.
            if isinstance(value, datetime):
                child = ET.SubElement(root, field_tag)
                child.text = value.strftime('%d/%m/%Y')

            # If the field is a nested model (assumed to be XMLBaseModel).
            elif isinstance(value, XMLBaseModel):
                # Dump the nested model and change its tag to match the field tag
                child = value.model_dump_xml(tag=field_tag, tags=tags)
                root.append(child)

            # If the field is a list.
            elif isinstance(value, list):
                container = ET.SubElement(root, field_tag)
                for item in value:
                    if isinstance(item, XMLBaseModel):
                        # Pass tags to nested models
                        container.append(item.model_dump_xml(tags=tags))
                    else:
                        item_elem = ET.SubElement(container, "item")
                        item_elem.text = str(item)

            # Other primitive types.
            else:
                child = ET.SubElement(root, field_tag)
                child.text = str(value)
        return root
    
    def model_dump_xml_str(self, tag: Optional[str] = None, tags: Optional[Dict[str, str]] = None, 
                         encoding: Literal["unicode", "utf-8"] = "utf-8") -> str:
        """
        Serializes the model instance to an XML string representation.
        
        Args:
            tag (Optional[str]): 
                The tag name for the root element; if not provided,
                the class name is used.
            tags (Optional[Dict[str, str]]): 
                A dictionary mapping class names or field names to custom XML tag names.
            encoding ("utf-8", "unicode"):
                The encoding of the output string. Defaults to "utf-8".
        
        Returns:
            str: A valid XML string, encoded in utf-8.
        """
        return ET.tostring(self.model_dump_xml(tag=tag, tags=tags), encoding="unicode")

    def model_dump_xml_str_pretty(self, tag: Optional[str] = None, tags: Optional[Dict[str, str]] = None, 
                                encoding: Literal["unicode", "utf-8"] = "utf-8") -> str:
        """
        Serializes the model instance to an XML string representation.

        Args:
            tag (Optional[str]):
                The tag name for the root element; if not provided,
                the class name is used.
            tags (Optional[Dict[str, str]]): 
                A dictionary mapping class names or field names to custom XML tag names.
            encoding ("utf-8", "unicode"):
                The encoding of the output string. Defaults to "utf-8".

        Returns:
            str: A valid XML string, encoded in utf-8.
        """
        rough_string = ET.tostring(self.model_dump_xml(tag=tag, tags=tags), 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')

    @classmethod
    def model_validate_xml(cls, xml_data: Union[bytes, str, ET.Element], encoding: Optional[str] = "utf-8", 
                          tags: Optional[Dict[str, str]] = None, date_format: str = '%d/%m/%Y') -> Self:
        """
        Parses XML data and returns an instance of the model by iterating over its fields.
        
        Args:
            xml_data (Union[str, ET.Element]): The XML data as a string or Element.
            encoding (str, Optional): If xml_data is bytes, run decode using this encoding parameter. Defaults to "utf-8".
            tags (Optional[Dict[str, str]]): A dictionary mapping class names or field names
                to custom XML tag names. The same dictionary used in model_dump_xml can be used here.
            date_format (str, Optional): Format string for parsing dates. Defaults to '%d/%m/%Y'.
        
        Returns:
            An instance of the model populated from the XML.
        """
        if isinstance(xml_data, str):
            root = ET.fromstring(xml_data)
        elif isinstance(xml_data, bytes):
            root = ET.fromstring(xml_data.decode(encoding=encoding))
        else:
            root = xml_data

        tags = tags or {}
        
        # Create a reverse mapping from tag names to field names
        reverse_tags = {}
        for field_name, tag_name in tags.items():
            reverse_tags[tag_name] = field_name

        data = {}
        for field_name, field_info in cls.model_fields.items():
            # Get the custom XML tag for this field
            xml_tag = tags.get(field_name, field_name)
            
            # Look for element with this tag name
            elem = root.find(xml_tag)
            if elem is None:
                continue

            # Retrieve the field type using the annotation.
            field_type = field_info.annotation

            # Handle Optional types
            if getattr(field_type, "__origin__", None) is Union and type(None) in field_type.__args__:
                # Get the inner type from the Union (excluding None)
                inner_types = [t for t in field_type.__args__ if t is not type(None)]
                if len(inner_types) == 1:
                    field_type = inner_types[0]

            # Handle list types by examining the __args__ attribute.
            if getattr(field_type, "__origin__", None) is list:
                # Get the inner type for the list.
                inner_type = field_type.__args__[0]
                items = []
                for child in list(elem):
                    if isinstance(inner_type, type) and issubclass(inner_type, XMLBaseModel):
                        # Pass tags to nested model validation
                        items.append(inner_type.model_validate_xml(child, tags=tags, date_format=date_format))
                    elif inner_type is datetime or inner_type is date:
                        if child.text:
                            try:
                                items.append(datetime.strptime(child.text, date_format))
                            except ValueError:
                                # Try ISO format as fallback
                                try:
                                    items.append(datetime.fromisoformat(child.text))
                                except ValueError:
                                    # If parsing fails, pass the raw text and let Pydantic handle validation
                                    items.append(child.text)
                        else:
                            items.append(None)
                    elif inner_type in (int, float):
                        items.append(inner_type(child.text))
                    else:
                        items.append(child.text)
                data[field_name] = items
            # Handle nested XMLBaseModel types.
            elif isinstance(field_type, type) and issubclass(field_type, XMLBaseModel):
                # Pass tags to nested model validation
                data[field_name] = field_type.model_validate_xml(elem, tags=tags, date_format=date_format)
            # Handle datetime values.
            elif field_type is datetime or field_type is date:
                if elem.text:
                    try:
                        data[field_name] = datetime.strptime(elem.text, date_format)
                    except ValueError:
                        # Try ISO format as fallback
                        try:
                            data[field_name] = datetime.fromisoformat(elem.text)
                        except ValueError:
                            # If parsing fails, pass the raw text and let Pydantic handle validation
                            data[field_name] = elem.text
                else:
                    data[field_name] = None
            # Handle numeric types.
            elif field_type in (int, float):
                data[field_name] = field_type(elem.text) if elem.text else None
            # Default: assign the text content.
            else:
                data[field_name] = elem.text

        return cls(**data)
