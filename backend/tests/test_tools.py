import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.tools import ToolDefinition, ToolRegistry


def test_register_tool():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="example",
        description="Ferramenta de exemplo.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "ok",
    )

    registry.register(tool)

    assert registry.get("example") is tool


def test_get_nonexistent_tool():
    registry = ToolRegistry()

    assert registry.get("inexistente") is None


def test_reject_duplicate_tool_name():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="example",
        description="Ferramenta de exemplo.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "ok",
    )
    registry.register(tool)

    with pytest.raises(ValueError, match="já está registrada"):
        registry.register(tool)


def test_reject_empty_tool_name():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="   ",
        description="Ferramenta sem nome.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "ok",
    )

    with pytest.raises(ValueError, match="nome da ferramenta"):
        registry.register(tool)


def test_list_registered_tools():
    registry = ToolRegistry()
    first = ToolDefinition(
        name="first",
        description="Primeira ferramenta.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "first",
    )
    second = ToolDefinition(
        name="second",
        description="Segunda ferramenta.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "second",
    )

    registry.register(first)
    registry.register(second)

    assert registry.list_tools() == [first, second]


def test_describe_tools_does_not_expose_handler():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="example",
        description="Ferramenta de exemplo.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "ok",
        requires_confirmation=True,
    )
    registry.register(tool)

    assert registry.describe_tools() == [
        {
            "name": "example",
            "description": "Ferramenta de exemplo.",
            "parameters": {"type": "object", "properties": {}},
            "requires_confirmation": True,
        }
    ]

    
def test_reject_tool_name_with_surrounding_spaces():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name=" example ",
        description="Ferramenta de exemplo.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "ok",
    )

    with pytest.raises(ValueError, match="espaços"):
        registry.register(tool)


def test_reject_duplicate_name_ignoring_case():
    registry = ToolRegistry()

    first = ToolDefinition(
        name="example",
        description="Primeira ferramenta.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "first",
    )
    second = ToolDefinition(
        name="EXAMPLE",
        description="Segunda ferramenta.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "second",
    )

    registry.register(first)

    with pytest.raises(ValueError, match="já está registrada"):
        registry.register(second)


def test_get_tool_ignores_case_and_surrounding_spaces():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="example",
        description="Ferramenta de exemplo.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "ok",
    )

    registry.register(tool)

    assert registry.get("EXAMPLE") is tool
    assert registry.get(" example ") is tool


def test_reject_empty_tool_description():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="example",
        description="   ",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "ok",
    )

    with pytest.raises(ValueError, match="descrição"):
        registry.register(tool)


def test_reject_non_dict_parameters():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="example",
        description="Ferramenta de exemplo.",
        parameters=[],
        handler=lambda: "ok",
    )

    with pytest.raises(ValueError, match="dicionário"):
        registry.register(tool)


def test_reject_non_callable_handler():
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="example",
        description="Ferramenta de exemplo.",
        parameters={"type": "object", "properties": {}},
        handler="não é uma função",
    )

    with pytest.raises(ValueError, match="executável"):
        registry.register(tool)


"""Registro central das ferramentas disponíveis para o H.U.G.O."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class ToolDefinition:
    """Define os metadados e o executor de uma ferramenta."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]
    requires_confirmation: bool = False


class ToolRegistry:
    """Armazena e consulta as ferramentas registradas."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Valida e registra uma ferramenta com nome único."""

        name = tool.name.strip()

        if not name:
            raise ValueError("O nome da ferramenta é obrigatório.")

        if name != tool.name:
            raise ValueError(
                "O nome da ferramenta não pode começar ou terminar "
                "com espaços."
            )

        if not name.replace("_", "").isalnum():
            raise ValueError(
                "O nome da ferramenta deve conter apenas letras, "
                "números e sublinhados."
            )

        if not tool.description.strip():
            raise ValueError("A descrição da ferramenta é obrigatória.")

        if not isinstance(tool.parameters, dict):
            raise ValueError(
                "Os parâmetros da ferramenta devem ser um dicionário."
            )

        if not callable(tool.handler):
            raise ValueError(
                "O executor da ferramenta precisa ser executável."
            )

        if not isinstance(tool.requires_confirmation, bool):
            raise ValueError(
                "requires_confirmation deve ser True ou False."
            )

        normalized_name = name.casefold()

        if any(
            registered_name.casefold() == normalized_name
            for registered_name in self._tools
        ):
            raise ValueError(
                f"A ferramenta '{name}' já está registrada."
            )

        self._tools[name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Retorna uma ferramenta pelo nome, sem diferenciar maiúsculas."""

        normalized_name = name.strip().casefold()

        for registered_name, tool in self._tools.items():
            if registered_name.casefold() == normalized_name:
                return tool

        return None

    def list_tools(self) -> list[ToolDefinition]:
        """Retorna as ferramentas registradas."""

        return list(self._tools.values())

    def describe_tools(self) -> list[dict[str, Any]]:
        """Retorna descrições sem expor os executores."""

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "requires_confirmation": tool.requires_confirmation,
            }
            for tool in self._tools.values()
        ]


def get_current_datetime() -> dict[str, str]:
    """Retorna a data e hora atuais no fuso de São Paulo."""

    timezone_name = "America/Sao_Paulo"

    try:
        timezone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise RuntimeError(
            f"Não foi possível carregar o fuso horário {timezone_name}."
        ) from exc

    current_time = datetime.now(timezone)

    return {
        "datetime": current_time.isoformat(),
        "timezone": timezone_name,
    }


tool_registry = ToolRegistry()

tool_registry.register(
    ToolDefinition(
        name="get_current_datetime",
        description=(
            "Consulta a data e a hora atuais no fuso de São Paulo. "
            "Não altera dados nem executa ações externas."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        handler=get_current_datetime,
        requires_confirmation=False,
    )
)

def test_datetime_tool_returns_current_date_and_time():
    from datetime import datetime
    from app.tools import get_current_datetime

    result = get_current_datetime()

    assert isinstance(result, dict)
    assert "datetime" in result
    assert "timezone" in result
    assert datetime.fromisoformat(result["datetime"])
    assert isinstance(result["timezone"], str)
    assert result["timezone"] == "America/Sao_Paulo"
