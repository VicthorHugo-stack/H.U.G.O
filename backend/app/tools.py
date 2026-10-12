"""Registro central das ferramentas disponíveis para o H.U.G.O."""

from dataclasses import dataclass
from datetime import datetime
import json
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
    """Armazena, consulta e executa ferramentas registradas."""

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

        if not isinstance(name, str):
            return None

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

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Valida e executa uma ferramenta registrada."""

        tool = self.get(name)

        if tool is None:
            raise ValueError("Ferramenta não encontrada ou não autorizada.")

        if not isinstance(arguments, dict):
            raise ValueError("Os argumentos devem ser um objeto JSON.")

        if tool.requires_confirmation:
            raise PermissionError(
                "Esta ferramenta exige confirmação antes da execução."
            )

        parameters = tool.parameters
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])
        allow_additional = parameters.get(
            "additionalProperties",
            True,
        )

        if not isinstance(properties, dict):
            raise ValueError("A definição dos parâmetros é inválida.")

        if not isinstance(required, list):
            raise ValueError("A definição dos parâmetros obrigatórios é inválida.")

        unknown_arguments = set(arguments) - set(properties)

        if unknown_arguments and allow_additional is False:
            raise ValueError(
                "Argumentos não permitidos: "
                + ", ".join(sorted(unknown_arguments))
            )

        missing_arguments = [
            key for key in required
            if key not in arguments
        ]

        if missing_arguments:
            raise ValueError(
                "Argumentos obrigatórios ausentes: "
                + ", ".join(missing_arguments)
            )

        for key, value in arguments.items():
            if key not in properties:
                continue

            expected_type = properties[key].get("type")

            if expected_type == "string" and not isinstance(value, str):
                raise ValueError(f"O argumento '{key}' deve ser texto.")

            if expected_type == "object" and not isinstance(value, dict):
                raise ValueError(f"O argumento '{key}' deve ser um objeto.")

            if expected_type == "array" and not isinstance(value, list):
                raise ValueError(f"O argumento '{key}' deve ser uma lista.")

            if expected_type == "boolean" and not isinstance(value, bool):
                raise ValueError(f"O argumento '{key}' deve ser verdadeiro ou falso.")

            if expected_type == "integer" and (
                not isinstance(value, int) or isinstance(value, bool)
            ):
                raise ValueError(f"O argumento '{key}' deve ser um número inteiro.")

            if expected_type == "number" and (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                raise ValueError(f"O argumento '{key}' deve ser numérico.")

        try:
            result = tool.handler(**arguments)
        except Exception as exc:
            raise RuntimeError(
                f"Falha ao executar a ferramenta '{tool.name}'."
            ) from exc

        try:
            json.dumps(result, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "A ferramenta retornou um resultado que não pode ser "
                "convertido para JSON."
            ) from exc

        return {
            "name": tool.name,
            "result": result,
        }


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
