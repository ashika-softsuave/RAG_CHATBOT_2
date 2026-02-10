def generate_followup(answer: str) -> str:
    """
     Generates a follow-up only within SoftSuave document scope.
    """
    return (
        f"{answer}\n\n"
        "ℹ️ If you have another question related to our company,please ask."
    )
