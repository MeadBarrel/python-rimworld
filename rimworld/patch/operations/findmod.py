""" Provides PatchOperationFindMod"""

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.patch.proto import (PatchContext, Patcher, PatchOperation,
                                  PatchOperationResult)
from rimworld.patch.result import PatchOperationBasicConditionalResult


@dataclass(frozen=True, kw_only=True)
class PatchOperationFindMod(PatchOperation):
    """PatchOperationAdd

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationFindMod
    """

    mods: list[str]
    match: PatchOperation | None
    nomatch: PatchOperation | None

    def __call__(
        self, xml: etree._ElementTree, context: PatchContext
    ) -> PatchOperationResult:
        matches = all(m in context.active_package_names for m in self.mods)
        if matches:
            return PatchOperationBasicConditionalResult(
                self,
                True,
                self.match(xml, context) if self.match else None,
            )
        return PatchOperationBasicConditionalResult(
            self,
            False,
            self.nomatch(xml, context) if self.nomatch else None,
        )

    @classmethod
    def from_xml(cls, get_operation: Patcher, node: etree._Element) -> Self:
        """Deserialize from xml"""
        mods_elt = node.find("mods")
        if mods_elt is None:
            mods_elt = etree.Element("mods")
        mods = []
        for child in mods_elt:
            if child.tag != "li":
                continue
            mods.append(child.text or "")
        match_elt = node.find("match")
        match = get_operation(match_elt) if match_elt is not None else None

        nomatch_elt = node.find("nomatch")
        nomatch = get_operation(nomatch_elt) if nomatch_elt is not None else None
        return cls(
            mods=mods,
            match=match,
            nomatch=nomatch,
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationFindMod")

        mods = etree.Element("mods")
        for mod in self.mods:
            li = etree.Element("li")
            li.text = mod
            mods.append(mods)
        node.append(mods)

        if self.match is not None:
            match = etree.Element("match")
            self.match.to_xml(match)
            node.append(match)
        if self.nomatch is not None:
            nomatch = etree.Element("nomatch")
            self.nomatch.to_xml(nomatch)
            node.append(nomatch)
