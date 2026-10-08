from fastapi import APIRouter, status

from car_api.schemas.users import UserListPublicSchema

router = APIRouter()

@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=UserListPublicSchema,
)
async def list_users():
    return {
        'users': [
            {
                'id': 1,
                'username': 'teste1',
                'email': 'teste1@gmail.com',
            },
            {
                'id': 2,
                'username': 'test2',
                'email': 'teste2@hotmail.com',
            },
            {
                'id': 3,
                'username': 'teste3',
                'email': 'teste3@outlook.com',
            }
        ]
    }
