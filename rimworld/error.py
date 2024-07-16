""" Exceptions used by the library """


class DifferentRootsError(Exception):
    """
    Exception raised when attempting to merge XML trees with different root elements.
    """


class MalformedPatchError(Exception):
    """
    Raised when a patch is malformed
    """


class PatchError(Exception):
    """
    Raised when a critical error happens during patching
    """


class PatchingUnsuccessful(Exception):
    """
    Used in PatchOperationResult when formally no error happens but
    it would be printed in red in rimworld log
    """


class NoNodesFound(PatchingUnsuccessful):
    """No nodes were found during xpath search"""
