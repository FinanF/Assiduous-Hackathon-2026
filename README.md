# Assiduous-Hackathon-2026
This is my submistion for the 2026 Assiduous Hackathon, it is an Earning per Share (EPS) predictor.


## Deployment

To deploy this project run

```bash
  docker-compose up --build
```


## API Reference

#### Add data to database

```http
  POST /sync-data
```

#### Get quarterly predictions

```http
  GET /forecast/${quarters}
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `quarters`      | `int` | **Required**. returns quarterly predictions |


