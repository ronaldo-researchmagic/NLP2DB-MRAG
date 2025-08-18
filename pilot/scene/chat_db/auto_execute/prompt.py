import json
import importlib
from pilot.prompts.prompt_new import PromptTemplate
from pilot.configs.config import Config
from pilot.scene.base import ChatScene
from pilot.scene.chat_db.auto_execute.out_parser import DbChatOutputParser, SqlAction
from pilot.common.schema import SeparatorStyle
from pilot.language.prompt_language import get_prompt_template

CFG = Config()

PROMPT_SCENE_DEFINE = get_prompt_template("scene_define")


_DEFAULT_TEMPLATE = f"""
{get_prompt_template("sql_expert_role")}
{get_prompt_template("sql_limit_results")}
{get_prompt_template("sql_use_few_tables")}
{get_prompt_template("sql_data_validation")}
{get_prompt_template("sql_schema_attention")}

"""

PROMPT_SUFFIX = f"""{get_prompt_template("sql_tables_prefix")}
{{table_info}}

{get_prompt_template("sql_question_prefix")} {{input}}

"""

PROMPT_RESPONSE = f"""{get_prompt_template("sql_response_format")}
{{response}}

{get_prompt_template("sql_json_parsing")}
"""

RESPONSE_FORMAT = {
    "thoughts": {
        "reasoning": get_prompt_template("sql_thoughts_reasoning"),
        "speak": get_prompt_template("sql_thoughts_speak"),
    },
    "sql": get_prompt_template("sql_query_to_run"),
}

RESPONSE_FORMAT_SIMPLE = {
    "thoughts": get_prompt_template("sql_thoughts_speak"),
    "sql": get_prompt_template("sql_query_to_run"),
}

PROMPT_SEP = SeparatorStyle.SINGLE.value

PROMPT_NEED_NEED_STREAM_OUT = False

prompt = PromptTemplate(
    template_scene=ChatScene.ChatWithDbExecute.value,
    input_variables=["input", "table_info", "dialect", "top_k", "response"],
    response_format=json.dumps(RESPONSE_FORMAT_SIMPLE, indent=4),
    template_define=PROMPT_SCENE_DEFINE,
    template=_DEFAULT_TEMPLATE + PROMPT_SUFFIX + PROMPT_RESPONSE,
    stream_out=PROMPT_NEED_NEED_STREAM_OUT,
    output_parser=DbChatOutputParser(
        sep=PROMPT_SEP, is_stream_out=PROMPT_NEED_NEED_STREAM_OUT
    ),
)
CFG.prompt_templates.update({prompt.template_scene: prompt})
