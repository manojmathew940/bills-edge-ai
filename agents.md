# Agents Instructions

## Project Overview
This repository contains the "Bills AI Analyst" project.

The goal is to build an AI-assisted system that analyzes Buffalo Bills games and explains outcomes using structured data, validated queries, reasoning, and clear explanations.

The AI-assisted system will:
•	Answer questions like: Why did the Bills lose this game? What changed after halftime? Which three factors mattered most? Which drives and plays support that claim?
•	Return structured evidence rather than just prose: generated SQL, validation status, result rows, ranked reasons, supporting metrics, key drives, key plays, charts, and eventually retrieved recap snippets.
•	Allow drilldown from season to game to drive to play, so the user can inspect the evidence rather than trust a black-box answer.


---

## Core Principles

1. **Clarity over complexity**
   - Prefer simple, readable implementations
   - Avoid unnecessary abstractions or frameworks

2. **Explainability first**
   - Outputs should clearly explain *why* something happened
   - Prefer ranked reasons, structured outputs, validated SQL, returned data, and traceable logic

3. **Incremental development**
   - Make small, testable changes
   - Do not introduce large architectural changes without justification

4. **Production-minded, not overengineered**
   - Write code as if it could be productionized
   - But avoid premature optimization or infrastructure

---

## Technical Stack

- Language: Python 3.10+
- Framework: FastAPI
- Data handling: pandas (as needed)
- API-first design

Avoid introducing new technologies unless necessary.

---

## Project Structure Guidelines

- `app/` → application code (API, logic)
- `data/` → sample or local data (non-sensitive)
- `tests/` → unit or integration tests
- `docs/` → documentation and design notes

Keep structure flat and easy to understand.

Before implementing meaningful new code, agents should first review:

- `docs/roadmap.md` for project direction and sequencing
- `docs/data_schema.md` for the intended analytics dataset contract

Before editing files, agents should provide an overview of the changes and get the go ahead.

If code and docs diverge, agents should use judgment, verify the current codebase, and update documentation when appropriate.

The target question-answering architecture is data-extractor first:

1. The first LLM decides whether approved local data can help answer the question.
2. If data is useful, that LLM produces SQL against approved analytics views.
3. Application code validates the SQL before execution.
4. Application code executes valid read-only SQL with limits.
5. The answer LLM receives the question, extractor decision, SQL, validation status, and rows.
6. If no local data is needed or available, the answer LLM answers directly or states what context is missing.

---

## Coding Guidelines

- Use clear, descriptive function and variable names
- Prefer small functions over large classes
- Add comments only where logic is non-obvious
- Avoid deep inheritance or complex patterns
- Keep dependencies minimal

---

## API Design Expectations

- Use FastAPI for endpoints
- Endpoints should be:
  - simple
  - well-named
  - testable

Example direction:
- `/analyze-game`
- `/health`

Responses should:
- be structured (JSON)
- include reasoning, not just results
- expose data used, validation status, and limits when local data contributes to the answer

---

## AI / Analysis Expectations

When implementing analysis logic:

- Prefer **structured reasoning** over black-box outputs
- Prefer data extraction from approved analytics views before free-form answering
- Validate all LLM-generated SQL before execution
- Keep raw data files out of runtime query surfaces
- Make generated SQL, validation status, and returned rows inspectable
- Break explanations into:
  - ranked factors
  - supporting evidence
- Avoid vague summaries
- Show intermediate data and logic when possible
- If available data does not answer the question, state what context is missing instead of forcing an answer

---

## What to Avoid

- Do not introduce Docker unless explicitly requested
- Do not introduce cloud infrastructure (AWS, GCP, etc.) yet
- Do not refactor large parts of the repo without clear benefit
- Do not add heavy frameworks or unnecessary dependencies
- Do not overcomplicate file structure

---

## Preferred Contributions from Agents

Agents should prioritize:

- Improving clarity of code and structure
- Adding small, meaningful features
- Strengthening the data extractor, SQL validation, and data-grounded answer workflow
- Enhancing documentation (especially README)
- Suggesting logical next steps
- Keeping changes scoped and understandable

---

## Example Good Tasks

- Add a simple FastAPI endpoint for game analysis
- Add a guarded SQL-backed question flow
- Improve extractor prompts or schema guidance
- Improve README with clear project explanation
- Refactor a function for readability
- Add input/output schema for an endpoint
- Suggest next incremental feature

---

## Example Bad Tasks

- Introduce full microservices architecture
- Add Docker + Kubernetes setup
- Replace simple logic with complex frameworks
- Rewrite the entire project structure unnecessarily

---

## Final Notes

This project is intentionally evolving.

Agents should:
- act as a thoughtful collaborator
- prioritize learning and clarity
- avoid unnecessary complexity
