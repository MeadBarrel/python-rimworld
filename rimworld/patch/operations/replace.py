""" Provides PatchOperationReplace """

from dataclasses import dataclass
from typing import Self, cast

from lxml import etree

from rimworld.error import MalformedPatchError, NoNodesFound, PatchError
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import SafeElement, ensure_value, ensure_xpath
from rimworld.xml import ElementXpath, TextXpath


@dataclass(frozen=True, kw_only=True)
class PatchOperationReplace(PatchOperation):
    """PatchOperationReplace

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationReplace
    """

    xpath: ElementXpath | TextXpath
    value: SafeElement

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:
        match self.xpath:
            case ElementXpath():
                if isinstance(self.value, str):
                    raise PatchError(
                        "Elements can only be replaced with other elements"
                    )
                found = self.xpath.search(xml)
                if not found:
                    return PatchOperationFailedResult(
                        self, NoNodesFound(str(self.xpath))
                    )
                for f in found:
                    parent = f.getparent()
                    if parent is None:
                        raise PatchError(f"Parent not found for {self.xpath}")
                    v1, *v_ = self.value.copy()
                    parent.replace(f, v1)

                    for v in reversed(v_):
                        v1.addnext(v)

            case TextXpath():
                found = self.xpath.search(xml)
                if not found:
                    return PatchOperationFailedResult(
                        self, NoNodesFound(str(self.xpath))
                    )
                for f in found:
                    value = self.value.copy()
                    if value.text is not None:
                        f.node.text = value.text
                    else:
                        f.node.text = None
                        for v in value:
                            f.node.append(v)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        xpath = ensure_xpath(node)
        if type(xpath) not in (ElementXpath, TextXpath):
            raise MalformedPatchError("Replace only work on text or elements")

        return cls(
            xpath=cast(ElementXpath | TextXpath, xpath),
            value=ensure_value(node),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationReplace")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)

        node.append(self.value.copy())
