from hypoforge.agents.prompts import prompt_for


def critic_prompt() -> str:
    return prompt_for("critic")

