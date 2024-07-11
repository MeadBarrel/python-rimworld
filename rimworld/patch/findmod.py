from dataclasses import dataclass
from typing import Self
from lxml import etree
from ._base import *
from ._result import PatchOperationBasicConditionalResult



@dataclass(frozen=True)
class PatchOperationFindMod(PatchOperation):
    mods: list[str]
    match: PatchOperation|None
    nomatch: PatchOperation|None

    def apply(self, xml: etree._ElementTree, patcher: Patcher) -> PatchOperationBasicConditionalResult:
        matches = all(m in patcher.active_package_names for m in self.mods)
        if matches:
            return PatchOperationBasicConditionalResult(
                    self,
                    True,
                    patcher.apply(xml, self.match) if self.match else None
                    )
        return PatchOperationBasicConditionalResult(
                self,
                False,
                patcher.apply(xml, self.nomatch) if self.nomatch else None
                )

    @classmethod
    def from_xml(cls, node: etree._Element, patcher: Patcher) -> Self:
        mods_elt = get_element(node, 'mods')
        mods = []
        for child in mods_elt:
            if child.tag != 'li':
                raise MalformedPatchError('<mods> node in PatchOperationFindMod should only contain <li> elements')
            mods.append(child.text or '')       
        match_elt = node.find('match')
        match = patcher.select_operation(match_elt) if match_elt is not None else None

        nomatch_elt = node.find('nomatch')
        nomatch = patcher.select_operation(nomatch_elt) if nomatch_elt is not None else None
        return cls(
                PatchOperationMeta.from_xml(node),
                mods, 
                match, 
                nomatch
                )
