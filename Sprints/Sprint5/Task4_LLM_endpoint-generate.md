# S5-04 — LLM Question Generation Endpoint

Se implementează endpoint-ul:

`POST /api/generate`

care primește de la backend conținutul complet al unei lecții și numărul de întrebări care trebuie generate.

Request-ul primit de la backend:
```json
{ 
"content": "insert_a_very_descriptive_lesson_here",  
"count": 5,
}
```
Content reprezintă întreg conținutul lecției, iar count reprezintă câte întrebări trebuie generate. Dacă count lipsește, valoarea default va fi 5.

Endpoint-ul trebuie protejat la fel ca celelalte endpoint-uri, folosind header-ul:

`X-Api-Key: {api_key}` 

sau, dacă backend-ul îl scrie exact așa:

`X-API-KEY: {api_key}`

În Django, header-ul poate fi citit tot prin:
`request.headers.get("X-Api-Key")`
deoarece header-ele HTTP sunt case-insensitive.

Response-ul pe care AI-ul trebuie să îl trimită
```json 
{
  "questions": [
    {
      "text": "Care este forma generală a ecuației de gradul al doilea?",
      "type": "SINGLE_CHOICE",
      "answers": ["ax² + bx + c = 0", "ax + b = 0", "a/x + b = 0", "x + y = 0"],
      "correctAnswers": ["ax² + bx + c = 0"],
      "difficulty": 0.4
    }
  ]
}
```
Fiecare întrebare trebuie să aibă:
```
text
type
answer
scorrectAnswers
difficulty
```
Tipurile acceptate:
`SINGLE_CHOICE MULTIPLE_CHOICE`

`difficulty` trebuie să fie între:
`0.0 și 1.0`

Flow-ul conceptual

```
Backend trimite content + count
        ↓
AI validează API key
        ↓
AI validează request body
        ↓
AI construiește prompt pentru LLM
        ↓
AI apelează LLM-ul
        ↓
AI primește răspuns text/JSON
        ↓
AI parsează JSON-ul
        ↓
AI validează structura întrebărilor
        ↓
AI returnează { "questions": [...] } 
```

# Cum am putea apela un astfel de LLM
Aveți două variante principale.

## Varianta 1 — API extern, de exemplu OpenAI API

În production, cea mai simplă variantă este să apelați un API extern de LLM.
Conceptual, aveți un service:
`LLMQuestionGenerationService`
care primește:
```
content 
count 
```
și trimite către LLM un prompt de forma:

```
You are an educational question generation assistant.

Generate exactly {count} questions based only on the lesson content below.

Return only valid JSON in this exact format:
{
  "questions": [
    {
      "text": "...",
      "type": "SINGLE_CHOICE" or "MULTIPLE_CHOICE",
      "answers": ["...", "...", "...", "..."],
      "correctAnswers": ["..."],
      "difficulty": 0.5
    }
  ]
}

Rules:
- Generate exactly {count} questions.
- Each question must have 4 answer options.
- correctAnswers must contain only values from answers.
- difficulty must be between 0.0 and 1.0.
- Do not return markdown.
- Do not return explanations.
- Use only the lesson content.

Lesson content:
{content} 
```

Apoi service-ul parsează răspunsul primit de la LLM ca JSON și îl validează.

# Varianta 2 — model local / self-hosted

Dacă nu vreți API extern, puteți folosi un model local sau self-hosted, de exemplu prin:
```
Ollama
LM Studio
vLLM
Hugging Face endpoint 
```
Flow-ul rămâne același:

`Django service → HTTP request către LLM local → primește JSON → validează → returnează backendului`

Diferența este doar URL-ul și modul de autentificare.
Exemplu conceptual cu Ollama:
```
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
    },
    timeout=60,
) 
```
# Structură recomandată pentru cod
```
tutoring/
├── services/
│   ├── llm_question_generation_service.py
│   └── question_generation_prompt_service.py
├── serializers.py
├── views.py
└── urls.py 
```

# Responsabilități

`QuestionGenerationPromptService` construiește promptul.
`LLMQuestionGenerationService` apelează LLM-ul și parsează răspunsul.
`GenerateQuestionsView` validează request-ul și returnează răspunsul.
`Serializer-ul` validează request-ul și response-ul.

# Ce NU face acest task
Task 4 nu trebuie să:
folosească `QuestionRecommendationEnginesalveze` întrebările generate în DB automatactualizeze StudentInteractionactualizeze StudentTopicLevelproceseze feedbackantreneze model ML
Acest task este strict pentru:
generare întrebări din lecție folosind LLM

# Definition of Done
Task-ul este gata când:
```
- endpoint-ul POST /api/generate există
- endpoint-ul este protejat cu X-Api-Key / X-API-KEY
- request-ul acceptă content și count
- count are default 5
- AI-ul construiește prompt pentru LLM
- AI-ul apelează un LLM printr-un service separat
- răspunsul LLM este parsat ca JSON
- răspunsul este validat după structura stabilită
- endpoint-ul returnează { "questions": [...] }
- există fallback/error handling dacă LLM-ul nu răspunde sau răspunde invalid 
```

Pe scurt: backend-ul trimite lecția, iar AI-ul folosește LLM-ul ca să întoarcă întrebări în JSON-ul vostru standard.