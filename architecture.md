# TriageAI Bedtime Storyteller Architecture

This document illustrates the flow of the AI Bedtime Storyteller system, showcasing the interactions between the User, Categorizer, Storyteller, and Judge components.

## Block Diagram

```mermaid
flowchart TD
    User([User])
    Categorizer[[Categorizer (LLM)]]
    Storyteller[[Storyteller (LLM)]]
    Judge[[Judge (LLM)]]
    
    %% Initial Request Flow
    User -- "1. Story Request" --> Categorizer
    Categorizer -- "2. Determine Genre" --> Storyteller
    User -- "Original Request" --> Storyteller
    
    %% Generation and Judging Loop
    Storyteller -- "3. Generate Story Draft" --> Judge
    Judge -- "4. Evaluate (Score & Feedback)" --> JudgeDecision{Score >= 8?}
    
    %% Decision branches
    JudgeDecision -- "No (Retry limit not reached)" --> Revise[Send Feedback to Storyteller]
    Revise -. "Incorporate Feedback" .-> Storyteller
    
    JudgeDecision -- "Yes (or Max Retries)" --> Present[Present Final Draft]
    
    %% Presenting to User and User Feedback Loop
    Present --> User
    User -- "5. Accept Story" --> End([End])
    User -- "5. Request Changes (User Feedback)" --> StorytellerFeedback[User Feedback]
    StorytellerFeedback -. "Incorporate User Feedback" .-> Storyteller
```

## Components Description

1. **User**: Provides the initial bedtime story request and offers feedback on the generated story.
2. **Categorizer (LLM)**: Analyzes the user's initial request to identify the most appropriate literary genre (e.g., Fantasy, Sci-Fi, Adventure, Educational, Animal Fable, General). This allows the Storyteller to tailor its style and tone effectively.
3. **Storyteller (LLM)**: The core creative agent. It generates the story based on the user's prompt, the assigned genre, and specific guidelines ensuring the content is appropriate for ages 5-10. It is also responsible for revising the story based on feedback from either the Judge or the User.
4. **Judge (LLM)**: Acts as an expert editor. It reviews the Storyteller's draft against the original request, focusing on age-appropriateness, pacing, engagement, and vocabulary. It outputs a JSON response containing a score (1-10) and actionable critique.

## Workflow

1. **Initialization**: The user inputs a prompt (e.g., "A story about a cat who goes to space").
2. **Categorization**: The system categorizes the prompt to assign a genre.
3. **Drafting**: The Storyteller writes an initial draft.
4. **Evaluation Loop**: 
   - The Judge reviews the draft.
   - If the score is below 8, the Judge's feedback is sent back to the Storyteller for revision.
   - This loop repeats until the story scores an 8 or higher, or until a maximum number of revisions (2) is reached.
5. **Presentation & Feedback**: The finalized story is presented to the user. The user can either accept the story or provide their own feedback. If the user provides feedback, the Storyteller revises the draft incorporating the user's suggestions directly.
