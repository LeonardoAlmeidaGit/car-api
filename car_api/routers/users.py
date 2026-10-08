from fastapi import APIRouter, status


router = APIRouter()

@router.get('/', status_code=status.HTTP_200_OK)
async def list_users():
    return {
        'users': [
            {
                'id': 1,
                'e-mail': 'teste1@gmail.com',
            },
            {
                'id': 2,
                'e-mail': 'teste2@hotmail.com',
            },
            {
                'id': 3,
                'e-mail': 'teste3@outlook.com',
            }
        ]
    }
