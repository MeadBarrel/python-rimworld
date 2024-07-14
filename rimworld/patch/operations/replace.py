from dataclasses import dataclass
from typing import Self, cast
from lxml import etree

from rimworld.xml import ElementXpath, TextXpath

from .. import *


@dataclass(frozen=True, kw_only=True)
class PatchOperationReplace(PatchOperation):
    xpath: ElementXpath|TextXpath
    value: list[SafeElement]|str

    def apply(self, context: PatchContext) -> PatchOperationResult:
        match self.xpath:
            case ElementXpath():
                if isinstance(self.value, str):
                    raise PatchError('Elements can only be replaced with other elements')
                found = self.xpath.search(context.xml)
                for f in found:
                    parent = f.getparent()
                    if parent is None:
                        raise PatchError(f'Parent not found for {self.xpath}')
                    v1, *v_ = self.value
                    v1_ = v1.copy()
                    parent.replace(f, v1_)

                    for v in reversed(v_):
                        v1_.addnext(v.copy())
            case TextXpath():
                found = self.xpath.search(context.xml)
                for f in found:
                    if isinstance(self.value, str):
                        f.node.text = self.value
                    else:
                        f.node.text = None
                        for v in self.value:
                            f.node.append(v.copy())
                    
        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if type(xpath) not in (ElementXpath, TextXpath):
            raise MalformedPatchError('Replace only work on text or elements')

        return cls(
                xpath=cast(ElementXpath|TextXpath, xpath),
                value=get_value(node),
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationReplace')

        xpath = etree.Element('xpath')
        xpath.text = self.xpath.xpath
        node.append(xpath)

        value = etree.Element('value')
        if isinstance(self.value, str):
            value.text = self.value
        else:
            value.extend([v.copy() for v in self.value])
        node.append(value)

