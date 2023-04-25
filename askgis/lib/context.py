from dataclasses import dataclass
from typing import Dict, List, Optional

from qgis.core import QgsCategorizedSymbolRenderer, QgsField, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QVariant


@dataclass
class ContextField:
    id: str
    name: str
    type: QVariant.Type
    values: Optional[Dict[str, str]] = None

    @property
    def prompt(self) -> str:
        if self.values:
            # figure out a prompt that can take the (often more human-readable) values in the dict
            type_prompt = "possible values are " + ", ".join(self.values.keys())
        elif self.type == QVariant.String:
            type_prompt = "is a string"
        elif self.type in (
            QVariant.Int,
            QVariant.UInt,
            QVariant.LongLong,
            QVariant.ULongLong,
            QVariant.Double,
        ):
            type_prompt = "is a number"
        elif self.type == QVariant.Bool:
            type_prompt = "is a boolean"
        else:
            raise ValueError("Unhandled field type")
        if self.id.lower() == self.name.lower():
            return f"{self.id} ({type_prompt})"
        else:
            return f"{self.id} (also known as {self.name}, {type_prompt})"


@dataclass
class ContextLayer:
    id: str
    name: str
    fields: List[ContextField]

    @property
    def prompt(self) -> str:
        fields = ", ".join(field.prompt for field in self.fields)
        #        return f"* {self.id} (also known as {self.name}, has attributes {fields})"
        return f"* {self.name} (has attributes {fields})"


@dataclass
class Context:
    layers: List[ContextLayer]
    project: QgsProject


def compute_context(project: QgsProject) -> Context:
    def process_layer(layer: QgsVectorLayer) -> ContextLayer:
        def process_field(field: QgsField) -> ContextField:
            field = ContextField(
                id=field.name(), name=field.displayName(), type=field.type()
            )

            renderer = layer.renderer()
            if (
                isinstance(renderer, QgsCategorizedSymbolRenderer)
                and renderer.classAttribute() == field.name
            ):
                field.values = {
                    field: cat.label()
                    for cat in renderer.categories()
                    if not (isinstance(cat.value(), QVariant) and cat.value().isNull())
                    for field in (
                        cat.value() if isinstance(cat.value(), list) else [cat.value()]
                    )
                }

            return field

        return ContextLayer(
            id=layer.id(),
            name=layer.name(),
            fields=[process_field(field) for field in layer.fields().toList()],
        )

    ctx = Context(
        project=project,
        layers=[
            process_layer(layer)
            for layer in project.mapLayers().values()
            if isinstance(layer, QgsVectorLayer)
        ],
    )

    return ctx
