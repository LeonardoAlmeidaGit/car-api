from fastapi import FastAPI, status


app = FastAPI()

@app.get('/health_check', status_code=status.HTTP_200_OK)
def health_check():
    return {'message': 'ok'}
