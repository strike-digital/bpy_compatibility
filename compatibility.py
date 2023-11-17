from typing import Any, Literal

from bpy.types import (
    Area,
    AssetMetaData,
    Context,
    FileSelectEntry,
    NodeSocket,
    NodeTree,
)
import bpy

# Changes accounted for:
# Active asset changed from context.asset_file_handle to context.asset
# Asset metadata changed from FileSelectEntry.asset_data to AssetRepresentation.metadata
# Active asset library name changed from asset_library_ref to asset_library_reference
# API for interacting with node tree interfaces changed
# Socket type changed from uppercase to idname
# Socket type api changed from socket.type to socket.socket_type

IS_4_0 = bpy.app.version >= (4, 0, 0)


def get_active_asset(context: Context) -> FileSelectEntry | None:
    """
    Needed for 4.0 compatibility.
    Get the currently active asset in the asset browser.
    """
    return context.asset if IS_4_0 else context.asset_file_handle


def get_asset_metadata(asset_handle: FileSelectEntry) -> AssetMetaData:
    """
    Needed for 4.0 compatibility.
    Get the metadata for the given asset representation.
    """
    return asset_handle.metadata if IS_4_0 else asset_handle.asset_data


def get_active_asset_library_name(area: Area) -> str:
    """
    Needed for 4.0 compatibility.
    Get the name of the currently active asset library
    """
    params = area.spaces.active.params
    return params.asset_library_reference if IS_4_0 else params.asset_library_ref


def get_asset_import_method(area: Area) -> str:
    """
    Needed for 4.0 compatibility.
    Get the name of the current import type
    """
    params = area.spaces.active.params
    return params.import_method if IS_4_0 else params.import_type


def get_socket_type(socket: NodeSocket) -> str:
    """
    Needed for 4.0 compatibility.
    Get the type of the given socket
    """
    return socket.socket_type if IS_4_0 else socket.type


class BpyDict(dict):
    """Used to mimic the behavior of the built in Collection Properties in Blender, which act as a
    mix of dictionaries and lists."""

    def __iter__(self):
        return iter(self.values())

    def __getitem__(self, __key: Any) -> Any:
        if isinstance(__key, int):
            return list(self.values())[__key]
        return super().__getitem__(__key)


class CompatibleNodeTree:
    """A wrapper to allow the old 3.6 node tree interface api to be used with the new 4.0 api."""
    def __init__(self, node_tree: NodeTree):
        self.node_tree = node_tree

    def __getattribute__(self, __name: str) -> Any:
        print("ho")
        return super().__getattribute__(__name)

    def interface_items(self, type: Literal["INPUT", "OUTPUT", "PANEL"]):
        items = BpyDict()
        for item in self.node_tree.interface.items_tree:
            if item.item_type == "SOCKET" and item.in_out == type:
                items[item.name] = item
        return items

    @property
    def inputs(self) -> dict[str, NodeSocket]:
        if IS_4_0:
            return self.interface_items("INPUT")
        else:
            return self.node_tree.inputs

    @property
    def outputs(self) -> dict[str, NodeSocket]:
        if IS_4_0:
            return self.interface_items("OUTPUT")
        else:
            return self.node_tree.inputs


class CompatiblePrincipledBSDF:
    """
    A wrapper for the Principled BSDF node so that it's api remains compatible with pre 3.6 versions of Blender
    """

    aliases = {
        "Subsurface": "Subsurface Weight",
        "Specular": "Specular IOR Level",
        "Sheen": "Sheen Weight",
        "Clearcoat": "Coat Weight",
        "Clearcoat Roughness": "Coat Roughness",
        "Transmission": "Weight",
        "Emission": "Emission Color",
    }
    inv_aliases = {v: k for k, v in aliases.items()}

    def __init__(self, node: bpy.types.ShaderNodeBsdfPrincipled) -> None:
        self.node = node

    def __getattribute__(self, __name: str) -> Any:
        return super().__getattribute__(__name)

    def get_socket_name(self, name: str):
        return self.aliases.get(name, name) if IS_4_0 else name

    def get_socket(self, name: str) -> NodeSocket:
        socket = self.node.inputs[self.get_socket_name(name)]
        return socket

    def get_sockets(self, inputs: bool = True) -> dict[str, NodeSocket]:
        all_sockets = self.node.inputs if inputs else self.node.outputs
        if IS_4_0:
            sockets = BpyDict()
            for socket in all_sockets:
                sockets[self.inv_aliases.get(socket.name, socket.name)] = socket
            return sockets
        return all_sockets

    @property
    def inputs(self) -> dict[str, NodeSocket]:
        return self.get_sockets(inputs=True)

    @property
    def outputs(self) -> dict[str, NodeSocket]:
        return self.get_sockets(inputs=False)
