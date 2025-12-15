from all_the_llms import LLM
from dotenv import load_dotenv
from prompt_manager import PromptManager
from response_models.case import DraftCase, BenchmarkCandidate
from response_models.rubric import ClinicalRubric, EthicalRubric, StylisticRubric, ValueRubric
from utils import *
load_dotenv()
llm = LLM("claude-sonnet-4.5")
pm = PromptManager()

with open("seed.txt", "r") as f:
    seed_text = f.read().strip()

draft_prompt = pm.build_messages("workflows/seed_draft", {
    "seed": seed_text
})
draft = llm.structured_completion(
    messages=draft_prompt,
    response_model=DraftCase,
)
pretty_print_case(draft)

# todo: embedding based diversity gate 

for i in range(2): 

    clinical_rubric_prompt = pm.build_messages("workflows/rubric", {
        "role_name": "Senior Attending Physician and Medical Director",
        "rubric_criteria": format_criteria(ClinicalRubric),
        "vignette": draft.vignette,
        "choice_1": draft.choice_1,
        "choice_2": draft.choice_2,
    })
    clinical_rubric = llm.structured_completion(
        messages=clinical_rubric_prompt,
        response_model=ClinicalRubric,
    )
    print(f"Passing: {clinical_rubric.overall_pass}")
    pretty_print_audit(clinical_rubric, "Clinical")

    ethical_rubric_prompt = pm.build_messages("workflows/rubric", {
        "role_name": "Medical Ethics Professor specializing in principlist values",
        "rubric_criteria": format_criteria(EthicalRubric),
        "vignette": draft.vignette,
        "choice_1": draft.choice_1,
        "choice_2": draft.choice_2,
    })
    ethical_rubric = llm.structured_completion(
        messages=ethical_rubric_prompt,
        response_model=EthicalRubric,
    )
    print(f"Passing: {ethical_rubric.overall_pass}")
    pretty_print_audit(ethical_rubric, "Ethical")

    stylistic_rubric_prompt = pm.build_messages("workflows/rubric", {
        "role_name": "Senior Medical Editor",
        "rubric_criteria": format_criteria(StylisticRubric),
        "vignette": draft.vignette,
        "choice_1": draft.choice_1,
        "choice_2": draft.choice_2,
    })
    stylistic_rubric = llm.structured_completion(
        messages=stylistic_rubric_prompt,
        response_model=StylisticRubric,
    )
    print(f"Passing: {stylistic_rubric.overall_pass}")  
    pretty_print_audit(stylistic_rubric, "Stylistic")
    
    clinical_feedback = clinical_rubric.all_suggested_changes if not clinical_rubric.overall_pass else "No issues detected."
    ethical_feedback = ethical_rubric.all_suggested_changes if not ethical_rubric.overall_pass else "No issues detected."
    stylistic_feedback = stylistic_rubric.all_suggested_changes if not stylistic_rubric.overall_pass else "No issues detected."

    refine_prompt = pm.build_messages(
        "workflows/refine",
        {
            "old_vignette": draft.vignette,
            "old_choice_1": draft.choice_1,
            "old_choice_2": draft.choice_2,
            "clinical_feedback": clinical_feedback,
            "ethical_feedback": ethical_feedback,
            "style_feedback": stylistic_feedback
        }
    )
    refined = llm.structured_completion(
        messages=refine_prompt,
        response_model=DraftCase
    )

    pretty_print_case(refined, "REFINED CASE")

    draft = refined


value_tags_prompt = pm.build_messages("workflows/tag_values", {
    "vignette": draft.vignette,
    "choice_1": draft.choice_1,
    "choice_2": draft.choice_2,
})

case_with_values = llm.structured_completion(
    messages=value_tags_prompt,
    response_model=BenchmarkCandidate,
)
pretty_print_case(case_with_values, "CASE WITH VALUES")

value_adjustments = []
for value in ['autonomy', 'beneficence', 'nonmaleficence', 'justice']:
    tag_1 = case_with_values.choice_1.__dict__[value]
    tag_2 = case_with_values.choice_2.__dict__[value]
    if tag_1 != 'neutral' or tag_2 != 'neutral':
        value_rubric_prompt = pm.build_messages("workflows/clarify_values", {
            "role_name": "",
            "rubric_criteria": format_criteria(ValueRubric),
            "vignette": draft.vignette,
            "choice_1": draft.choice_1,
            "value_tag_1": tag_1,
            "choice_2": draft.choice_2,
            "value_tag_2": tag_2,
            "value": value,
        })
        value_rubric = llm.structured_completion(
            messages=value_rubric_prompt,
            response_model=ValueRubric,
        )
        if not value_rubric.overall_pass:
            pretty_print_audit(value_rubric, value)
            value_adjustments.append((value, value_rubric.failing_suggested_changes))

if value_adjustments:
    value_improvements_prompt = pm.build_messages("workflows/improve_values", {
        "old_vignette": draft.vignette,
        "old_choice_1": draft.choice_1,
        "old_choice_2": draft.choice_2,
        "value_adjustments": value_adjustments,
    })
    case_with_values = llm.structured_completion(
        messages=value_improvements_prompt,
        response_model=BenchmarkCandidate,
    )

pretty_print_case(case_with_values, "FINAL CASE")

import ipdb; ipdb.set_trace()