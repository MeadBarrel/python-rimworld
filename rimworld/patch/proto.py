from dataclasses import dataclass
from typing import Protocol, Self, Type, runtime_checkable
from lxml import etree

from rimworld.worldsettings import WorldSettings


@runtime_checkable
class PatchOperationResult(Protocol):
    operation: 'PatchOperation'
    nodes_affected: int 
    exception: Exception|None
    is_successful: bool


@runtime_checkable
class PatchOperation(Protocol):
    def apply(self, context: 'PatchContext') -> 'PatchOperationResult':
        ...



class Patcher(Protocol):
    def patch(
            self, 
            xml: etree._ElementTree, 
            patch: etree._ElementTree, 
            settings: WorldSettings) -> list[PatchOperationResult]:
        ...

    def collect_operations(
            self, 
            node: etree._Element, 
            tag: str, 
            ) -> list[PatchOperation]:
        ...

    def select_operation(
            self, 
            node: etree._Element,
            ) -> PatchOperation:
        ...

    def apply_operation(
            self, 
            xml: etree._ElementTree, 
            operation: PatchOperation,
            settings: WorldSettings,
            ) -> PatchOperationResult:
        ... 


@dataclass(frozen=True)
class PatchContext:
    xml: etree._ElementTree
    settings: WorldSettings
    patcher: 'Patcher'

    def patch(self, patch: etree._ElementTree) -> list[PatchOperationResult]:
        return self.patcher.patch(self.xml, patch, self.settings)

    def collect_operations(self, node: etree._Element, tag: str) -> list[PatchOperation]:
        return self.patcher.collect_operations(node, tag)

    def select_operation(self, node: etree._Element) -> PatchOperation:
        return self.patcher.select_operation(node)

    def apply_operation(self, operation: PatchOperation) -> PatchOperationResult:
        return self.patcher.apply_operation(self.xml, operation, self.settings)
