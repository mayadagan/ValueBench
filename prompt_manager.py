import os
import yaml
from jinja2 import Environment, FileSystemLoader

class PromptManager:
    def __init__(self, prompt_dir="prompts"):
        # Tell Jinja2 to look for templates starting inside the 'prompts' folder
        self.env = Environment(loader=FileSystemLoader(prompt_dir))
    
    def build(self, prompt_path, variables):
        try:
            # Load the raw YAML file as a text template
            template = self.env.get_template(prompt_path)
            
            # Replace {{ variable }} with data and runs {% include %}
            # Result is a string that looks like valid YAML.
            rendered_yaml = template.render(**variables)
            
            # Parse the rendered YAML string into a real messages dictionary
            config = yaml.safe_load(rendered_yaml)
            return config
            
        except Exception as e:
            print(f"❌ Error building prompt: {e}")
            print(f"Failed YAML:\n{rendered_yaml}") 
            return None