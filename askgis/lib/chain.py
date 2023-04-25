from typing import Any, Callable, Dict, List, Optional

from langchain import BasePromptTemplate, LLMChain, PromptTemplate
from langchain.chains.base import Chain
from langchain.schema import BaseLanguageModel, BaseOutputParser
from langchain.tools import BaseTool
from qgis.core import QgsProcessingFeedback

from askgis.lib.context import Context
from askgis.lib.executor import (
    Action,
    Executor,
    action_functions,
    get_prompt_functions,
    to_action,
)


class PythonCodeActionParser(BaseOutputParser):
    def parse(self, text: str) -> Any:
        action = to_action(text)
        return text, action

    def get_format_instructions(self) -> str:
        return "Do not respond with anything other than the Python code. Do not include comments or empty lines."


PROMPT = '''
{functions}

def func1() -> Action:
    """
    Given these layers:
    * buildings_fasdff3234 (also known as Buildings, has attributes year_of_construction (also known as Year of construction, is a number), type (also known as Type, possible values are residential, industrial, commercial))
    * roads_fa4123 (also known as Roads, has attributes type (also known as Type, possible values are small, large, highway), width (also known as Width, is a number))

    Perform this action:
    Select buildings close to highways
    """

    return select(intersection(get_layer('buildings_fasdff3234'), buffer(filter(get_layer('roads_fa4123'), 'type', 'highway'), 500)))

def func2() -> Action:
    """
    Given these layers:
    {layers}

    Perform this action:
    {question}
    """

    return
'''


class GISChain(Chain):
    llm: BaseLanguageModel
    prompt: BasePromptTemplate
    context: Context
    feedback: Optional[QgsProcessingFeedback]
    code_callback: Optional[Callable[[str], None]]
    prompt_callback: Optional[Callable[[str], None]]
    action_callback: Optional[Callable[[Action], None]]
    input_key: str = "question"  #: :meta private:
    output_key: str = "answer"  #: :meta private:

    def __init__(self, context: Context, llm: BaseLanguageModel, **data: Any):
        prompt = PromptTemplate(
            input_variables=["question"],
            template=PROMPT,
            output_parser=PythonCodeActionParser(),
            partial_variables={
                "layers": "\n".join(layer.prompt for layer in context.layers),
                "functions": "\n".join(get_prompt_functions()).format(
                    layer_names=", ".join(layer.name for layer in context.layers)
                ),
            },
        )
        super().__init__(**data, context=context, prompt=prompt, llm=llm)

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    def _call(self, inputs: Dict[str, str]) -> Dict[str, str]:
        if self.prompt_callback:
            self.prompt_callback(
                self.prompt.format(question=inputs[self.input_key]).strip()
            )

        llm_executor = LLMChain(
            prompt=self.prompt, llm=self.llm, callback_manager=self.callback_manager
        )
        self.callback_manager.on_text(inputs[self.input_key], verbose=self.verbose)
        text = llm_executor.predict(question=inputs[self.input_key])
        code, action = self.prompt.output_parser.parse_with_prompt(
            text, self.prompt.format_prompt(question=inputs[self.input_key])
        )
        if self.code_callback:
            self.code_callback(code)  # type: ignore
        if self.action_callback:
            self.action_callback(action)
        executor = Executor(self.context.project, self.feedback)
        result = executor.execute(action)
        return {self.output_key: result}


class GISTool(BaseTool):
    name = "GIS"
    description = f"""
Useful to act on the GIS data. Input should start with a
command ({', '.join(a.title() for a in action_functions.keys())})", followed by a free form description of what to do. Prefer this tool when asked questions about locations, geography, etc.
""".replace(
        "\n", " "
    ).strip()

    context: Context
    llm: BaseLanguageModel
    feedback: Optional[QgsProcessingFeedback]
    code_callback: Optional[Callable[[str], None]]
    prompt_callback: Optional[Callable[[str], None]]
    action_callback: Optional[Callable[[Action], None]]

    def _run(self, tool_input: str) -> str:
        chain = GISChain(
            context=self.context,
            llm=self.llm,
            callback_manager=self.callback_manager,
            feedback=self.feedback,
            code_callback=self.code_callback,
            prompt_callback=self.prompt_callback,
            action_callback=self.action_callback,
        )
        return chain.run(tool_input)

    async def _arun(self, tool_input: str) -> str:
        raise NotImplementedError("async version is not implemented")
