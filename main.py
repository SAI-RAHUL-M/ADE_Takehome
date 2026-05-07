import os
import json
import openai
from typing import List, Dict, Tuple

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

If I had two more hours, I would implement an interactive Web UI (using Streamlit or Gradio) to make the storytelling experience more engaging for children, potentially integrating an AI image generator to provide illustrations for each story segment. I would also add a "Memory" component to retain context across multiple storytelling sessions, allowing for recurring characters and long-term world-building. Finally, I'd implement structured logging and LangSmith tracing to better evaluate the Judge's effectiveness and track prompt performance over time.
"""

def call_model(messages: List[Dict[str, str]], max_tokens: int = 3000, temperature: float = 0.7) -> str:
    """
    Calls the OpenAI API. Supports both older (openai<1.0.0) and newer (openai>=1.0.0)
    SDK versions to ensure compatibility regardless of the local environment.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Please set it before running.")
    
    # Attempt to use the newer OpenAI client (openai >= 1.0.0)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages, # type: ignore
            stream=False,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
    except ImportError:
        # Fallback to the older OpenAI API syntax (openai < 1.0.0)
        openai.api_key = api_key
        resp = openai.ChatCompletion.create( # type: ignore
            model="gpt-3.5-turbo",
            messages=messages,
            stream=False,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message["content"] # type: ignore


def categorize_request(user_input: str) -> str:
    """Categorizes the user's request into a literary genre."""
    system_prompt = (
        "You are an expert children's story categorizer. "
        "Categorize the following story request into one of these genres: "
        "Fantasy, Sci-Fi, Adventure, Educational, Animal Fable, or General. "
        "Only reply with the genre name, nothing else."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    return call_model(messages, max_tokens=10, temperature=0.1).strip()


def generate_story(user_input: str, genre: str, previous_draft: str = "", judge_feedback: str = "", user_feedback: str = "") -> str:
    """Generates or revises the story based on the prompts and feedback."""
    system_prompt = (
        f"You are a master storyteller for children ages 5 to 10. "
        f"Your genre is {genre}. Create a captivating, age-appropriate story with a clear beginning, middle, and end, "
        f"and a positive or educational underlying message. Keep the language simple but engaging."
    )
    
    if not previous_draft:
        user_prompt = f"Write a story based on this request: {user_input}"
    elif judge_feedback:
        user_prompt = (
            f"Here was your previous draft:\n\n{previous_draft}\n\n"
            f"An expert judge provided this feedback: {judge_feedback}\n\n"
            f"Please rewrite and improve the story based on this feedback, while still fulfilling the original request: {user_input}"
        )
    elif user_feedback:
        user_prompt = (
            f"Here was your previous draft:\n\n{previous_draft}\n\n"
            f"The reader provided this feedback: {user_feedback}\n\n"
            f"Please revise the story to incorporate their feedback. Original request: {user_input}"
        )
    else:
        user_prompt = f"Write a story based on this request: {user_input}"
        
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return call_model(messages, max_tokens=2000, temperature=0.7)


def judge_story(story: str, user_input: str) -> Dict:
    """Evaluates the story draft and provides a score and actionable feedback."""
    system_prompt = (
        "You are an expert editor and judge for children's literature (ages 5-10). "
        "Evaluate the provided story draft based on the original request. "
        "Consider age-appropriateness, pacing, engagement, vocabulary, and whether it fulfills the request. "
        "Provide your response in strictly valid JSON format with two keys: "
        "'score' (an integer from 1 to 10) and 'feedback' (a string with specific, actionable critique for the storyteller to improve the story). "
        "Do not include any markdown formatting like ```json in the output, just the raw JSON object."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Original Request: {user_input}\n\nStory Draft:\n{story}"}
    ]
    
    response_text = call_model(messages, max_tokens=500, temperature=0.2)
    
    try:
        # Clean up possible markdown artifacts from the model's response
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_text)
        return result
    except json.JSONDecodeError:
        # Fallback in case the model fails to return valid JSON
        return {"score": 10, "feedback": "Failed to parse judge's feedback. Moving forward with the story as is."}


def storytelling_pipeline(user_input: str) -> Tuple[str, str]:
    """Manages the generation, evaluation, and revision loop for the story."""
    print(f"\n[System] Categorizing request...")
    genre = categorize_request(user_input)
    print(f"[System] Genre identified: {genre}")
    
    draft = ""
    feedback = ""
    max_revisions = 2
    
    for iteration in range(max_revisions + 1):
        if iteration == 0:
            print("[System] Generating initial story draft...")
        else:
            print(f"[System] Revising story based on judge's feedback (Iteration {iteration})...")
            
        draft = generate_story(user_input, genre, previous_draft=draft, judge_feedback=feedback)
        
        print("[System] Judging story...")
        judge_result = judge_story(draft, user_input)
        score = judge_result.get("score", 0)
        feedback = judge_result.get("feedback", "")
        
        print(f"[Judge] Score: {score}/10")
        print(f"[Judge] Feedback: {feedback}")
        
        if score >= 8:
            print("[System] Story passed the judge's quality threshold!")
            break
        elif iteration < max_revisions:
            print("[System] Story needs improvement. Sending back to storyteller...")
        else:
            print("[System] Max revisions reached. Presenting the final draft.")
            
    return draft, genre


def main():
    print("Welcome to the AI Bedtime Storyteller!")
    user_input = input("What kind of story do you want to hear? ")
    
    story, genre = storytelling_pipeline(user_input)
    
    while True:
        print("\n" + "="*50)
        print("HERE IS YOUR STORY:")
        print("="*50 + "\n")
        print(story)
        print("\n" + "="*50)
        
        print("\nWould you like to make any changes to the story?")
        print("1. Yes, I have feedback for changes.")
        print("2. No, I love it! (Exit)")
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == '1':
            user_feedback = input("\nWhat would you like to change? ")
            print("\n[System] Generating revised story based on your feedback...")
            # We bypass the full judging pipeline here to provide a quick response to the user's specific request
            story = generate_story(user_input, genre, previous_draft=story, user_feedback=user_feedback)
        else:
            print("\nSweet dreams! Thanks for using the AI Bedtime Storyteller.")
            break


if __name__ == "__main__":
    main()