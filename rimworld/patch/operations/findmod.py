from dataclasses import dataclass
from typing import Self
from lxml import etree

from .. import *


@dataclass(frozen=True, kw_only=True)
class PatchOperationFindMod(PatchOperation):
    mods: list[str]
    match: PatchOperation|None
    nomatch: PatchOperation|None

    def apply(self, context: PatchContext) -> PatchOperationResult:
        matches = all(m in context.settings.active_package_names for m in self.mods)
        if matches:
            return PatchOperationBasicConditionalResult(
                    self,
                    True,
                    context.apply_operation(self.match) if self.match else None,
                    )
        return PatchOperationBasicConditionalResult(
                self,
                False,
                context.apply_operation(self.nomatch) if self.nomatch else None
                )

    @classmethod
    def from_xml(cls, patcher: Patcher, node: etree._Element) -> Self:
        mods_elt = get_element(node, 'mods')
        mods = []
        for child in mods_elt:
            if child.tag != 'li':
                continue
            mods.append(child.text or '')       
        match_elt = node.find('match')
        match = patcher.select_operation(match_elt) if match_elt is not None else None

        nomatch_elt = node.find('nomatch')
        nomatch = patcher.select_operation(nomatch_elt) if nomatch_elt is not None else None
        return cls(
                mods=mods,
                match=match,
                nomatch=nomatch,
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationFindMod')

        mods = etree.Element('mods')
        for mod in self.mods:
            li = etree.Element('li')
            li.text = mod
            mods.append(mods)
        node.append(mods)

        if self.match is not None:
            match = etree.Element('match')
            self.match.to_xml(match)
            node.append(match)
        if self.nomatch is not None:
            nomatch = etree.Element('nomatch')
            self.nomatch.to_xml(nomatch)
            node.append(nomatch)

