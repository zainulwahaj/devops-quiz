# DevOps Quiz 3 - Selenium News Summary API

Registration: `FA23-BAI-058`

Assigned source: `The Atlantic`

This project builds a Dockerized FastAPI service that uses Selenium with Chrome/ChromeDriver to search The Atlantic, open the first article result for a keyword, summarize the article locally, and expose the required API on port `7000`.

## API

```http
GET /get?keyword=technology
```

Response shape:

```json
{
  "registration": "FA23-BAI-058",
  "newssource": "The Atlantic",
  "keyword": "technology",
  "url": "https://www.theatlantic.com/...",
  "summary": "..."
}
```

The root page also shows the registration number:

```http
GET /
```

## Build

```bash
docker build -t devops-quiz:fa23-bai-058 .
```

## Run

```bash
docker run --rm -p 7000:7000 devops-quiz:fa23-bai-058
```

## Test API

```bash
curl http://localhost:7000/
curl "http://localhost:7000/get?keyword=technology"
```

## Docker Hub Tagging

Replace `your-dockerhub-username` with your Docker Hub username:

```bash
docker tag devops-quiz:fa23-bai-058 your-dockerhub-username/devops-quiz:fa23-bai-058
docker push your-dockerhub-username/devops-quiz:fa23-bai-058
```

## Local Tests

```bash
python3 -m pytest
```
