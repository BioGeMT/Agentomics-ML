import os
import dotenv
from smolagents import LiteLLMModel, ToolCallingAgent
from tools.bash import get_bash_tool
from utils.models import MODELS
from utils.create_user import create_new_user_and_rundir
from run_logging.wandb import setup_logging
from run_logging.evaluate_log_run import evaluate_log_run
from prompts.prompts_utils import load_prompts


dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") #Openrouter models need their OPENROUTER API key
wandb_key = os.getenv("WANDB_API_KEY")

agent_id = create_new_user_and_rundir()
tools = [get_bash_tool(agent_id, 60*5)]

config = {
    "agent_id" : agent_id,
    "model" : MODELS.GPT4o,
    "temperature" : 1,
    "max_steps" : 30,
    "dataset" : "human_non_tata_promoters",
    "tags" : ["testing"],
    "tools" : [tool.name for tool in tools],
    "prompt" : "toolcalling_agent.yaml",
}

setup_logging(config, api_key=wandb_key)

model = LiteLLMModel(
    model_id=config['model'], 
    api_key=api_key, 
    temperature=config["temperature"],
)

agent = ToolCallingAgent(
    tools=tools,
    model=model,
    add_base_tools=False,
    max_steps=config["max_steps"],
    prompt_templates=load_prompts(config["prompt"]),
)

user_prompt = f"""
You are using a linux system.
You have access to CPU only, no GPU.
You can only work in /workspace/runs/{config['agent_id']} directory.
Create a new conda environment called {config['agent_id']}_env (run the installation in non-verbose mode). 
Use this environment to install any packages you need (use non-verbose mode for installations).
Write all your python scripts in files. 
Run all scripts in this environment.
Your final output should be inference.py script, located in the workspace folder (/workspace/runs/{config['agent_id']}/inference.py). 
This script will be separated from the training script and only load the already trained model and run inference.
Any path inside the inference.py script should be absolute (eg. /workspace/runs/{config['agent_id']}/model.pth).
The script will be taking the following named arguments:
    --input (an input file path, file is of the same format as your training data (except the label column))
    --output (the output file path, this file should be a one column csv file with the predictions, the column name should be 'prediction')

Create a prototype model, with only few training steps, no need to optimize it for performance.

Look into the workspace/datasets/{config['dataset']} folder and create a ML classifier using files in there.
Use the ..._train.csv as training data.
Use the ..._test.csv as testing data.
Run all bash commands and python command in a way that prints the least possible amount of tokens into the console.

Column descriptions:
sequence: DNA sequence to be classified, alphabet: A, C, G, T, N
Make sure to tokenize for all characters from the alphabet.

class: 1 if the promoter is a non-TATA promoter, 0 otherwise
"""

agent.run(user_prompt)
evaluate_log_run(config)
