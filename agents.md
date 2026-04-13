# Agents Instructions

## Project Overview
This repository contains the "Bills AI Analyst" project.

The goal is to build an AI-assisted system that analyzes Buffalo Bills games and explains outcomes (wins/losses) using structured data, reasoning, and clear, ranked explanations.

This project is intended to be:
- A learning platform for AI development (RAG, agents, backend systems)
- A portfolio-quality project demonstrating practical AI system design
- A clean, well-structured Python backend application

---

## Core Principles

1. **Clarity over complexity**
   - Prefer simple, readable implementations
   - Avoid unnecessary abstractions or frameworks

2. **Explainability first**
   - Outputs should clearly explain *why* something happened
   - Prefer ranked reasons, structured outputs, and traceable logic

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

---

## AI / Analysis Expectations

When implementing analysis logic:

- Prefer **structured reasoning** over black-box outputs
- Break explanations into:
  - ranked factors
  - supporting evidence
- Avoid vague summaries
- Show intermediate logic when possible

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
- Enhancing documentation (especially README)
- Suggesting logical next steps
- Keeping changes scoped and understandable

---

## Example Good Tasks

- Add a simple FastAPI endpoint for game analysis
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