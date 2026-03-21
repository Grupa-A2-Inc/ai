# AI Endpoint

Asta implică 4 lucruri:

backend-ul trebuie să știe ce trimite;
AI-ul trebuie să știe ce validează;
AI-ul trebuie să știe ce serviciu intern apelează;
backend-ul trebuie să primească un răspuns standardizat.

1. definești contractul request/response
2. validezi datele de intrare
3. creezi view-ul
4. conectezi view-ul cu engine-ul
5. gestionezi erorile
6. expui ruta în urls.py
7. testezi endpoint-ul

## 1. Definisesti contractul request/response (minim pe sprint 1)

Request
```json 
{
  "user_id": 12,
  "subject_id": 3,
  "topic_id": 8
}
```

Response 
```json 
{
  "question_id": 41,
  "difficulty": 0.5,
  "source": "selection"
}
```

Response de eroare 
```json
{
  "error": "No question could be recommended for the given topic."
}
```

Prima: chiar dacă în Sprint 1 poate nu folosești subject_id foarte mult în logică, e bine să-l primești din start dacă apare în fluxul vostru arhitectural, ca să nu schimbi API-ul mai târziu. Documentul tău spune explicit că backend-ul trimite user_id, subject_id, topic_id.

A doua: răspunsul trebuie să fie simplu, dar suficient de clar pentru backend. Nu trimite obiecte prea mari, nu trimite logică internă, nu expune detalii de implementare.

## 2. Alegi endpointul si metoda HTTP

```POST /recommend/``` <- REST Framework

In urls.py
```python 
from django.urls import path
from .views import RecommendQuestionView

urlpatterns = [
    path("recommend/", RecommendQuestionView.as_view(), name="recommend-question"),
]
```

## 3. Serlizer de input

```python
from rest_framework import serializers

class RecommendationRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    subject_id = serializers.IntegerField(min_value=1)
    topic_id = serializers.IntegerField(min_value=1)
```

Aici faci deja primul filtru de siguranță:
nu accepți string-uri;
nu accepți null;
nu accepți ID-uri negative sau zero.

„accept numai request-uri corecte structural.” si resping altceva

## 4. Serializer de output

```python
class RecommendationResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    difficulty = serializers.FloatField()
    source = serializers.CharField()
```

## 5. View-ul

Pentru sprint 1 vom crea un APIView.

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RecommendationRequestSerializer
from .services.question_recommendation_engine import QuestionRecommendationEngine


class RecommendQuestionView(APIView):
    def post(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        user_id = validated_data["user_id"]
        subject_id = validated_data["subject_id"]
        topic_id = validated_data["topic_id"]

        engine = QuestionRecommendationEngine()
        result = engine.recommend(
            user_id=user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        if result is None:
            return Response(
                {"error": "No question could be recommended for the given topic."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "question_id": result.question_id,
                "difficulty": result.difficulty,
                "source": result.source,
            },
            status=status.HTTP_200_OK,
        ) 
```

View-ul trebuie să facă doar 4 lucruri:

primește request-ul;
validează request-ul;
apelează engine-ul;
returnează răspunsul.

Pentru inceput engine-ul va fi doar o functie ```engine = QuestionRecommendationEngine()```
De asemenea semnatura lui recommend va fi ```def recommend(self, user_id: int, subject_id: int, topic_id: int):``` 
Pentru sprinturile viitoare daca vreau mai multe date merge un DTO 

## 6. Error Handling

A. Request Invalid -> serlizer trebuie sa dea automat 400 Bad Request
Ex : topic_id nu exista -> ```{"topic_id": ["This field is required."]}```

B. Request valid dar nu se poate recomanda nicio intrebare -> 404 Not Found

C. Eroare interna -> 500 Internal Server Error (Django se ocupa de asta, dar e bine sa te asiguri ca nu scapi exceptii necontrolate)

## 7. Pregatire pentru Sprint 1

Trebuie un mock engine -> Dto rezultat -> raspuns coerent (daca celelalte taskuri nu sunt gata, poti hardcoda un raspuns in engine pentru a testa endpoint-ul)
```python
return Response(
    {
        "question_id": 1,
        "difficulty": 0.5,
        "source": "mock"
    }
) 
```
## 8. Testare Task 1

Test - request valid  
```json 
{
  "user_id": 12,
  "subject_id": 3,
  "topic_id": 8
}
```

Ma astept la status 200 si raspuns valid

Teste invalide de testat... 



