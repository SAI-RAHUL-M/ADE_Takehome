import os
import json
import openai
from typing import List, Dict, Tuple

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

If I had two more hours, I would implement a Web UI (using Streamlit or Gradio) for a more interactive experience, complete with AI-generated DALL-E illustrations for each "Act" of the story. 
I would also add a "Memory" abstraction to allow recurring characters across multiple storytelling sessions, and I would integrate LangSmith to trace the multi-agent token usage and evaluate the Judge's strictness over time.
"""

def call_model(messages: List[Dict[str, str]], max_tokens: int = 2000, temperature: float = 0.7) -> str:
    """
    Calls the OpenAI API using gpt-3.5-turbo.
    Supports both older (openai<1.0.0) and newer (openai>=1.0.0) SDK versions.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Please set it before running.")
    
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
        openai.api_key = api_key
        resp = openai.ChatCompletion.create( # type: ignore
            model="gpt-3.5-turbo",
            messages=messages,
            stream=False,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message["content"] # type: ignore


# ==========================================
# AGENT 1: The Categorizer
# ==========================================
def categorize_request(user_input: str) -> str:
    """Analyzes the request to determine genre, tone, and a core educational value."""
    system_prompt = (
        "You are an expert children's literature analyst. "
        "Analyze the user's story request and determine the best approach for a 5-10 year old audience. "
        "Provide exactly three things in the following format:\n"
        "Genre: [e.g., Sci-Fi, Fantasy, Fable]\n"
        "Tone: [e.g., Whimsical, Calming, Adventurous]\n"
        "Core Value: [e.g., Courage, Sharing, Curiosity]"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Request: {user_input}"}
    ]
    return call_model(messages, max_tokens=150, temperature=0.3).strip()


# ==========================================
# AGENT 2: The Arc Planner
# ==========================================
def plan_story_arc(user_input: str, category_details: str) -> str:
    """Creates a structured 3-act outline to ensure the story has a satisfying narrative arc."""
    system_prompt = (
        "You are a master story outliner for children's books. "
        "Based on the user's request and the provided literary analysis, create a compelling 3-act story arc. "
        "Ages: 5 to 10. "
        "Format your response EXACTLY like this:\n\n"
        "Characters: [List the main characters]\n"
        "Setting: [Describe the world]\n"
        "Act 1 (Introduction): [The setup and inciting incident]\n"
        "Act 2 (Conflict): [The challenge or adventure the characters face]\n"
        "Act 3 (Resolution): [How it resolves and the moral learned]"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User Request: {user_input}\n\nAnalysis:\n{category_details}"}
    ]
    return call_model(messages, max_tokens=400, temperature=0.7).strip()


# ==========================================
# AGENT 3: The Storyteller
# ==========================================
def generate_story(user_input: str, category_details: str, arc: str, previous_draft: str = "", judge_feedback: str = "", user_feedback: str = "") -> str:
    """Drafts or revises the story based on the planned arc and feedback."""
    system_prompt = (
        f"You are a beloved, imaginative storyteller for children ages 5 to 10. "
        f"You are writing a story based on the following framework:\n\n"
        f"--- ANALYSIS ---\n{category_details}\n\n"
        f"--- STORY ARC ---\n{arc}\n\n"
        f"Follow the arc closely. Use engaging, sensory language suitable for children. Ensure clear paragraph breaks and excellent pacing."
    )
    
    if judge_feedback:
        user_prompt = (
            f"Here was your previous draft:\n\n{previous_draft}\n\n"
            f"An expert editor provided this critical feedback: {judge_feedback}\n\n"
            f"Please rewrite and improve the story based on this feedback, making it even better for the reader."
        )
    elif user_feedback:
        user_prompt = (
            f"Here was your previous draft:\n\n{previous_draft}\n\n"
            f"The reader wants to make a change! They said: '{user_feedback}'\n\n"
            f"Please revise the story to creatively incorporate their request."
        )
    else:
        user_prompt = f"Write the story! The original user request was: {user_input}"
        
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return call_model(messages, max_tokens=800, temperature=0.8)


# ==========================================
# AGENT 4: The Judge
# ==========================================
def judge_story(story: str, user_input: str, arc: str) -> Dict:
    """Evaluates the draft for quality, pacing, age-appropriateness, and arc fulfillment."""
    system_prompt = (
        "You are an expert editor and judge for children's literature (ages 5-10). "
        "Evaluate the provided story draft. Does it follow the intended story arc? Is it age-appropriate? Is it engaging? "
        "Does it fulfill the user's original request?\n\n"
        "You MUST respond in strictly valid JSON format with exactly two keys: "
        "'score' (an integer from 1 to 10) and 'feedback' (a string with specific, actionable critique). "
        "Do not include markdown blocks like ```json."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Original Request: {user_input}\n\nIntended Arc:\n{arc}\n\nStory Draft:\n{story}"}
    ]
    
    response_text = call_model(messages, max_tokens=500, temperature=0.2)
    
    try:
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        return {"score": 10, "feedback": "Failed to parse judge's feedback. Assuming it is good enough to proceed."}


# ==========================================
# PIPELINE ORCHESTRATION
# ==========================================
def storytelling_pipeline(user_input: str) -> Tuple[str, str, str]:
    print(f"\n[🪄 Magic Hat] Analyzing your request to find the perfect mix of wonder and adventure...")
    print(f"(Note: The 4-agent pipeline may take 30-60 seconds to complete. Magic takes time! ✨)")
    category_details = categorize_request(user_input)
    print(f"[🪄  Magic Hat] Aha! Here is the secret formula:\n{category_details}\n")
    
    print(f"[📜 Arc Planner] Waking up the master architect to sketch out the 3-act storyline...")
    arc = plan_story_arc(user_input, category_details)
    print(f"[📜 Arc Planner] The blueprint is ready!\n")
    
    draft = ""
    feedback = ""
    max_revisions = 1
    
    for iteration in range(max_revisions + 1):
        if iteration == 0:
            print("[🖋️  Storyteller] Dipping the quill in invisible ink to draft the story...")
        else:
            print(f"[🖋️  Storyteller] Grumbling slightly, the Storyteller is revising the draft (Revision {iteration}/{max_revisions})...")
            
        draft = generate_story(user_input, category_details, arc, previous_draft=draft, judge_feedback=feedback)
        
        print("[🧐 The Judge] Putting on reading glasses to rigorously evaluate the story...")
        judge_result = judge_story(draft, user_input, arc)
        score = judge_result.get("score", 0)
        feedback = judge_result.get("feedback", "")
        
        print(f"[🧐 The Judge] Score: {score}/10")
        print(f"[🧐 The Judge] Critique: {feedback}")
        
        if score >= 8:
            print("[✨ System] The Judge smiled! The story is approved.")
            break
        elif iteration < max_revisions:
            print("[✨ System] The Judge wants it to be even more magical. Sending it back for a rewrite...")
        else:
            print("[✨ System] Maximum revisions reached. Polishing the final masterpiece.")
            
    return draft, category_details, arc


def main():
    print("========================================")
    print(" Welcome to the AI Bedtime Storyteller! ")
    print("========================================")
    user_input = input("What kind of story do you want to hear today? ")
    
    story, category_details, arc = storytelling_pipeline(user_input)
    
    while True:
        print("\n" + "="*50)
        print("HERE IS YOUR STORY:")
        print("="*50 + "\n")
        print(story)
        print("\n" + "="*50)
        
        print("\nWould you like to make any changes to the story?")
        print("1. Yes, I have feedback for changes!")
        print("2. No, it's perfect! (Exit)")
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == '1':
            user_feedback = input("\nWhat would you like to change? (e.g., 'Make the dragon friendlier', 'Add a magical sword'): ")
            print("\n[🖋️  Storyteller] *Sighs dramatically*, rolls up sleeves, and gets back to work...")
            # Generate a rapid revision incorporating user feedback without looping back to the Judge
            story = generate_story(user_input, category_details, arc, previous_draft=story, user_feedback=user_feedback)
        else:
            print("\nSweet dreams! Thanks for reading with the AI Bedtime Storyteller.")
            break

if __name__ == "__main__":
    main()